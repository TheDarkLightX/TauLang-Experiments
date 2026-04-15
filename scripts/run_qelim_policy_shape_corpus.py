#!/usr/bin/env python3
"""Benchmark qelim on policy-shaped formulas from the table demo domain.

The non-pure BDD corpus proved that the patched auto route can be fast on
generated formulas. This harness asks a narrower question: do the same route
families appear on formulas that look like guarded-choice tables, priority
policies, incident-memory updates, and pointwise revision laws?
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Mode:
    name: str
    backend: str = ""
    kb: str = ""


MODES = [
    Mode("default"),
    Mode("auto", backend="auto"),
    Mode("auto_kb_guarded", backend="auto", kb="guarded"),
]


def atom(name: str) -> str:
    return f"({name} = 0)"


def neg(name: str) -> str:
    return f"!{atom(name)}"


def choice(guard: str, then_value: str, else_value: str) -> str:
    return f"(({atom(guard)} && {then_value}) || ({neg(guard)} && {else_value}))"


def dp_guard(guard: str, if_on: str, if_off: str) -> str:
    return f"(({atom(guard)} || {atom(if_on)}) && ({neg(guard)} || {atom(if_off)}))"


def qprefix(vars_: list[str]) -> str:
    return " ".join(f"ex {v}" for v in vars_)


def priority_table(rows: list[tuple[str, str]], default: str) -> str:
    expr = atom(default)
    for guard, value in reversed(rows):
        expr = choice(guard, atom(value), expr)
    return expr


def cases() -> list[dict[str, str]]:
    firewall = priority_table(
        [
            ("emergency", "freeze"),
            ("exploit", "quarantine"),
            ("oracle_alarm", "slow"),
            ("liquidity_alarm", "cap"),
        ],
        "allow",
    )
    collateral_reason = priority_table(
        [
            ("registry_fail", "reject_registry"),
            ("depth_fail", "reject_depth"),
            ("age_fail", "reject_age"),
            ("provenance_fail", "reject_provenance"),
        ],
        "admit",
    )
    incident_update = priority_table(
        [
            ("exploit_witness", "exploit_state"),
            ("oracle_witness", "oracle_state"),
            ("governance_patch", "patched_state"),
        ],
        "old_state",
    )
    revision = choice("revision_guard", atom("replacement"), atom("old_value"))
    two_cell_revision = (
        f"{choice('risk_region', atom('quarantine'), atom('old_risk'))} && "
        f"{choice('oracle_region', atom('freeze'), atom('old_oracle'))}"
    )
    dp_policy = (
        f"{dp_guard('witness', 'escalate', 'review')} && "
        f"{dp_guard('oracle_alarm', 'pause', 'allow')} && "
        f"{dp_guard('liquidity_alarm', 'cap', 'allow')}"
    )
    table_with_choice_child = choice(
        "incident_gate",
        choice("witness", atom("freeze"), atom("review")),
        choice("clear_gate", atom("allow"), atom("monitor")),
    )
    independent_priority_shards = (
        f"{priority_table([('emergency', 'freeze'), ('exploit', 'quarantine')], 'allow')} && "
        f"{priority_table([('oracle_alarm', 'slow'), ('liquidity_alarm', 'cap')], 'allow')}"
    )
    return [
        {
            "name": "firewall_priority_hidden_guards",
            "command": f"qelim {qprefix(['emergency', 'exploit', 'oracle_alarm', 'liquidity_alarm'])} {firewall}",
        },
        {
            "name": "collateral_reason_hidden_failures",
            "command": f"qelim {qprefix(['registry_fail', 'depth_fail', 'age_fail', 'provenance_fail'])} {collateral_reason}",
        },
        {
            "name": "incident_memory_hidden_witnesses",
            "command": f"qelim {qprefix(['exploit_witness', 'oracle_witness', 'governance_patch'])} {incident_update}",
        },
        {
            "name": "pointwise_revision_hidden_guard",
            "command": f"qelim {qprefix(['revision_guard'])} {revision}",
        },
        {
            "name": "two_cell_pointwise_revision",
            "command": f"qelim {qprefix(['risk_region', 'oracle_region'])} ({two_cell_revision})",
        },
        {
            "name": "dp_policy_hidden_guards",
            "command": f"qelim {qprefix(['witness', 'oracle_alarm', 'liquidity_alarm'])} ({dp_policy})",
        },
        {
            "name": "table_with_choice_child",
            "command": f"qelim {qprefix(['incident_gate', 'witness', 'clear_gate'])} {table_with_choice_child}",
        },
        {
            "name": "independent_priority_shards",
            "command": f"qelim {qprefix(['emergency', 'exploit', 'oracle_alarm', 'liquidity_alarm'])} ({independent_priority_shards})",
        },
    ]


def parse_prefixed_stats(text: str, prefix: str) -> dict[str, str]:
    line = ""
    for candidate in text.splitlines():
        if candidate.startswith(prefix):
            line = candidate
    return dict(STAT_RE.findall(line))


def strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        wraps = True
        for i, ch in enumerate(text):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(text) - 1:
                    wraps = False
                    break
        if not wraps:
            return text
        text = text[1:-1].strip()
    return text


def split_top(text: str, op: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth -= 1
            i += 1
            continue
        if depth == 0 and text.startswith(op, i):
            parts.append(text[start:i].strip())
            i += len(op)
            start = i
            continue
        i += 1
    if parts:
        parts.append(text[start:].strip())
    return parts


def canonical_formula(text: str) -> str:
    text = strip_outer_parens(text)
    for op in [" || ", " && "]:
        parts = split_top(text, op)
        if parts:
            canon = sorted(canonical_formula(part) for part in parts)
            return "(" + op.strip().join(canon) + ")"
    return text


def canonical_stdout(stdout: str) -> str:
    lines = []
    for line in stdout.strip().splitlines():
        if line.startswith("[") or "Experimental qelim BDD backend rejected" in line:
            continue
        if line.startswith("%1:"):
            lines.append("%1: " + canonical_formula(line.removeprefix("%1:").strip()))
        else:
            lines.append(line)
    return "\n".join(lines)


def as_float(d: dict[str, str], key: str) -> float:
    try:
        return float(d.get(key, "0"))
    except ValueError:
        return 0.0


def as_int(d: dict[str, str], key: str) -> int:
    try:
        return int(float(d.get(key, "0")))
    except ValueError:
        return 0


def run_tau(tau_bin: Path, command: str, mode: Mode) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_QELIM_STATS"] = "1"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if mode.backend:
        env["TAU_QELIM_BACKEND"] = mode.backend
    else:
        env.pop("TAU_QELIM_BACKEND", None)
    if mode.kb:
        env["TAU_QELIM_BDD_KB_REWRITE"] = mode.kb
    else:
        env.pop("TAU_QELIM_BDD_KB_REWRITE", None)

    argv = [
        str(tau_bin),
        "--charvar",
        "false",
        "-e",
        command,
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
    qelim_stats = parse_prefixed_stats(combined, "[qelim_cmd]")
    bdd_stats = parse_prefixed_stats(combined, "[qelim_bdd]")
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "normalized_stdout": canonical_stdout(proc.stdout),
        "stderr": proc.stderr.strip(),
        "elapsed_ms": round(elapsed_ms, 3),
        "qelim_stats": qelim_stats,
        "bdd_stats": bdd_stats,
        "qelim_total_ms": round(as_float(qelim_stats, "total_ms"), 6),
        "bdd_internal_ms": round(
            as_float(bdd_stats, "compile_ms")
            + as_float(bdd_stats, "project_ms")
            + as_float(bdd_stats, "rebuild_ms"),
            6,
        ),
    }


def summarize(values: list[dict[str, object]]) -> dict[str, object]:
    elapsed = [float(v["elapsed_ms"]) for v in values]
    qelim = [float(v["qelim_total_ms"]) for v in values]
    bdd = [float(v["bdd_internal_ms"]) for v in values]
    routes = Counter(
        str(v["bdd_stats"].get("route", "missing"))  # type: ignore[union-attr]
        for v in values
    )
    return {
        "runs": len(values),
        "returncodes": sorted({int(v["returncode"]) for v in values}),
        "elapsed_ms_sum": round(sum(elapsed), 3),
        "elapsed_ms_median": round(statistics.median(elapsed), 3) if elapsed else 0,
        "qelim_total_ms_sum": round(sum(qelim), 6),
        "qelim_total_ms_median": round(statistics.median(qelim), 6) if qelim else 0,
        "bdd_internal_ms_sum": round(sum(bdd), 6),
        "bdd_internal_ms_median": round(statistics.median(bdd), 6) if bdd else 0,
        "root_nodes_sum": sum(as_int(v["bdd_stats"], "root_nodes") for v in values),  # type: ignore[arg-type]
        "projected_nodes_sum": sum(as_int(v["bdd_stats"], "projected_nodes") for v in values),  # type: ignore[arg-type]
        "kb_steps_sum": sum(as_int(v["bdd_stats"], "kb_steps") for v in values),  # type: ignore[arg-type]
        "route_counts": dict(sorted(routes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-policy-shape-corpus.json"))
    parser.add_argument("--reps", type=int, default=10)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    per_mode: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
    ok = True
    for case in cases():
        case_runs: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
        for _ in range(args.reps):
            for mode in MODES:
                result = run_tau(args.tau_bin, case["command"], mode)
                case_runs[mode.name].append(result)
                per_mode[mode.name].append(result)

        default_stdout = case_runs["default"][0]["normalized_stdout"]
        default_returncode = case_runs["default"][0]["returncode"]
        parity = {
            mode.name: all(
                r["normalized_stdout"] == default_stdout and r["returncode"] == default_returncode
                for r in case_runs[mode.name]
            )
            for mode in MODES
        }
        ok = ok and default_returncode == 0 and all(parity.values())
        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "exact_default_parity": parity,
                "summary": {mode.name: summarize(case_runs[mode.name]) for mode in MODES},
            }
        )

    summary = {
        "scope": "patched Tau qelim policy-shaped corpus for safe table demo formulas",
        "ok": ok,
        "case_count": len(cases()),
        "reps": args.reps,
        "mode_summary": {mode.name: summarize(per_mode[mode.name]) for mode in MODES},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
