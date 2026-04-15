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

python3 scripts/run_incremental_execution_demo.py \
  --out "$RESULT_DIR/incremental-execution-demo.json" \
  > "$RESULT_DIR/incremental-execution-demo.txt"

echo "Incremental execution demo written to $RESULT_DIR/incremental-execution-demo.json"

python3 scripts/run_tau_derivative_equivalence_demo.py \
  --out "$RESULT_DIR/tau-derivative-equivalence-demo.json" \
  > "$RESULT_DIR/tau-derivative-equivalence-demo.txt"

echo "Tau derivative/equivalence demo written to $RESULT_DIR/tau-derivative-equivalence-demo.json"

python3 scripts/run_bitvector_modular_demo.py \
  --max-width 6 \
  --out "$RESULT_DIR/bitvector-modular-demo.json" \
  > "$RESULT_DIR/bitvector-modular-demo.txt"

echo "Bitvector modular arithmetic demo written to $RESULT_DIR/bitvector-modular-demo.json"

python3 scripts/run_bitvector_constant_folding_demo.py \
  --width "${TAU_BV_FOLD_WIDTH:-4}" \
  --count "${TAU_BV_FOLD_COUNT:-80}" \
  --out "$RESULT_DIR/bitvector-constant-folding-demo.json" \
  > "$RESULT_DIR/bitvector-constant-folding-demo.txt"

echo "Bitvector constant-folding demo written to $RESULT_DIR/bitvector-constant-folding-demo.json"

python3 scripts/run_var_name_cache_key_demo.py \
  --out "$RESULT_DIR/var-name-cache-key-demo.json" \
  > "$RESULT_DIR/var-name-cache-key-demo.txt"

echo "Var-name cache-key demo written to $RESULT_DIR/var-name-cache-key-demo.json"

python3 scripts/run_equality_path_simplification_demo.py \
  --out "$RESULT_DIR/equality-path-simplification-demo.json" \
  > "$RESULT_DIR/equality-path-simplification-demo.txt"

echo "Equality-aware path simplification demo written to $RESULT_DIR/equality-path-simplification-demo.json"

if [[ -n "$TAU_BIN" ]]; then
  python3 scripts/run_qelim_kb_probe.py \
    --tau-bin "$TAU_BIN" \
    --out "$RESULT_DIR/qelim-kb-probe.json" \
    > "$RESULT_DIR/qelim-kb-probe.txt"
  echo "Qelim KB probe written to $RESULT_DIR/qelim-kb-probe.json"

  python3 scripts/run_equality_split_tau_probe.py \
    --tau-bin "$TAU_BIN" \
    --out "$RESULT_DIR/equality-split-tau-probe.json" \
    > "$RESULT_DIR/equality-split-tau-probe.txt"
  echo "Equality-split Tau recombination probe written to $RESULT_DIR/equality-split-tau-probe.json"

  python3 scripts/run_tau_runtime_stats_demo.py \
    --tau-bin "$TAU_BIN" \
    --out "$RESULT_DIR/tau-runtime-stats-demo.json" \
    > "$RESULT_DIR/tau-runtime-stats-demo.txt"
  echo "Tau runtime stats demo written to $RESULT_DIR/tau-runtime-stats-demo.json"

  if [[ "${RUN_TAU_IO_REBUILD_REGRESSION:-0}" == "1" ]]; then
    python3 scripts/run_tau_io_rebuild_regression.py \
      --tau-root "$TAU_DIR" \
      --build-dir "$TAU_DIR/build-Release" \
      --out "$RESULT_DIR/tau-io-rebuild-regression.json" \
      > "$RESULT_DIR/tau-io-rebuild-regression.txt"
    echo "Tau IO rebuild regression written to $RESULT_DIR/tau-io-rebuild-regression.json"
  fi

  if [[ "${RUN_QELIM_KB_MATRIX:-0}" == "1" ]]; then
    python3 scripts/run_qelim_kb_matrix.py \
      --tau-bin "$TAU_BIN" \
      --out "$RESULT_DIR/qelim-kb-matrix.json" \
      --max-cases "${QELIM_KB_MATRIX_CASES:-18}" \
      --reps "${QELIM_KB_MATRIX_REPS:-3}" \
      > "$RESULT_DIR/qelim-kb-matrix.txt"
    echo "Qelim KB matrix written to $RESULT_DIR/qelim-kb-matrix.json"
  fi

  if [[ "${RUN_QELIM_AUTO_KB_MATRIX:-0}" == "1" ]]; then
    python3 scripts/run_qelim_auto_kb_matrix.py \
      --tau-bin "$TAU_BIN" \
      --out "$RESULT_DIR/qelim-auto-kb-matrix.json" \
      --max-cases "${QELIM_AUTO_KB_MATRIX_CASES:-18}" \
      --reps "${QELIM_AUTO_KB_MATRIX_REPS:-3}" \
      > "$RESULT_DIR/qelim-auto-kb-matrix.txt"
    echo "Qelim auto+KB matrix written to $RESULT_DIR/qelim-auto-kb-matrix.json"
  fi

  if [[ "${RUN_TABLE_COMPOUND_CHECK:-0}" == "1" ]]; then
    python3 scripts/run_table_demo_compound_check.py \
      --tau-bin "$TAU_BIN" \
      --reps "${TABLE_COMPOUND_REPS:-1}" \
      --out "$RESULT_DIR/table-demo-compound-check.json" \
      > "$RESULT_DIR/table-demo-compound-check.txt"
    echo "Table compound check written to $RESULT_DIR/table-demo-compound-check.json"
  fi
fi
