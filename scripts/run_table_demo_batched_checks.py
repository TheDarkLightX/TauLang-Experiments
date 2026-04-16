#!/usr/bin/env python3
"""Run the safe-table equivalence checks in one Tau process.

Tau's CLI grammar accepts multiple REPL commands in one `-e` string when every
command after the first is prefixed by a dot:

    solve --tau A . solve --tau B

This harness compares the older one-process-per-check path against that batched
CLI shape. Unlike the compound mismatch query, this keeps one solver result per
obligation. It changes command loading and parsing overhead, not Tau semantics.
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

from run_table_demo_compound_check import individual_program, table_checks, tau_source


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean_lines(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def solve_command(diff: str) -> str:
    return f"solve --tau ({diff})"


def batched_program(root: Path) -> str:
    checks = table_checks()
    sources: list[str] = []
    seen = set()
    for check in checks:
        if check.source not in seen:
            sources.append(tau_source(root / check.source))
            seen.add(check.source)
    commands = [solve_command(check.diff) for check in checks]
    cli_commands = [commands[0], *[f". {command}" for command in commands[1:]]]
    return "\n".join(sources + cli_commands)


def run_tau(tau_bin: Path, program: str) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
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
    lines = clean_lines(proc.stdout + proc.stderr)
    solve_lines = [line for line in lines if line == "no solution" or line == "solution:"]
    return {
        "returncode": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 3),
        "line_count": len(lines),
        "solve_result_count": len(solve_lines),
        "no_solution_count": sum(1 for line in solve_lines if line == "no solution"),
        "last_line": lines[-1] if lines else "",
        "ok": proc.returncode == 0,
    }


def summarize_elapsed(values: list[float]) -> dict[str, float]:
    return {
        "sum_ms": round(sum(values), 3),
        "median_ms": round(statistics.median(values), 3) if values else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("results/local/table-demo-batched-checks.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    root = Path.cwd()
    checks = table_checks()
    individual_runs = []
    batch_runs = []
    for _ in range(args.reps):
        for check in checks:
            individual_runs.append(run_tau(args.tau_bin, individual_program(root, check)))
        batch_runs.append(run_tau(args.tau_bin, batched_program(root)))

    individual_elapsed = [float(run["elapsed_ms"]) for run in individual_runs]
    batch_elapsed = [float(run["elapsed_ms"]) for run in batch_runs]
    expected_batch_results = len(checks)
    individual_ok = all(
        bool(run["ok"])
        and run["solve_result_count"] == 1
        and run["no_solution_count"] == 1
        for run in individual_runs
    )
    batch_ok = all(
        bool(run["ok"])
        and run["solve_result_count"] == expected_batch_results
        and run["no_solution_count"] == expected_batch_results
        for run in batch_runs
    )
    individual_sum = sum(individual_elapsed)
    batch_sum = sum(batch_elapsed)
    elapsed_reduction = (
        100.0 * (individual_sum - batch_sum) / individual_sum
        if individual_sum
        else 0.0
    )
    summary = {
        "scope": "safe table demo equivalence checks only",
        "ok": individual_ok and batch_ok,
        "check_count": len(checks),
        "reps": args.reps,
        "individual": summarize_elapsed(individual_elapsed),
        "batched": summarize_elapsed(batch_elapsed),
        "elapsed_reduction_percent": round(elapsed_reduction, 3),
        "individual_processes": len(individual_runs),
        "batched_processes": len(batch_runs),
        "expected_results_per_batch": expected_batch_results,
        "individual_runs": individual_runs,
        "batch_runs": batch_runs,
        "cli_shape": "cmd_1 . cmd_2 . ... . cmd_n",
        "boundary": (
            "This is a CLI batching and demo-harness optimization. It preserves "
            "one solver result per obligation, but it does not change Tau's "
            "solver, table semantics, or parser grammar."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
