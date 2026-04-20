#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAU_DIR="${TAU_DIR:-"$ROOT/external/tau-lang"}"
BUILD_DIR="${TAU_BUILD_DIR:-"$TAU_DIR/build-Release"}"
JOBS="${JOBS:-2}"
ACCEPT_FLAG=""

if [[ "${1:-}" == "--accept-tau-license" ]]; then
  ACCEPT_FLAG="--accept-tau-license"
  shift
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--accept-tau-license]" >&2
  exit 2
fi

if [[ "${TAU_QNS_DEMO_SKIP_SETUP_PATCH:-0}" != "1" ]]; then
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

python3 "$ROOT/scripts/run_qns_semantic_ba_demo.py" \
  --tau-bin "$TAU_BIN" \
  --out "$RESULT_DIR/qns-semantic-ba-demo.json"
