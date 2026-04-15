#!/usr/bin/env python3
"""Exercise Tau's native run loop with TAU_RUN_STATS enabled.

This is runtime telemetry plus an opt-in IO-rebuild skip check. The goal is to
pin down the native interpreter surface that a future delta cache would have to
preserve: step count, path attempts, memory growth, update revision behavior,
and whether unchanged IO stream sets can avoid rebuilds without changing output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


RUN_STATS_RE = re.compile(r"\[run_step\]\s+(.*)")
UPDATE_STATS_RE = re.compile(r"\[update_revision\]\s+(.*)")
KV_RE = re.compile(r"([A-Za-z_]+)=([^ ]+)")


def parse_stats(output: str, pattern: re.Pattern[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for match in pattern.finditer(output):
        row: dict[str, object] = {}
        for key, value in KV_RE.findall(match.group(1)):
            if key.endswith("_ms"):
                row[key] = float(value)
            else:
                row[key] = int(value)
        rows.append(row)
    return rows


def run_tau(tau_bin: Path, *, skip_unchanged_io_rebuild: bool) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_RUN_STATS"] = "1"
    if skip_unchanged_io_rebuild:
        env["TAU_SKIP_UNCHANGED_IO_REBUILD"] = "1"
    else:
        env.pop("TAU_SKIP_UNCHANGED_IO_REBUILD", None)
    proc = subprocess.run(
        [
            str(tau_bin),
            "--charvar",
            "false",
            "-e",
            "run u[t] = i1[t]",
            "--severity",
            "info",
            "--color",
            "false",
            "--status",
            "true",
        ],
        input="o1[t] = 1\no2[t] = 0\no1[t] = 0\n\n",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    run_stats = parse_stats(combined, RUN_STATS_RE)
    update_stats = parse_stats(combined, UPDATE_STATS_RE)
    return {
        "returncode": proc.returncode,
        "run_stats": run_stats,
        "update_stats": update_stats,
        "stdout": proc.stdout,
        "stderr_tail": proc.stderr[-1200:],
    }


def summarize_run(result: dict[str, object]) -> dict[str, object]:
    run_stats = result["run_stats"]
    update_stats = result["update_stats"]
    assert isinstance(run_stats, list)
    assert isinstance(update_stats, list)
    accepted_updates = [
        row for row in update_stats if int(row.get("accepted", 0)) == 1
    ]
    return {
        "returncode": result["returncode"],
        "step_count": len(run_stats),
        "update_revision_count": len(update_stats),
        "accepted_update_count": len(accepted_updates),
        "total_paths_attempted": sum(int(row["paths_attempted"]) for row in run_stats),
        "total_paths_solved": sum(int(row["paths_solved"]) for row in run_stats),
        "total_outputs": sum(int(row["outputs"]) for row in run_stats),
        "total_revisions_attempted": sum(
            int(row.get("revisions_attempted", 0)) for row in accepted_updates
        ),
        "total_added_parts": sum(int(row.get("added_parts", 0)) for row in accepted_updates),
        "input_rebuild_skipped": sum(
            int(row.get("input_rebuild_skipped", 0)) for row in accepted_updates
        ),
        "output_rebuild_skipped": sum(
            int(row.get("output_rebuild_skipped", 0)) for row in accepted_updates
        ),
        "final_memory_size": int(run_stats[-1]["memory_after"]) if run_stats else 0,
        "max_step_ms": max(float(row["step_ms"]) for row in run_stats) if run_stats else 0,
        "run_stats": run_stats,
        "update_stats": update_stats,
    }


def comparable_output(result: dict[str, object]) -> str:
    stdout = result["stdout"]
    assert isinstance(stdout, str)
    return "\n".join(line.rstrip() for line in stdout.splitlines())


def summarize(baseline: dict[str, object], optimized: dict[str, object]) -> dict[str, object]:
    baseline_summary = summarize_run(baseline)
    optimized_summary = summarize_run(optimized)
    output_parity = comparable_output(baseline) == comparable_output(optimized)
    shape_parity = {
        key: baseline_summary[key] == optimized_summary[key]
        for key in [
            "step_count",
            "update_revision_count",
            "accepted_update_count",
            "total_paths_attempted",
            "total_paths_solved",
            "total_outputs",
            "total_revisions_attempted",
            "total_added_parts",
            "final_memory_size",
        ]
    }
    ok = (
        baseline_summary["returncode"] == 0
        and optimized_summary["returncode"] == 0
        and baseline_summary["step_count"] >= 3
        and optimized_summary["input_rebuild_skipped"] > 0
        and optimized_summary["output_rebuild_skipped"] > 0
        and output_parity
        and all(shape_parity.values())
    )
    return {
        "scope": "native Tau run-loop telemetry for update-stream pointwise revision",
        "ok": ok,
        "output_parity": output_parity,
        "shape_parity": shape_parity,
        "baseline": baseline_summary,
        "optimized": optimized_summary,
        "boundary": (
            "This is a feature-gated native IO-rebuild skip plus telemetry. "
            "It only skips unchanged stream sets when the active stream class "
            "declares rebuild skipping safe. It does not implement the "
            "incremental delta cache."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-runtime-stats-demo.json"))
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    baseline = run_tau(args.tau_bin, skip_unchanged_io_rebuild=False)
    optimized = run_tau(args.tau_bin, skip_unchanged_io_rebuild=True)
    summary = summarize(baseline, optimized)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
