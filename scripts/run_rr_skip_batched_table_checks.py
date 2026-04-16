#!/usr/bin/env python3
"""Measure RR skip impact inside the batched safe-table check path.

This script removes most repeated Tau process startup from the measurement by
running the fifteen table-vs-raw solver obligations in one Tau command file.
It compares:

    baseline
    TAU_RR_SKIP_VALUE_INFER=1

The result is still a demo-corpus measurement, not a default Tau optimization
claim.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from run_table_demo_batched_checks import batched_program, table_checks


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


def parse_prefixed_stats(text: str, prefix: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if line.startswith(prefix):
            rows.append(dict(STAT_RE.findall(line)))
    return rows


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def clean_lines(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def run_batched(tau_bin: Path, program: str, skip: bool) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    env["TAU_CLI_FILE_MODE"] = "1"
    env["TAU_SOLVE_STATS"] = "1"
    env["TAU_RR_STATS"] = "1"
    if skip:
        env["TAU_RR_SKIP_VALUE_INFER"] = "1"
    else:
        env.pop("TAU_RR_SKIP_VALUE_INFER", None)
        env.pop("TAU_RR_SKIP_VALUE_INFER_AUDIT", None)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir="results/local",
        suffix=".taucmd",
        delete=False,
    ) as tmp:
        tmp.write(program)
        tmp_path = Path(tmp.name)

    argv = [
        str(tau_bin),
        "--charvar",
        "false",
        str(tmp_path),
        "--severity",
        "info",
        "--color",
        "false",
        "--status",
        "true",
    ]
    start = time.perf_counter()
    try:
        proc = subprocess.run(argv, env=env, text=True, capture_output=True, check=False)
    finally:
        tmp_path.unlink(missing_ok=True)
    elapsed_ms = (time.perf_counter() - start) * 1000
    combined = proc.stdout + proc.stderr
    lines = clean_lines(combined)
    solve_result_lines = [
        line for line in lines if line == "no solution" or line == "solution:"
    ]
    solve_rows = parse_prefixed_stats(combined, "[solve_cmd]")
    rr_get_defs_rows = parse_prefixed_stats(combined, "[rr_get_defs]")
    rr_with_defs_rows = parse_prefixed_stats(combined, "[rr_with_defs]")
    rr_formula_rows = parse_prefixed_stats(combined, "[rr_formula]")
    rr_transform_defs_cache_rows = parse_prefixed_stats(combined, "[rr_transform_defs_cache]")
    rr_skip_audit_rows = parse_prefixed_stats(combined, "[rr_skip_audit]")
    branch_counts: dict[str, int] = {}
    for row in rr_get_defs_rows:
        branch = row.get("branch", "missing")
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
    return {
        "mode": "skip" if skip else "baseline",
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "elapsed_ms": round(elapsed_ms, 3),
        "line_count": len(lines),
        "solve_result_count": len(solve_result_lines),
        "no_solution_count": sum(1 for line in solve_result_lines if line == "no solution"),
        "solve_stat_count": len(solve_rows),
        "rr_get_defs_stat_count": len(rr_get_defs_rows),
        "rr_with_defs_stat_count": len(rr_with_defs_rows),
        "rr_formula_stat_count": len(rr_formula_rows),
        "rr_transform_defs_cache_stat_count": len(rr_transform_defs_cache_rows),
        "rr_transform_defs_cache_hit_count": sum(
            1 for row in rr_transform_defs_cache_rows if row.get("hit") == "1"
        ),
        "rr_skip_audit_stat_count": len(rr_skip_audit_rows),
        "solve_total_ms": round(sum(as_float(row, "total_ms") for row in solve_rows), 6),
        "solve_apply_ms": round(sum(as_float(row, "apply_ms") for row in solve_rows), 6),
        "rr_get_ms": round(sum(as_float(row, "get_rr_ms") for row in rr_with_defs_rows), 6),
        "rr_apply_formula_ms": round(
            sum(as_float(row, "apply_formula_ms") for row in rr_with_defs_rows), 6
        ),
        "rr_total_ms": round(sum(as_float(row, "total_ms") for row in rr_with_defs_rows), 6),
        "rr_formula_total_ms": round(sum(as_float(row, "total_ms") for row in rr_formula_rows), 6),
        "rr_formula_transform_ms": round(
            sum(as_float(row, "transform_ms") for row in rr_formula_rows), 6
        ),
        "rr_formula_fixed_point_ms": round(
            sum(as_float(row, "fixed_point_ms") for row in rr_formula_rows), 6
        ),
        "rr_formula_rewrite_ms": round(
            sum(as_float(row, "rewrite_ms") for row in rr_formula_rows), 6
        ),
        "rr_infer_ms": round(sum(as_float(row, "infer_ms") for row in rr_get_defs_rows), 6),
        "rr_branch_counts": branch_counts,
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def summarize_mode(runs: list[dict[str, object]]) -> dict[str, object]:
    elapsed = [float(run["elapsed_ms"]) for run in runs]
    return {
        "runs": runs,
        "run_count": len(runs),
        "elapsed_sum_ms": round(sum(elapsed), 3),
        "elapsed_median_ms": round(statistics.median(elapsed), 3),
        "solve_total_ms": round(sum(float(run["solve_total_ms"]) for run in runs), 6),
        "solve_apply_ms": round(sum(float(run["solve_apply_ms"]) for run in runs), 6),
        "rr_get_ms": round(sum(float(run["rr_get_ms"]) for run in runs), 6),
        "rr_apply_formula_ms": round(
            sum(float(run["rr_apply_formula_ms"]) for run in runs), 6
        ),
        "rr_total_ms": round(sum(float(run["rr_total_ms"]) for run in runs), 6),
        "rr_formula_total_ms": round(
            sum(float(run["rr_formula_total_ms"]) for run in runs), 6
        ),
        "rr_formula_transform_ms": round(
            sum(float(run["rr_formula_transform_ms"]) for run in runs), 6
        ),
        "rr_formula_fixed_point_ms": round(
            sum(float(run["rr_formula_fixed_point_ms"]) for run in runs), 6
        ),
        "rr_formula_rewrite_ms": round(
            sum(float(run["rr_formula_rewrite_ms"]) for run in runs), 6
        ),
        "rr_infer_ms": round(sum(float(run["rr_infer_ms"]) for run in runs), 6),
        "rr_transform_defs_cache_rows": sum(
            int(run["rr_transform_defs_cache_stat_count"]) for run in runs
        ),
        "rr_transform_defs_cache_hits": sum(
            int(run["rr_transform_defs_cache_hit_count"]) for run in runs
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-skip-batched-table-checks.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    root = Path.cwd()
    expected = len(table_checks())
    program = batched_program(root)
    baseline_runs = [run_batched(args.tau_bin, program, skip=False) for _ in range(args.reps)]
    skip_runs = [run_batched(args.tau_bin, program, skip=True) for _ in range(args.reps)]
    ok = True
    for run in baseline_runs + skip_runs:
        ok = ok and bool(run["ok"])
        ok = ok and run["solve_result_count"] == expected
        ok = ok and run["no_solution_count"] == expected
        ok = ok and run["solve_stat_count"] == expected
        ok = ok and run["rr_get_defs_stat_count"] == expected
        ok = ok and run["rr_with_defs_stat_count"] == expected
        ok = ok and run["rr_formula_stat_count"] == expected

    baseline = summarize_mode(baseline_runs)
    skip = summarize_mode(skip_runs)
    summary = {
        "scope": "batched safe-table solver obligations with RR telemetry",
        "ok": ok,
        "check_count": expected,
        "reps": args.reps,
        "baseline": baseline,
        "skip": skip,
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_sum_ms"]), float(skip["elapsed_sum_ms"])
        ),
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]), float(skip["solve_total_ms"])
        ),
        "rr_get_improvement_percent": pct_delta(
            float(baseline["rr_get_ms"]), float(skip["rr_get_ms"])
        ),
        "rr_infer_improvement_percent": pct_delta(
            float(baseline["rr_infer_ms"]), float(skip["rr_infer_ms"])
        ),
        "boundary": (
            "This measures the batched table-demo solver path. It is stronger "
            "than one-process-per-check timing, but still scoped to the demo "
            "corpus and not a default Tau optimization claim."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "baseline_elapsed_ms": baseline["elapsed_sum_ms"],
        "skip_elapsed_ms": skip["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "skip_solve_total_ms": skip["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_rr_get_ms": baseline["rr_get_ms"],
        "skip_rr_get_ms": skip["rr_get_ms"],
        "rr_get_improvement_percent": summary["rr_get_improvement_percent"],
        "baseline_rr_apply_formula_ms": baseline["rr_apply_formula_ms"],
        "skip_rr_apply_formula_ms": skip["rr_apply_formula_ms"],
        "skip_rr_formula_transform_ms": skip["rr_formula_transform_ms"],
        "skip_rr_formula_rewrite_ms": skip["rr_formula_rewrite_ms"],
        "skip_rr_transform_defs_cache_hits": skip["rr_transform_defs_cache_hits"],
        "skip_rr_transform_defs_cache_rows": skip["rr_transform_defs_cache_rows"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
