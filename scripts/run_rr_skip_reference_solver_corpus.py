#!/usr/bin/env python3
"""Measure RR skip on ordinary Tau reference definitions.

This corpus avoids the safe-table syntax and instead uses small named Tau
definitions whose equivalences are checked with `solve --tau`.

It compares:

    baseline
    TAU_RR_SKIP_VALUE_INFER=1
    TAU_RR_SKIP_VALUE_INFER=1 plus TAU_RR_SKIP_VALUE_INFER_AUDIT=1

Audit mode computes the full inference path too and checks structural equality,
so it is correctness evidence rather than a performance mode.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Case:
    name: str
    program: str


def cases() -> list[Case]:
    return [
        Case(
            "identity_alias",
            "id(x):tau := x. double(x):tau := id(id(x)). "
            "solve --tau (double(x) != x)",
        ),
        Case(
            "join_commutes",
            "lhs(x,y):tau := x | y. rhs(x,y):tau := y | x. "
            "solve --tau (lhs(x,y) != rhs(x,y))",
        ),
        Case(
            "meet_commutes",
            "lhs(x,y):tau := x & y. rhs(x,y):tau := y & x. "
            "solve --tau (lhs(x,y) != rhs(x,y))",
        ),
        Case(
            "absorption_join",
            "absorbed(x,y):tau := x | (x & y). "
            "solve --tau (absorbed(x,y) != x)",
        ),
        Case(
            "absorption_meet",
            "absorbed(x,y):tau := x & (x | y). "
            "solve --tau (absorbed(x,y) != x)",
        ),
        Case(
            "double_prime",
            "dp(x):tau := x''. solve --tau (dp(x) != x)",
        ),
        Case(
            "de_morgan_meet",
            "lhs(x,y):tau := (x & y)'. rhs(x,y):tau := x' | y'. "
            "solve --tau (lhs(x,y) != rhs(x,y))",
        ),
        Case(
            "de_morgan_join",
            "lhs(x,y):tau := (x | y)'. rhs(x,y):tau := x' & y'. "
            "solve --tau (lhs(x,y) != rhs(x,y))",
        ),
        Case(
            "guarded_choice_identity",
            "choice(g,a,x):tau := (g & a) | (g' & x). "
            "same(g,a,x):tau := choice(g,a,x). "
            "solve --tau (same(g,a,x) != ((g & a) | (g' & x)))",
        ),
    ]


def parse_prefixed_stats(text: str, prefix: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if line.startswith(prefix):
            rows.append(dict(STAT_RE.findall(line)))
    return rows


def clean_lines(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def run_tau(tau_bin: Path, program: str, mode: str) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_SOLVE_STATS"] = "1"
    env["TAU_RR_STATS"] = "1"
    if mode in {"skip", "audit"}:
        env["TAU_RR_SKIP_VALUE_INFER"] = "1"
    else:
        env.pop("TAU_RR_SKIP_VALUE_INFER", None)
    if mode == "audit":
        env["TAU_RR_SKIP_VALUE_INFER_AUDIT"] = "1"
    else:
        env.pop("TAU_RR_SKIP_VALUE_INFER_AUDIT", None)

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
    solve_rows = parse_prefixed_stats(combined, "[solve_cmd]")
    rr_get_defs_rows = parse_prefixed_stats(combined, "[rr_get_defs]")
    rr_with_defs_rows = parse_prefixed_stats(combined, "[rr_with_defs]")
    rr_skip_audit_rows = parse_prefixed_stats(combined, "[rr_skip_audit]")
    branch_counts: dict[str, int] = {}
    for row in rr_get_defs_rows:
        branch = row.get("branch", "missing")
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
    return {
        "mode": mode,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "elapsed_ms": round(elapsed_ms, 3),
        "has_no_solution": "no solution" in lines,
        "last_line": lines[-1] if lines else "",
        "solve_stat_count": len(solve_rows),
        "rr_get_defs_stat_count": len(rr_get_defs_rows),
        "rr_with_defs_stat_count": len(rr_with_defs_rows),
        "rr_skip_audit_stat_count": len(rr_skip_audit_rows),
        "audit_structural_equal_count": sum(
            1
            for row in rr_skip_audit_rows
            if row.get("inferred") == "1" and row.get("structural_equal") == "1"
        ),
        "solve_total_ms": round(sum(as_float(row, "total_ms") for row in solve_rows), 6),
        "solve_apply_ms": round(sum(as_float(row, "apply_ms") for row in solve_rows), 6),
        "rr_get_ms": round(sum(as_float(row, "get_rr_ms") for row in rr_with_defs_rows), 6),
        "rr_total_ms": round(sum(as_float(row, "total_ms") for row in rr_with_defs_rows), 6),
        "rr_infer_ms": round(sum(as_float(row, "infer_ms") for row in rr_get_defs_rows), 6),
        "rr_branch_counts": branch_counts,
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def summarize_mode(rows: list[dict[str, object]]) -> dict[str, object]:
    elapsed = [float(row["elapsed_ms"]) for row in rows]
    return {
        "elapsed_sum_ms": round(sum(elapsed), 3),
        "elapsed_median_ms": round(statistics.median(elapsed), 3),
        "solve_total_ms": round(sum(float(row["solve_total_ms"]) for row in rows), 6),
        "solve_apply_ms": round(sum(float(row["solve_apply_ms"]) for row in rows), 6),
        "rr_get_ms": round(sum(float(row["rr_get_ms"]) for row in rows), 6),
        "rr_total_ms": round(sum(float(row["rr_total_ms"]) for row in rows), 6),
        "rr_infer_ms": round(sum(float(row["rr_infer_ms"]) for row in rows), 6),
        "audit_rows": sum(int(row["rr_skip_audit_stat_count"]) for row in rows),
        "audit_structural_equal_rows": sum(int(row["audit_structural_equal_count"]) for row in rows),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-skip-reference-solver-corpus.json"))
    args = parser.parse_args()
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    corpus = cases()
    rows = []
    baseline_runs = []
    skip_runs = []
    audit_runs = []
    ok = True
    for case in corpus:
        baseline = run_tau(args.tau_bin, case.program, "baseline")
        skip = run_tau(args.tau_bin, case.program, "skip")
        audit = run_tau(args.tau_bin, case.program, "audit")
        baseline_runs.append(baseline)
        skip_runs.append(skip)
        audit_runs.append(audit)
        for run in [baseline, skip, audit]:
            ok = ok and bool(run["ok"])
            ok = ok and bool(run["has_no_solution"])
            ok = ok and run["solve_stat_count"] == 1
            ok = ok and run["rr_get_defs_stat_count"] == 1
            ok = ok and run["rr_with_defs_stat_count"] == 1
        ok = ok and audit["rr_skip_audit_stat_count"] == 1
        ok = ok and audit["audit_structural_equal_count"] == 1
        rows.append({
            "name": case.name,
            "baseline": baseline,
            "skip": skip,
            "audit": audit,
        })

    baseline_summary = summarize_mode(baseline_runs)
    skip_summary = summarize_mode(skip_runs)
    audit_summary = summarize_mode(audit_runs)
    summary = {
        "scope": "ordinary Tau reference-definition solver corpus",
        "ok": ok,
        "case_count": len(corpus),
        "baseline": baseline_summary,
        "skip": skip_summary,
        "audit": audit_summary,
        "elapsed_improvement_percent": pct_delta(
            float(baseline_summary["elapsed_sum_ms"]),
            float(skip_summary["elapsed_sum_ms"]),
        ),
        "solve_total_improvement_percent": pct_delta(
            float(baseline_summary["solve_total_ms"]),
            float(skip_summary["solve_total_ms"]),
        ),
        "rr_get_improvement_percent": pct_delta(
            float(baseline_summary["rr_get_ms"]),
            float(skip_summary["rr_get_ms"]),
        ),
        "rr_infer_improvement_percent": pct_delta(
            float(baseline_summary["rr_infer_ms"]),
            float(skip_summary["rr_infer_ms"]),
        ),
        "rows": rows,
        "boundary": (
            "This broadens RR skip evidence beyond safe-table syntax, but it "
            "is still a synthetic reference-definition corpus, not a full Tau "
            "workload benchmark. A three-variable distributivity candidate was "
            "left out because this Tau build segfaulted before solver stats in "
            "the baseline and skip paths, which makes it invalid performance "
            "evidence for this skip."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "case_count": len(corpus),
        "baseline_elapsed_ms": baseline_summary["elapsed_sum_ms"],
        "skip_elapsed_ms": skip_summary["elapsed_sum_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "baseline_solve_total_ms": baseline_summary["solve_total_ms"],
        "skip_solve_total_ms": skip_summary["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_rr_get_ms": baseline_summary["rr_get_ms"],
        "skip_rr_get_ms": skip_summary["rr_get_ms"],
        "rr_get_improvement_percent": summary["rr_get_improvement_percent"],
        "audit_rows": audit_summary["audit_rows"],
        "audit_structural_equal_rows": audit_summary["audit_structural_equal_rows"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
