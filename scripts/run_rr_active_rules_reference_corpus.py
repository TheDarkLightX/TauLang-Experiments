#!/usr/bin/env python3
"""Measure active RR rule filtering on ordinary Tau reference definitions.

This corpus avoids safe-table syntax. Both modes keep the prior RR candidates
enabled:

    TAU_RR_SKIP_VALUE_INFER=1
    TAU_RR_TRANSFORM_DEFS_CACHE=1

The only difference is:

    baseline: TAU_RR_ACTIVE_RULES unset
    active:   TAU_RR_ACTIVE_RULES=1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from pathlib import Path

from run_rr_skip_reference_solver_corpus import cases


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


def run_tau(tau_bin: Path, program: str, active: bool) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_SOLVE_STATS"] = "1"
    env["TAU_RR_STATS"] = "1"
    env["TAU_RR_SKIP_VALUE_INFER"] = "1"
    env["TAU_RR_TRANSFORM_DEFS_CACHE"] = "1"
    if active:
        env["TAU_RR_ACTIVE_RULES"] = "1"
    else:
        env.pop("TAU_RR_ACTIVE_RULES", None)

    argv = [
        str(tau_bin),
        "--charvar",
        "false",
        "-e",
        program,
        "--severity",
        "info",
        "--color",
        "false",
        "--status",
        "true",
    ]
    start = time.perf_counter()
    proc = subprocess.run(argv, env=env, text=True, capture_output=True, check=False)
    elapsed_ms = (time.perf_counter() - start) * 1000
    combined = proc.stdout + proc.stderr
    lines = clean_lines(combined)
    result_lines = [
        line for line in lines if line == "no solution" or line == "solution:"
    ]
    solve_rows = parse_prefixed_stats(combined, "[solve_cmd]")
    rr_with_defs_rows = parse_prefixed_stats(combined, "[rr_with_defs]")
    rr_formula_rows = parse_prefixed_stats(combined, "[rr_formula]")
    rr_active_rules_rows = parse_prefixed_stats(combined, "[rr_active_rules]")
    return {
        "mode": "active" if active else "baseline",
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "elapsed_ms": round(elapsed_ms, 3),
        "result_lines": result_lines,
        "has_no_solution": "no solution" in result_lines,
        "solve_stat_count": len(solve_rows),
        "rr_with_defs_stat_count": len(rr_with_defs_rows),
        "rr_formula_stat_count": len(rr_formula_rows),
        "rr_active_rules_stat_count": len(rr_active_rules_rows),
        "solve_total_ms": round(sum(as_float(row, "total_ms") for row in solve_rows), 6),
        "rr_apply_formula_ms": round(
            sum(as_float(row, "apply_formula_ms") for row in rr_with_defs_rows), 6
        ),
        "rr_formula_rewrite_ms": round(
            sum(as_float(row, "rewrite_ms") for row in rr_formula_rows), 6
        ),
        "rr_active_rules_before": round(
            sum(as_float(row, "before") for row in rr_active_rules_rows), 6
        ),
        "rr_active_rules_after": round(
            sum(as_float(row, "after") for row in rr_active_rules_rows), 6
        ),
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    elapsed = [float(row["elapsed_ms"]) for row in rows]
    return {
        "elapsed_sum_ms": round(sum(elapsed), 3),
        "elapsed_median_ms": round(statistics.median(elapsed), 3),
        "solve_total_ms": round(sum(float(row["solve_total_ms"]) for row in rows), 6),
        "rr_apply_formula_ms": round(
            sum(float(row["rr_apply_formula_ms"]) for row in rows), 6
        ),
        "rr_formula_rewrite_ms": round(
            sum(float(row["rr_formula_rewrite_ms"]) for row in rows), 6
        ),
        "rr_active_rules_rows": sum(int(row["rr_active_rules_stat_count"]) for row in rows),
        "rr_active_rules_before": round(
            sum(float(row["rr_active_rules_before"]) for row in rows), 6
        ),
        "rr_active_rules_after": round(
            sum(float(row["rr_active_rules_after"]) for row in rows), 6
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-active-rules-reference-corpus.json"))
    args = parser.parse_args()
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    baseline_runs = []
    active_runs = []
    ok = True
    for case in cases():
        baseline = run_tau(args.tau_bin, case.program, active=False)
        active = run_tau(args.tau_bin, case.program, active=True)
        baseline_runs.append(baseline)
        active_runs.append(active)
        ok = ok and bool(baseline["ok"]) and bool(active["ok"])
        ok = ok and bool(baseline["has_no_solution"]) and bool(active["has_no_solution"])
        ok = ok and baseline["result_lines"] == active["result_lines"]
        ok = ok and baseline["solve_stat_count"] == 1
        ok = ok and active["solve_stat_count"] == 1
        rows.append({
            "name": case.name,
            "baseline": baseline,
            "active": active,
        })

    baseline = summarize(baseline_runs)
    active = summarize(active_runs)
    summary = {
        "scope": "ordinary Tau reference-definition corpus with active RR rule filtering",
        "ok": ok,
        "case_count": len(rows),
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
        "rows": rows,
        "boundary": (
            "This avoids safe-table syntax, but remains a small synthetic "
            "reference-definition corpus. It is output-parity evidence, not a "
            "default-promotion proof."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "cases": len(rows),
        "baseline_elapsed_ms": baseline["elapsed_sum_ms"],
        "active_elapsed_ms": active["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "active_solve_total_ms": active["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_rewrite_ms": baseline["rr_formula_rewrite_ms"],
        "active_rewrite_ms": active["rr_formula_rewrite_ms"],
        "rr_formula_rewrite_improvement_percent": summary["rr_formula_rewrite_improvement_percent"],
        "active_rules_rows": active["rr_active_rules_rows"],
        "active_rules_before": active["rr_active_rules_before"],
        "active_rules_after": active["rr_active_rules_after"],
        "active_rules_skipped": summary["active_rules_skipped"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
