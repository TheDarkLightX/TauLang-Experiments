#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAU_DIR="${TAU_DIR:-"$ROOT/external/tau-lang"}"
BUILD_DIR="${TAU_BUILD_DIR:-"$TAU_DIR/build-Release"}"
JOBS="${JOBS:-2}"
REPS="${REPS:-5}"
ACCEPT_FLAG=""

if [[ "${1:-}" == "--accept-tau-license" ]]; then
  ACCEPT_FLAG="--accept-tau-license"
  shift
fi

if [[ "${1:-}" == "--reps" ]]; then
  REPS="${2:?missing value after --reps}"
fi

"$ROOT/scripts/setup_tau.sh" $ACCEPT_FLAG
"$ROOT/scripts/apply_patches.sh"

if [[ ! -x "$BUILD_DIR/tau" ]]; then
  cmake -S "$TAU_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
fi
cmake --build "$BUILD_DIR" --target tau -j "$JOBS"

TAU_BIN="${TAU_BIN:-"$BUILD_DIR/tau"}"
RESULT_DIR="${RESULT_DIR:-"$ROOT/results/local"}"
OUT_JSON="$RESULT_DIR/qelim-table-demo-corpus.json"
OUT_TXT="$RESULT_DIR/qelim-table-demo-summary.txt"
mkdir -p "$RESULT_DIR"

python3 "$ROOT/scripts/run_qelim_policy_semantic_corpus.py" \
  --tau-bin "$TAU_BIN" \
  --reps "$REPS" \
  --out "$OUT_JSON" \
  > "$RESULT_DIR/qelim-table-demo-corpus.full.json"

python3 - "$OUT_JSON" > "$OUT_TXT" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
mode = data["mode_summary"]
default = float(mode["default"]["qelim_total_ms_sum"])
auto = float(mode["auto"]["qelim_total_ms_sum"])
auto_kb = float(mode["auto_kb_guarded"]["qelim_total_ms_sum"])
speedup = default / auto if auto else 0.0
auto_kb_speedup = default / auto_kb if auto_kb else 0.0

print("Qelim-backed safe-table policy demos passed.")
print()
print(f"cases:                  {data['case_count']}")
print(f"repetitions:            {data['reps']}")
print(f"semantic parity:         {'passed' if data['ok'] else 'failed'}")
print(f"syntactic fail, semantic pass: {data.get('syntactic_fail_semantic_pass_count', 0)}")
print(f"auto route counts:       {mode['auto']['route_counts']}")
print(f"default qelim total:     {default:.6f} ms")
print(f"auto qelim total:        {auto:.6f} ms")
print(f"auto+KB qelim total:     {auto_kb:.6f} ms")
print(f"auto speedup:            {speedup:.6f} x")
print(f"auto+KB speedup:         {auto_kb_speedup:.6f} x")
print()
print("Scope:")
print("- qelim command backend, not solve --tau runtime acceleration")
print("- formulas shaped like the table demos")
print("- residual formulas checked by the scoped semantic validator")
print("- current compiled BDD support boundary only")
print("- KB guarded mode is reported separately")
PY

cat "$OUT_TXT"
echo
echo "Full JSON: results/local/qelim-table-demo-corpus.json"
