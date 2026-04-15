#!/usr/bin/env python3
"""Check whether the public table demos exercise Tau's qelim telemetry path.

This is a boundary test for the qelim optimization work. The policy-shaped
qelim corpus is demo-adjacent, but the actual table demos use `solve --tau`.
This script runs representative table-demo solver checks with qelim telemetry
enabled and counts whether `[qelim_cmd]` or `[qelim_bdd]` lines appear.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Mode:
    name: str
    backend: str = ""


MODES = [
    Mode("default"),
    Mode("auto", backend="auto"),
]


def tau_source(path: Path) -> str:
    lines = []
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


def run_tau(tau_bin: Path, program: str, mode: Mode) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    env["TAU_QELIM_STATS"] = "1"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if mode.backend:
        env["TAU_QELIM_BACKEND"] = mode.backend
    else:
        env.pop("TAU_QELIM_BACKEND", None)
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
    qelim_rows = parse_prefixed_stats(combined, "[qelim_cmd]")
    bdd_rows = parse_prefixed_stats(combined, "[qelim_bdd]")
    clean_lines = [
        line.strip()
        for line in combined.splitlines()
        if not line.startswith("[qelim_cmd]") and not line.startswith("[qelim_bdd]")
        and line.strip()
    ]
    last_line = clean_lines[-1] if clean_lines else ""
    return {
        "returncode": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 3),
        "last_line": last_line,
        "qelim_stat_count": len(qelim_rows),
        "bdd_stat_count": len(bdd_rows),
        "qelim_rows": qelim_rows,
        "bdd_rows": bdd_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/table-demo-qelim-telemetry.json"))
    args = parser.parse_args()
    root = Path.cwd()
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    total_qelim_stats = 0
    ok = True
    for case in cases(root):
        runs = {}
        for mode in MODES:
            result = run_tau(args.tau_bin, case["program"], mode)
            runs[mode.name] = result
            total_qelim_stats += int(result["qelim_stat_count"])
            ok = ok and result["returncode"] == 0 and result["last_line"] == "no solution"
        rows.append({"name": case["name"], "runs": runs})

    summary = {
        "scope": "table-demo solver checks with qelim telemetry enabled",
        "ok": ok,
        "case_count": len(rows),
        "modes": [mode.name for mode in MODES],
        "total_runs": len(rows) * len(MODES),
        "total_qelim_stat_count": total_qelim_stats,
        "rows": rows,
        "boundary": (
            "No qelim telemetry means these solve --tau checks do not exercise "
            "the qelim command backend measured by the qelim corpora."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
