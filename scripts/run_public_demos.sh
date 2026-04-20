#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACCEPT_FLAG=""

if [[ "${1:-}" == "--accept-tau-license" ]]; then
  ACCEPT_FLAG="--accept-tau-license"
  shift
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--accept-tau-license]" >&2
  exit 2
fi

echo "== Safe table demo =="
"$ROOT/scripts/run_table_demos.sh" $ACCEPT_FLAG

echo
echo "== Qelim-backed policy-shape demo =="
TAU_QELIM_DEMO_SKIP_SETUP_PATCH=1 \
  "$ROOT/scripts/run_qelim_table_demos.sh" \
  --reps "${QELIM_TABLE_DEMO_REPS:-5}"

echo
echo "== qNS semantic Boolean-algebra demo =="
TAU_QNS_DEMO_SKIP_SETUP_PATCH=1 \
  "$ROOT/scripts/run_qns_semantic_ba_demo.sh"

echo
echo "== EML/qNS certificate demo =="
TAU_EML_QNS_DEMO_SKIP_SETUP_PATCH=1 \
  "$ROOT/scripts/run_eml_qns_demo.sh"

echo
echo "== EML/qNS table-memory demo =="
TAU_EML_QNS_LLM_DEMO_SKIP_SETUP_PATCH=1 \
  "$ROOT/scripts/run_eml_qns_llm_memory_demo.sh"

if [[ "${RUN_PUBLIC_BENCHMARKS:-0}" == "1" ]]; then
  echo
  echo "== Optional research benchmark suite =="
  "$ROOT/scripts/run_benchmarks.sh"
fi

echo
echo "Public demo suite passed."
RESULT_LABEL="${RESULT_DIR:-results/local}"
if [[ "$RESULT_LABEL" == "$ROOT/"* ]]; then
  RESULT_LABEL="${RESULT_LABEL#"$ROOT/"}"
fi
echo "Results are under $RESULT_LABEL."
