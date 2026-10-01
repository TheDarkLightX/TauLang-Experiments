#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
fail=0
for mode in ordinary evaluator memory; do
  (
    unset TAU_LLM_API_KEY OPENAI_API_KEY TAU_CONCRETE_EVAL_MAX_EXPRESSIONS
    export TAU_MEMORY_TELEMETRY=0
    export TAU_CONCRETE_EVAL=0
    setting=0
    if [[ "$mode" != ordinary ]]; then export TAU_CONCRETE_EVAL=1; fi
    if [[ "$mode" == memory ]]; then setting=1; fi
    for name in DECIMAL_ONLY TRANSIENT_NORMALIZE TRIM ARENA_OUTPUTS FLAT_LEAVES RELEASE_PARSE_SCRATCH; do
      export "TAU_EVAL_${name}=${setting}"
    done
    ctest --test-dir tau-source/build/release -j "${TAU_TEST_JOBS:-8}" --output-on-failure
  ) > "suite-${mode}.log" 2>&1 || fail=1
  tail -n 30 "suite-${mode}.log"
done
exit "$fail"
