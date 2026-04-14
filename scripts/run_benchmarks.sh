#!/usr/bin/env bash
set -euo pipefail

TAU_DIR="${TAU_DIR:-external/tau-lang}"
RESULT_DIR="${RESULT_DIR:-results/local}"

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
  TAU_BIN=""
fi

if [[ -n "$TAU_BIN" ]]; then
  echo "Using Tau binary: $TAU_BIN"
else
  echo "Tau binary not found. Running standalone benchmarks only."
fi

python3 scripts/tau_kb_normalizer.py benchmark \
  --count "${TAU_KB_BENCH_COUNT:-250}" \
  --depth "${TAU_KB_BENCH_DEPTH:-5}" \
  --seed "${TAU_KB_BENCH_SEED:-20260413}" \
  --out "$RESULT_DIR/kb-normalizer-benchmark.json" \
  > "$RESULT_DIR/kb-normalizer-benchmark.txt"

echo "KB normalizer benchmark written to $RESULT_DIR/kb-normalizer-benchmark.json"
