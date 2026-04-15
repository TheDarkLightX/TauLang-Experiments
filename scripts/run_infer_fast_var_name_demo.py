#!/usr/bin/env python3
"""Compare baseline type inference with the var-name fast path.

The patched Tau binary exposes an opt-in optimization:

    TAU_INFER_FAST_VAR_NAME=1

When enabled, type inference skips leave-phase default reconstruction for
`var_name` leaf nodes. This script runs the representative safe-table solver
checks in baseline and fast modes, checks output parity, and records telemetry.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from pathlib import Path

import run_table_demo_solve_telemetry as solve_telemetry


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def as_int(row: dict[str, str], key: str) -> int:
    return int(row.get(key, "0") or "0")


def run_mode(tau_bin: Path, reps: int, fast: bool) -> dict[str, object]:
    old_rr = os.environ.get("TAU_RR_STATS")
    old_fast = os.environ.get("TAU_INFER_FAST_VAR_NAME")
    os.environ["TAU_RR_STATS"] = "1"
    if fast:
        os.environ["TAU_INFER_FAST_VAR_NAME"] = "1"
    else:
        os.environ.pop("TAU_INFER_FAST_VAR_NAME", None)

    try:
        rows: list[dict[str, object]] = []
        ok = True
        for case in solve_telemetry.cases(Path.cwd()):
            runs = []
            for _ in range(reps):
                result = solve_telemetry.run_tau(tau_bin, case["program"])
                runs.append(result)
                ok = ok and result["returncode"] == 0
                ok = ok and result["last_line"] == "no solution"
                ok = ok and result["solve_stat_count"] == 1
                ok = ok and result["infer_visit_stat_count"] >= 1
            rows.append({"name": case["name"], "runs": runs})
    finally:
        if old_rr is None:
            os.environ.pop("TAU_RR_STATS", None)
        else:
            os.environ["TAU_RR_STATS"] = old_rr
        if old_fast is None:
            os.environ.pop("TAU_INFER_FAST_VAR_NAME", None)
        else:
            os.environ["TAU_INFER_FAST_VAR_NAME"] = old_fast

    solve_total_ms = 0.0
    solve_apply_ms = 0.0
    elapsed_ms = 0.0
    fast_hits = 0
    enter_name_var = 0
    enter_name_var_unique = 0
    enter_name_var_repeated = 0
    for row in rows:
        for run in row["runs"]:
            solve = run["solve_rows"][0] if run["solve_rows"] else {}
            solve_total_ms += as_float(solve, "total_ms")
            solve_apply_ms += as_float(solve, "apply_ms")
            elapsed_ms += float(run["elapsed_ms"])
            for visit in run["infer_visit_rows"]:
                fast_hits += as_int(visit, "leave_name_var_fastpath")
                enter_name_var += as_int(visit, "enter_name_var")
                enter_name_var_unique += as_int(visit, "enter_name_var_unique")
                enter_name_var_repeated += as_int(visit, "enter_name_var_repeated")

    return {
        "mode": "fast" if fast else "baseline",
        "ok": ok,
        "case_count": len(rows),
        "reps": reps,
        "run_count": len(rows) * reps,
        "solve_total_ms": round(solve_total_ms, 6),
        "solve_apply_ms": round(solve_apply_ms, 6),
        "elapsed_ms": round(elapsed_ms, 3),
        "leave_name_var_fastpath": fast_hits,
        "enter_name_var": enter_name_var,
        "enter_name_var_unique": enter_name_var_unique,
        "enter_name_var_repeated": enter_name_var_repeated,
        "median_elapsed_ms": round(
            statistics.median(
                float(run["elapsed_ms"])
                for row in rows
                for run in row["runs"]
            ),
            3,
        ),
        "rows": rows,
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--out", type=Path, default=Path("results/local/infer-fast-var-name-demo.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    baseline = run_mode(args.tau_bin, args.reps, fast=False)
    fast = run_mode(args.tau_bin, args.reps, fast=True)
    ok = bool(baseline["ok"]) and bool(fast["ok"])
    summary = {
        "scope": "feature-gated Tau type-inference var_name fast-path comparison",
        "ok": ok,
        "baseline": baseline,
        "fast": fast,
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]),
            float(fast["solve_total_ms"]),
        ),
        "solve_apply_improvement_percent": pct_delta(
            float(baseline["solve_apply_ms"]),
            float(fast["solve_apply_ms"]),
        ),
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_ms"]),
            float(fast["elapsed_ms"]),
        ),
        "boundary": (
            "This is a table-demo solver telemetry comparison for one "
            "feature-gated inference shortcut. It is not a general Tau speedup "
            "claim."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "fast_solve_total_ms": fast["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_elapsed_ms": baseline["elapsed_ms"],
        "fast_elapsed_ms": fast["elapsed_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "fastpath_hits": fast["leave_name_var_fastpath"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
