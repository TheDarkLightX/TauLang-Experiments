#!/usr/bin/env python3
"""Measure reachable RR definition pruning on the batched table checks.

Both modes keep the existing recurrence-rewrite candidates enabled:

    TAU_RR_SKIP_VALUE_INFER=1
    TAU_RR_TRANSFORM_DEFS_CACHE=1
    TAU_RR_ACTIVE_RULES=1

The only measured difference is:

    baseline:  TAU_RR_REACHABLE_DEFS unset
    reachable: TAU_RR_REACHABLE_DEFS=1

This is an internal-path experiment. It is useful only if output parity holds
and the pruning pass removes enough unreachable definitions to beat its own
reachability scan overhead.
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
def reachable_defs_mode(
    enabled: bool,
    audit: bool,
    post_transform: bool,
    reachable_cache: bool,
):
    keys = [
        "TAU_RR_SKIP_VALUE_INFER",
        "TAU_RR_TRANSFORM_DEFS_CACHE",
        "TAU_RR_ACTIVE_RULES",
        "TAU_RR_REACHABLE_DEFS",
        "TAU_RR_REACHABLE_DEFS_POST_TRANSFORM",
        "TAU_RR_REACHABLE_DEFS_CACHE",
        "TAU_RR_REACHABLE_DEFS_AUDIT",
        "TAU_RR_ACTIVE_RULES_AUDIT",
    ]
    old_env = {key: os.environ.get(key) for key in keys}
    os.environ["TAU_RR_SKIP_VALUE_INFER"] = "1"
    os.environ["TAU_RR_TRANSFORM_DEFS_CACHE"] = "1"
    os.environ["TAU_RR_ACTIVE_RULES"] = "1"
    if enabled:
        os.environ["TAU_RR_REACHABLE_DEFS"] = "1"
        if post_transform:
            os.environ["TAU_RR_REACHABLE_DEFS_POST_TRANSFORM"] = "1"
        else:
            os.environ.pop("TAU_RR_REACHABLE_DEFS_POST_TRANSFORM", None)
        if reachable_cache:
            os.environ["TAU_RR_REACHABLE_DEFS_CACHE"] = "1"
        else:
            os.environ.pop("TAU_RR_REACHABLE_DEFS_CACHE", None)
    else:
        os.environ.pop("TAU_RR_REACHABLE_DEFS", None)
        os.environ.pop("TAU_RR_REACHABLE_DEFS_POST_TRANSFORM", None)
        os.environ.pop("TAU_RR_REACHABLE_DEFS_CACHE", None)
    if audit and enabled:
        os.environ["TAU_RR_REACHABLE_DEFS_AUDIT"] = "1"
        os.environ["TAU_RR_ACTIVE_RULES_AUDIT"] = "1"
    else:
        os.environ.pop("TAU_RR_REACHABLE_DEFS_AUDIT", None)
        os.environ.pop("TAU_RR_ACTIVE_RULES_AUDIT", None)
    try:
        yield
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_mode(
    tau_bin: Path,
    program: str,
    reps: int,
    reachable: bool,
    audit: bool,
    post_transform: bool,
    reachable_cache: bool,
) -> list[dict[str, object]]:
    with reachable_defs_mode(reachable, audit, post_transform, reachable_cache):
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
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--post-transform", action="store_true")
    parser.add_argument("--reachable-cache", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-reachable-defs-batched.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    expected = len(table_checks())
    program = batched_program(Path.cwd())
    baseline_runs = run_mode(
        args.tau_bin, program, args.reps, reachable=False,
        audit=False, post_transform=False, reachable_cache=False,
    )
    reachable_runs = run_mode(
        args.tau_bin, program, args.reps, reachable=True,
        audit=args.audit, post_transform=args.post_transform,
        reachable_cache=args.reachable_cache,
    )
    baseline = summarize_mode(baseline_runs)
    reachable = summarize_mode(reachable_runs)
    ok = check_runs(baseline_runs, expected) and check_runs(reachable_runs, expected)
    if args.audit:
        ok = ok and reachable["rr_reachable_defs_audit_rows"] == reachable[
            "rr_reachable_defs_audit_equal"
        ]
        ok = ok and reachable["rr_active_rules_audit_rows"] == reachable[
            "rr_active_rules_audit_equal_rows"
        ]
    summary = {
        "scope": (
            "batched table checks with value-inference skip, transformed-"
            "definition cache, and active-rule filtering enabled"
        ),
        "ok": ok,
        "audit": args.audit,
        "post_transform": args.post_transform,
        "reachable_cache": args.reachable_cache,
        "check_count": expected,
        "reps": args.reps,
        "baseline": baseline,
        "reachable": reachable,
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_sum_ms"]), float(reachable["elapsed_sum_ms"])
        ),
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]), float(reachable["solve_total_ms"])
        ),
        "rr_apply_formula_improvement_percent": pct_delta(
            float(baseline["rr_apply_formula_ms"]), float(reachable["rr_apply_formula_ms"])
        ),
        "rr_formula_transform_improvement_percent": pct_delta(
            float(baseline["rr_formula_transform_ms"]),
            float(reachable["rr_formula_transform_ms"]),
        ),
        "rr_formula_rewrite_improvement_percent": pct_delta(
            float(baseline["rr_formula_rewrite_ms"]),
            float(reachable["rr_formula_rewrite_ms"]),
        ),
        "reachable_defs_skipped": max(
            0.0,
            float(reachable["rr_reachable_defs_before"])
            - float(reachable["rr_reachable_defs_after"]),
        ),
        "boundary": (
            "This is an experimental pre-transform pruning pass. A positive "
            "result on the demo corpus is not enough for default enablement "
            "without a larger corpus and a proof or exhaustive audit over the "
            "intended recurrence-fragment semantics."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "audit": args.audit,
        "post_transform": args.post_transform,
        "reachable_cache": args.reachable_cache,
        "checks": expected,
        "reps": args.reps,
        "baseline_elapsed_ms": baseline["elapsed_sum_ms"],
        "reachable_elapsed_ms": reachable["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "reachable_solve_total_ms": reachable["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_transform_ms": baseline["rr_formula_transform_ms"],
        "reachable_transform_ms": reachable["rr_formula_transform_ms"],
        "rr_formula_transform_improvement_percent": summary[
            "rr_formula_transform_improvement_percent"
        ],
        "reachable_defs_rows": reachable["rr_reachable_defs_rows"],
        "reachable_defs_hits": reachable["rr_reachable_defs_hits"],
        "reachable_defs_before": reachable["rr_reachable_defs_before"],
        "reachable_defs_after": reachable["rr_reachable_defs_after"],
        "reachable_defs_skipped": summary["reachable_defs_skipped"],
        "reachable_audit_rows": reachable["rr_reachable_defs_audit_rows"],
        "reachable_audit_equal_rows": reachable["rr_reachable_defs_audit_equal"],
        "active_audit_rows": reachable["rr_active_rules_audit_rows"],
        "active_audit_equal_rows": reachable["rr_active_rules_audit_equal_rows"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
