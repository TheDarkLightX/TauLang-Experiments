#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAU_DIR="${TAU_DIR:-"$ROOT/external/tau-lang"}"
BUILD_DIR="${TAU_BUILD_DIR:-"$TAU_DIR/build-Release"}"
JOBS="${JOBS:-2}"
ACCEPT_FLAG=""
MODEL="${QNS_LOCAL_MODEL:-llama3.2:3b}"
NUM_GPU="${QNS_OLLAMA_NUM_GPU:-0}"
SKIP_SETUP_PATCH="${TAU_EML_QNS_LLM_DEMO_SKIP_SETUP_PATCH:-0}"
LLM_OUTPUT=""
LIVE_OLLAMA="0"
REPORT_OUT=""
VERIFY_RECEIPT="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --accept-tau-license)
      ACCEPT_FLAG="--accept-tau-license"
      shift
      ;;
    --model)
      MODEL="${2:?missing model name}"
      shift 2
      ;;
    --num-gpu)
      NUM_GPU="${2:?missing num-gpu value}"
      shift 2
      ;;
    --proposal-json)
      LLM_OUTPUT="${2:?missing proposal JSON path}"
      shift 2
      ;;
    --report-out)
      REPORT_OUT="${2:?missing report output path}"
      shift 2
      ;;
    --live-ollama)
      LIVE_OLLAMA="1"
      shift
      ;;
    --skip-setup-patch)
      SKIP_SETUP_PATCH="1"
      shift
      ;;
    --skip-verify)
      VERIFY_RECEIPT="0"
      shift
      ;;
    *)
      echo "Usage: $0 [--accept-tau-license] [--skip-setup-patch] [--skip-verify] [--live-ollama] [--model NAME] [--num-gpu N] [--proposal-json FILE] [--report-out FILE]" >&2
      exit 2
      ;;
  esac
done

if [[ "$SKIP_SETUP_PATCH" != "1" ]]; then
  "$ROOT/scripts/setup_tau.sh" $ACCEPT_FLAG
  "$ROOT/scripts/apply_patches.sh"
else
  echo "Skipping Tau setup and patch application; using existing checkout."
fi

if [[ ! -x "$BUILD_DIR/tau" ]]; then
  cmake -S "$TAU_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
fi
cmake --build "$BUILD_DIR" --target tau -j "$JOBS"

TAU_BIN="${TAU_BIN:-"$BUILD_DIR/tau"}"
RESULT_DIR="${RESULT_DIR:-"$ROOT/results/local"}"
mkdir -p "$RESULT_DIR"
REPORT_OUT="${REPORT_OUT:-"$RESULT_DIR/eml-qns-llm-memory-demo.md"}"

CMD=(python3 "$ROOT/scripts/run_eml_qns_llm_memory_demo.py"
  --tau-bin "$TAU_BIN"
  --model "$MODEL"
  --num-gpu "$NUM_GPU"
  --out "$RESULT_DIR/eml-qns-llm-memory-demo.json"
  --report-out "$REPORT_OUT")

if [[ -n "$LLM_OUTPUT" ]]; then
  CMD+=(--llm-output "$LLM_OUTPUT")
fi

if [[ "$LIVE_OLLAMA" == "1" ]]; then
  CMD+=(--live-ollama)
fi

"${CMD[@]}"

if [[ "$VERIFY_RECEIPT" == "1" ]]; then
  python3 "$ROOT/scripts/verify_eml_qns_memory_receipt.py" \
    --receipt "$RESULT_DIR/eml-qns-llm-memory-demo.json" \
    --self-test
fi
