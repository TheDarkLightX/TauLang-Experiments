#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OLLAMA_BIN="${OLLAMA_BIN:-}"
PROFILE="installed"
MODEL=""
PULL="0"
RUN_SMOKE="0"
SKIP_TAU_SETUP="1"

usage() {
  cat >&2 <<'USAGE'
Usage:
  ./scripts/setup_local_llm_proposer.sh [options]

Options:
  --profile NAME       installed | tiny | compact | smol | bonsai
  --model NAME         explicit Ollama model name
  --pull               pull the selected model with Ollama
  --run-smoke          run the EML/qNS memory smoke demo after setup
  --no-skip-tau-setup  allow the smoke demo to run Tau setup and patching

Profiles:
  installed  llama3.2:3b     Uses the model already found in this workspace
  tiny       gemma3:270m      Very small public Ollama model
  compact    qwen3:0.6b       Small public Ollama model
  smol       smollm2:1.7b     Larger small-model fallback
  bonsai     bonsai-8b        Preferred if already registered locally

The script never downloads a model unless --pull is supplied.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:?missing profile}"
      shift 2
      ;;
    --model)
      MODEL="${2:?missing model}"
      shift 2
      ;;
    --pull)
      PULL="1"
      shift
      ;;
    --run-smoke)
      RUN_SMOKE="1"
      shift
      ;;
    --no-skip-tau-setup)
      SKIP_TAU_SETUP="0"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$OLLAMA_BIN" ]]; then
  if command -v ollama >/dev/null 2>&1 && ollama --version >/dev/null 2>&1; then
    OLLAMA_BIN="$(command -v ollama)"
  elif [[ -x /snap/ollama/current/bin/ollama ]]; then
    OLLAMA_BIN="/snap/ollama/current/bin/ollama"
  elif [[ -x /snap/ollama/112/bin/ollama ]]; then
    OLLAMA_BIN="/snap/ollama/112/bin/ollama"
  else
    echo "Ollama was not found. Install Ollama or set OLLAMA_BIN." >&2
    exit 1
  fi
fi

if [[ -z "$MODEL" ]]; then
  case "$PROFILE" in
    installed)
      MODEL="llama3.2:3b"
      ;;
    tiny)
      MODEL="gemma3:270m"
      ;;
    compact)
      MODEL="qwen3:0.6b"
      ;;
    smol)
      MODEL="smollm2:1.7b"
      ;;
    bonsai)
      MODEL="bonsai-8b"
      ;;
    *)
      echo "unknown profile: $PROFILE" >&2
      usage
      exit 2
      ;;
  esac
fi

echo "Ollama binary: $OLLAMA_BIN"
echo "Selected model: $MODEL"

if [[ "$PULL" == "1" ]]; then
  echo "Pulling model with Ollama. This may require substantial disk space."
  "$OLLAMA_BIN" pull "$MODEL"
fi

echo
echo "Installed Ollama models:"
"$OLLAMA_BIN" list || true

if [[ "$RUN_SMOKE" == "1" ]]; then
  if [[ "$SKIP_TAU_SETUP" == "1" ]]; then
    "$ROOT/scripts/run_eml_qns_llm_memory_demo.sh" --skip-setup-patch --live-ollama --model "$MODEL"
  else
    "$ROOT/scripts/run_eml_qns_llm_memory_demo.sh" --live-ollama --model "$MODEL"
  fi
fi
