#!/usr/bin/env python3
"""Measure active RR rule filtering on the batched table checks.

Both modes keep the previous two internal candidates enabled:

    TAU_RR_SKIP_VALUE_INFER=1
    TAU_RR_TRANSFORM_DEFS_CACHE=1

The only difference is:

    baseline: TAU_RR_ACTIVE_RULES unset
    active:   TAU_RR_ACTIVE_RULES=1

This is an internal-path experiment. It is useful only if output parity holds
and the active pass skips enough rule attempts to beat its own scan overhead.
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
def active_rules_mode(enabled: bool):
    old_skip = os.environ.get("TAU_RR_SKIP_VALUE_INFER")
    old_cache = os.environ.get("TAU_RR_TRANSFORM_DEFS_CACHE")
    old_active = os.environ.get("TAU_RR_ACTIVE_RULES")
    os.environ["TAU_RR_SKIP_VALUE_INFER"] = "1"
    os.environ["TAU_RR_TRANSFORM_DEFS_CACHE"] = "1"
    if enabled:
        os.environ["TAU_RR_ACTIVE_RULES"] = "1"
    else:
        os.environ.pop("TAU_RR_ACTIVE_RULES", None)
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
        if old_active is None:
            os.environ.pop("TAU_RR_ACTIVE_RULES", None)
        else:
            os.environ["TAU_RR_ACTIVE_RULES"] = old_active


def run_mode(tau_bin: Path, program: str, reps: int, active: bool) -> list[dict[str, object]]:
    with active_rules_mode(active):
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
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-active-rules-batched.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    expected = len(table_checks())
    program = batched_program(Path.cwd())
    baseline_runs = run_mode(args.tau_bin, program, args.reps, active=False)
    active_runs = run_mode(args.tau_bin, program, args.reps, active=True)
    baseline = summarize_mode(baseline_runs)
    active = summarize_mode(active_runs)
    ok = check_runs(baseline_runs, expected) and check_runs(active_runs, expected)
    summary = {
        "scope": (
            "batched table checks with value-inference skip and transformed-"
            "definition cache enabled"
        ),
        "ok": ok,
        "check_count": expected,
        "reps": args.reps,
        "baseline": baseline,
        "active": active,
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_sum_ms"]), float(active["elapsed_sum_ms"])
        ),
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]), float(active["solve_total_ms"])
        ),
        "rr_apply_formula_improvement_percent": pct_delta(
            float(baseline["rr_apply_formula_ms"]), float(active["rr_apply_formula_ms"])
        ),
        "rr_formula_rewrite_improvement_percent": pct_delta(
            float(baseline["rr_formula_rewrite_ms"]), float(active["rr_formula_rewrite_ms"])
        ),
        "active_rules_skipped": max(
            0.0,
            float(active["rr_active_rules_before"]) - float(active["rr_active_rules_after"]),
        ),
        "boundary": (
            "This is an experimental dynamic rule-filter pass. A positive "
            "result here is not enough for default enablement without a "
            "larger corpus and a semantic proof."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "checks": expected,
        "reps": args.reps,
        "baseline_elapsed_ms": baseline["elapsed_sum_ms"],
        "active_elapsed_ms": active["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "active_solve_total_ms": active["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_rr_rewrite_ms": baseline["rr_formula_rewrite_ms"],
        "active_rr_rewrite_ms": active["rr_formula_rewrite_ms"],
        "rr_formula_rewrite_improvement_percent": summary["rr_formula_rewrite_improvement_percent"],
        "active_rules_rows": active["rr_active_rules_rows"],
        "active_rules_before": active["rr_active_rules_before"],
        "active_rules_after": active["rr_active_rules_after"],
        "active_rules_skipped": summary["active_rules_skipped"],
        "active_audit_rows": active["rr_active_rules_audit_rows"],
        "active_audit_equal_rows": active["rr_active_rules_audit_equal_rows"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
