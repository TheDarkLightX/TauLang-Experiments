#!/usr/bin/env python3
"""Measure transformed-definition caching on the batched table checks.

This isolates the next RR optimization after `TAU_RR_SKIP_VALUE_INFER=1`.
Both modes keep the value-inference skip enabled. The only difference is:

    baseline: TAU_RR_TRANSFORM_DEFS_CACHE unset
    cache:    TAU_RR_TRANSFORM_DEFS_CACHE=1

The cache stores transformed recurrence-definition lists inside one Tau
process. It is expected to help only when several solve obligations share the
same stored definitions.
"""

from __future__ import annotations

import argparse
import json
import os
from contextlib import contextmanager
from pathlib import Path

from run_rr_skip_batched_table_checks import (
    batched_program,
    pct_delta,
    run_batched,
    summarize_mode,
    table_checks,
)


@contextmanager
def transform_cache_mode(enabled: bool):
    old_skip = os.environ.get("TAU_RR_SKIP_VALUE_INFER")
    old_cache = os.environ.get("TAU_RR_TRANSFORM_DEFS_CACHE")
    os.environ["TAU_RR_SKIP_VALUE_INFER"] = "1"
    if enabled:
        os.environ["TAU_RR_TRANSFORM_DEFS_CACHE"] = "1"
    else:
        os.environ.pop("TAU_RR_TRANSFORM_DEFS_CACHE", None)
    try:
        yield
    finally:
        if old_skip is None:
            os.environ.pop("TAU_RR_SKIP_VALUE_INFER", None)
        else:
            os.environ["TAU_RR_SKIP_VALUE_INFER"] = old_skip
        if old_cache is None:
            os.environ.pop("TAU_RR_TRANSFORM_DEFS_CACHE", None)
        else:
            os.environ["TAU_RR_TRANSFORM_DEFS_CACHE"] = old_cache


def run_mode(tau_bin: Path, program: str, reps: int, cache: bool) -> list[dict[str, object]]:
    with transform_cache_mode(cache):
        return [run_batched(tau_bin, program, skip=True) for _ in range(reps)]


def check_runs(runs: list[dict[str, object]], expected: int) -> bool:
    ok = True
    for run in runs:
        ok = ok and bool(run["ok"])
        ok = ok and run["solve_result_count"] == expected
        ok = ok and run["no_solution_count"] == expected
        ok = ok and run["solve_stat_count"] == expected
        ok = ok and run["rr_get_defs_stat_count"] == expected
        ok = ok and run["rr_with_defs_stat_count"] == expected
        ok = ok and run["rr_formula_stat_count"] == expected
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-transform-defs-cache-batched.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    expected = len(table_checks())
    program = batched_program(Path.cwd())
    no_cache_runs = run_mode(args.tau_bin, program, args.reps, cache=False)
    cache_runs = run_mode(args.tau_bin, program, args.reps, cache=True)
    no_cache = summarize_mode(no_cache_runs)
    cache = summarize_mode(cache_runs)
    ok = check_runs(no_cache_runs, expected) and check_runs(cache_runs, expected)
    summary = {
        "scope": "batched table checks with RR value-inference skip enabled",
        "ok": ok,
        "check_count": expected,
        "reps": args.reps,
        "no_cache": no_cache,
        "cache": cache,
        "elapsed_improvement_percent": pct_delta(
            float(no_cache["elapsed_sum_ms"]), float(cache["elapsed_sum_ms"])
        ),
        "solve_total_improvement_percent": pct_delta(
            float(no_cache["solve_total_ms"]), float(cache["solve_total_ms"])
        ),
        "rr_apply_formula_improvement_percent": pct_delta(
            float(no_cache["rr_apply_formula_ms"]), float(cache["rr_apply_formula_ms"])
        ),
        "rr_formula_transform_improvement_percent": pct_delta(
            float(no_cache["rr_formula_transform_ms"]), float(cache["rr_formula_transform_ms"])
        ),
        "boundary": (
            "This measures one-process batched table checks only. The cache is "
            "useful when several obligations share the same stored definitions. "
            "It is not evidence for one-shot Tau commands."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "checks": expected,
        "reps": args.reps,
        "no_cache_elapsed_ms": no_cache["elapsed_sum_ms"],
        "cache_elapsed_ms": cache["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "no_cache_solve_total_ms": no_cache["solve_total_ms"],
        "cache_solve_total_ms": cache["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "no_cache_rr_apply_formula_ms": no_cache["rr_apply_formula_ms"],
        "cache_rr_apply_formula_ms": cache["rr_apply_formula_ms"],
        "rr_apply_formula_improvement_percent": summary["rr_apply_formula_improvement_percent"],
        "no_cache_rr_formula_transform_ms": no_cache["rr_formula_transform_ms"],
        "cache_rr_formula_transform_ms": cache["rr_formula_transform_ms"],
        "rr_formula_transform_improvement_percent": summary["rr_formula_transform_improvement_percent"],
        "cache_hits": cache["rr_transform_defs_cache_hits"],
        "cache_rows": cache["rr_transform_defs_cache_rows"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
