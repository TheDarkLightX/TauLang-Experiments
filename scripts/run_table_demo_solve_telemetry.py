#!/usr/bin/env python3
"""Measure the `solve --tau` path used by the safe table demos.

This script is intentionally separate from the qelim telemetry corpus. The
table demos prove equivalence by asking Tau's solver whether a table expression
differs from its raw guarded-choice expansion. That path is `solve --tau`, not
the standalone `qelim` command.
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


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


def tau_source(path: Path) -> str:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def cases(root: Path) -> list[dict[str, str]]:
    full_style = tau_source(root / "examples/tau/full_style_taba_demo_v1.tau")
    protocol = tau_source(root / "examples/tau/protocol_firewall_priority_ladder_v1.tau")
    collateral = tau_source(root / "examples/tau/collateral_admission_reason_table_v1.tau")
    incident = tau_source(root / "examples/tau/incident_memory_table_v1.tau")
    pointwise = tau_source(root / "examples/tau/pointwise_revision_table_v1.tau")
    return [
        {
            "name": "tau_native_table_agrees_with_raw",
            "program": full_style
            + "\nsolve --tau (priority_quarantine_update(q,riskgate,reviewgate,depguard,seed,manualadd) != "
            + "priority_quarantine_raw(q,riskgate,reviewgate,depguard,seed,manualadd))",
        },
        {
            "name": "protocol_firewall_table_agrees_with_raw",
            "program": protocol
            + "\nsolve --tau (protocol_firewall_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != "
            + "protocol_firewall_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny))",
        },
        {
            "name": "collateral_reason_table_agrees_with_raw",
            "program": collateral
            + "\nsolve --tau (collateral_reason_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != "
            + "collateral_reason_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit))",
        },
        {
            "name": "incident_memory_table_agrees_with_raw",
            "program": incident
            + "\nsolve --tau (incident_memory_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != "
            + "incident_memory_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label))",
        },
        {
            "name": "pointwise_revision_entry_agrees_with_helper",
            "program": pointwise
            + "\nsolve --tau (pointwise_revise_entry(old,guard,replacement) != pointwise_revise_entry_raw(old,guard,replacement))",
        },
    ]


def parse_prefixed_stats(text: str, prefix: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if line.startswith(prefix):
            rows.append(dict(STAT_RE.findall(line)))
    return rows


def parse_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def run_tau(tau_bin: Path, program: str) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    env["TAU_SOLVE_STATS"] = "1"
    if os.environ.get("TAU_RR_STATS") == "1":
        env["TAU_RR_STATS"] = "1"
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
    solve_rows = parse_prefixed_stats(combined, "[solve_cmd]")
    infer_outer_rows = parse_prefixed_stats(combined, "[infer_outer]")
    infer_core_rows = parse_prefixed_stats(combined, "[infer_core]")
    infer_visit_rows = parse_prefixed_stats(combined, "[infer_visit]")
    infer_update_rows = parse_prefixed_stats(combined, "[infer_update]")
    rr_get_defs_rows = parse_prefixed_stats(combined, "[rr_get_defs]")
    rr_with_defs_rows = parse_prefixed_stats(combined, "[rr_with_defs]")
    rr_formula_rows = parse_prefixed_stats(combined, "[rr_formula]")
    clean_lines = [
        line.strip()
        for line in combined.splitlines()
        if not line.startswith("[solve_cmd]")
        and not line.startswith("[infer_outer]")
        and not line.startswith("[infer_core]")
        and not line.startswith("[infer_visit]")
        and not line.startswith("[infer_update]")
        and not line.startswith("[rr_get_defs]")
        and not line.startswith("[rr_with_defs]")
        and not line.startswith("[rr_formula]")
        and line.strip()
    ]
    last_line = clean_lines[-1] if clean_lines else ""
    return {
        "returncode": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 3),
        "last_line": last_line,
        "solve_stat_count": len(solve_rows),
        "solve_rows": solve_rows,
        "infer_outer_stat_count": len(infer_outer_rows),
        "infer_core_stat_count": len(infer_core_rows),
        "infer_visit_stat_count": len(infer_visit_rows),
        "infer_update_stat_count": len(infer_update_rows),
        "rr_get_defs_stat_count": len(rr_get_defs_rows),
        "rr_with_defs_stat_count": len(rr_with_defs_rows),
        "rr_formula_stat_count": len(rr_formula_rows),
        "infer_outer_rows": infer_outer_rows,
        "infer_core_rows": infer_core_rows,
        "infer_visit_rows": infer_visit_rows,
        "infer_update_rows": infer_update_rows,
        "rr_get_defs_rows": rr_get_defs_rows,
        "rr_with_defs_rows": rr_with_defs_rows,
        "rr_formula_rows": rr_formula_rows,
    }


def summarize_case(runs: list[dict[str, object]]) -> dict[str, object]:
    stats = [run["solve_rows"][0] for run in runs if run["solve_rows"]]
    if not stats:
        return {"has_stats": False}
    phase_names = ["apply_ms", "type_ms", "solve_ms", "total_ms"]
    means = {
        phase: round(statistics.mean(parse_float(row, phase) for row in stats), 6)
        for phase in phase_names
    }
    medians = {
        phase: round(statistics.median(parse_float(row, phase) for row in stats), 6)
        for phase in phase_names
    }
    dominant_phase = max(
        ["apply_ms", "type_ms", "solve_ms"],
        key=lambda phase: means[phase],
    )
    total = means["total_ms"] or 1.0
    return {
        "has_stats": True,
        "mean_ms": means,
        "median_ms": medians,
        "dominant_phase": dominant_phase,
        "solve_fraction": round(means["solve_ms"] / total, 6),
        "apply_fraction": round(means["apply_ms"] / total, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--rr-stats", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("results/local/table-demo-solve-telemetry.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    root = Path.cwd()
    rows = []
    ok = True
    if args.rr_stats:
        os.environ["TAU_RR_STATS"] = "1"
    for case in cases(root):
        runs = []
        for _ in range(args.reps):
            result = run_tau(args.tau_bin, case["program"])
            runs.append(result)
            ok = ok and result["returncode"] == 0
            ok = ok and result["last_line"] == "no solution"
            ok = ok and result["solve_stat_count"] == 1
        rows.append({
            "name": case["name"],
            "summary": summarize_case(runs),
            "runs": runs,
        })

    dominant_counts: dict[str, int] = {}
    for row in rows:
        phase = row["summary"].get("dominant_phase")
        if isinstance(phase, str):
            dominant_counts[phase] = dominant_counts.get(phase, 0) + 1

    summary = {
        "scope": "table-demo solver checks with solve telemetry enabled",
        "ok": ok,
        "case_count": len(rows),
        "reps": args.reps,
        "total_runs": len(rows) * args.reps,
        "dominant_phase_counts": dominant_counts,
        "rows": rows,
        "boundary": (
            "This measures the solver path used by the table demos. It is not "
            "evidence about the standalone qelim command backend."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
