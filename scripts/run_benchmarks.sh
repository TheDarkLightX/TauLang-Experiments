#!/usr/bin/env bash
set -euo pipefail

TAU_DIR="${TAU_DIR:-external/tau-lang}"
RESULT_DIR="${RESULT_DIR:-results/local}"

if [[ ! -d "$TAU_DIR" ]]; then
  echo "Missing Tau checkout at $TAU_DIR" >&2
  echo "Run ./scripts/setup_tau.sh first." >&2
  exit 1
fi

mkdir -p "$RESULT_DIR"

cat > "$RESULT_DIR/README.txt" <<'MSG'
Local benchmark outputs go here.
Do not commit large raw logs or machine-specific paths.
MSG

if [[ -x "$TAU_DIR/build-Release/tau" ]]; then
  TAU_BIN="$TAU_DIR/build-Release/tau"
elif [[ -x "$TAU_DIR/build/tau" ]]; then
  TAU_BIN="$TAU_DIR/build/tau"
else
  echo "Tau binary not found. Build Tau in $TAU_DIR, then rerun." >&2
  exit 1
fi

echo "Using Tau binary: $TAU_BIN"
echo "No benchmarks are registered yet. Add benchmark scripts under examples/ or scripts/."
