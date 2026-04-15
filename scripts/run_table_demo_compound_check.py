#!/usr/bin/env python3
"""Compare separate table-demo checks against one compound mismatch query.

Tau's `-e` path accepts one REPL command in this harness. It does not accept a
list of `solve` commands. The safe batching law is therefore logical, not
syntactic:

    unsat(diff_1 or ... or diff_n) implies every diff_i is unsat.

This wrapper measures that compound check against the individual public
table-vs-raw checks.
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


@dataclass(frozen=True)
class TableCheck:
    name: str
    source: str
    diff: str


def tau_source(path: Path) -> str:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def table_checks() -> list[TableCheck]:
    full = "examples/tau/full_style_taba_demo_v1.tau"
    protocol = "examples/tau/protocol_firewall_priority_ladder_v1.tau"
    collateral = "examples/tau/collateral_admission_reason_table_v1.tau"
    incident = "examples/tau/incident_memory_table_v1.tau"
    pointwise = "examples/tau/pointwise_revision_table_v1.tau"
    return [
        TableCheck(
            "tau_native_table_agrees_with_raw",
            full,
            "priority_quarantine_update(q,riskgate,reviewgate,depguard,seed,manualadd) != "
            "priority_quarantine_raw(q,riskgate,reviewgate,depguard,seed,manualadd)",
        ),
        TableCheck(
            "protocol_firewall_table_agrees_with_raw",
            protocol,
            "protocol_firewall_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != "
            "protocol_firewall_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny)",
        ),
        TableCheck(
            "protocol_firewall_emergency_priority",
            protocol,
            "protocol_firewall_emergency_slice_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != "
            "protocol_firewall_emergency_slice_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny)",
        ),
        TableCheck(
            "protocol_firewall_oracle_slice",
            protocol,
            "protocol_firewall_oracle_slice_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != "
            "protocol_firewall_oracle_slice_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny)",
        ),
        TableCheck(
            "collateral_reason_table_agrees_with_raw",
            collateral,
            "collateral_reason_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != "
            "collateral_reason_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit)",
        ),
        TableCheck(
            "collateral_reason_registry_priority",
            collateral,
            "collateral_registry_priority_slice_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != "
            "collateral_registry_priority_slice_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit)",
        ),
        TableCheck(
            "collateral_reason_provenance_slice",
            collateral,
            "collateral_provenance_slice_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != "
            "collateral_provenance_slice_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit)",
        ),
        TableCheck(
            "incident_memory_table_agrees_with_raw",
            incident,
            "incident_memory_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != "
            "incident_memory_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label)",
        ),
        TableCheck(
            "incident_memory_exploit_priority",
            incident,
            "incident_memory_exploit_slice_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != "
            "incident_memory_exploit_slice_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label)",
        ),
        TableCheck(
            "incident_memory_clear_slice",
            incident,
            "incident_memory_clear_slice_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != "
            "incident_memory_clear_slice_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label)",
        ),
        TableCheck(
            "pointwise_revision_entry_agrees_with_helper",
            pointwise,
            "pointwise_revise_entry(old,guard,replacement) != pointwise_revise_entry_raw(old,guard,replacement)",
        ),
        TableCheck(
            "pointwise_revision_whole_table_agrees",
            pointwise,
            "pointwise_revision_diff(old_mint,old_borrow,old_liquidate,guard_mint,guard_borrow,guard_liquidate,replacement_mint,replacement_borrow,replacement_liquidate) != 0",
        ),
        TableCheck(
            "pointwise_revision_outside_guard_preserves_old",
            pointwise,
            "pointwise_revision_outside_guard(old,guard,replacement) != pointwise_revision_outside_guard_raw(old,guard,replacement)",
        ),
        TableCheck(
            "pointwise_revision_inside_guard_uses_replacement",
            pointwise,
            "pointwise_revision_inside_guard(old,guard,replacement) != pointwise_revision_inside_guard_raw(old,guard,replacement)",
        ),
        TableCheck(
            "pointwise_revision_idempotent",
            pointwise,
            "pointwise_revision_twice(old,guard,replacement) != pointwise_revision_once(old,guard,replacement)",
        ),
    ]


def clean_lines(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


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
    last_line = lines[-1] if lines else ""
    return {
        "returncode": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 3),
        "last_line": last_line,
        "ok": proc.returncode == 0 and last_line == "no solution",
    }


def individual_program(root: Path, check: TableCheck) -> str:
    return f"{tau_source(root / check.source)}\nsolve --tau ({check.diff})"


def compound_program(root: Path, checks: list[TableCheck]) -> str:
    sources = []
    seen = set()
    for check in checks:
        if check.source not in seen:
            sources.append(tau_source(root / check.source))
            seen.add(check.source)
    compound_diff = " || ".join(f"({check.diff})" for check in checks)
    return "\n".join(sources) + f"\nsolve --tau ({compound_diff})"


def summarize_elapsed(values: list[float]) -> dict[str, float]:
    return {
        "sum_ms": round(sum(values), 3),
        "median_ms": round(statistics.median(values), 3) if values else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument(
        "--mode",
        choices=["compare", "compound-only", "individual-only"],
        default="compare",
        help=(
            "compare runs the individual baseline and the compound query; "
            "compound-only runs only the optimized obligation shape"
        ),
    )
    parser.add_argument("--out", type=Path, default=Path("results/local/table-demo-compound-check.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    root = Path.cwd()
    checks = table_checks()
    individual_runs = []
    compound_runs = []
    for _ in range(args.reps):
        if args.mode in {"compare", "individual-only"}:
            for check in checks:
                result = run_tau(args.tau_bin, individual_program(root, check))
                individual_runs.append({"name": check.name, **result})
        if args.mode in {"compare", "compound-only"}:
            compound_runs.append(run_tau(args.tau_bin, compound_program(root, checks)))

    individual_elapsed = [float(run["elapsed_ms"]) for run in individual_runs]
    compound_elapsed = [float(run["elapsed_ms"]) for run in compound_runs]
    individual_ok = all(bool(run["ok"]) for run in individual_runs)
    compound_ok = all(bool(run["ok"]) for run in compound_runs)
    individual_sum = sum(individual_elapsed)
    compound_sum = sum(compound_elapsed)
    improvement = None if args.mode != "compare" else (
        100.0 * (individual_sum - compound_sum) / individual_sum
        if individual_sum
        else 0.0
    )
    summary = {
        "scope": "safe table demo equivalence checks only",
        "ok": individual_ok and compound_ok,
        "mode": args.mode,
        "check_count": len(checks),
        "reps": args.reps,
        "individual": summarize_elapsed(individual_elapsed),
        "compound": summarize_elapsed(compound_elapsed),
        "elapsed_improvement_percent": (
            round(improvement, 3) if improvement is not None else None
        ),
        "individual_processes": len(individual_runs),
        "compound_processes": len(compound_runs),
        "individual_runs": individual_runs,
        "compound_runs": compound_runs,
        "law": "unsat(diff_1 or ... or diff_n) implies each diff_i is unsat",
        "boundary": (
            "The compound query proves the same table-vs-raw equivalence family "
            "for this corpus. It does not change Tau semantics and it does not "
            "include the bitvector smoke checks or the feature-flag rejection check."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
