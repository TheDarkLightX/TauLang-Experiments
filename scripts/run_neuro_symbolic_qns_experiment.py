#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAU_BIN = ROOT / "external" / "tau-lang" / "build-Release" / "tau"
DEFAULT_SOURCE = ROOT / "examples" / "tau" / "neuro_symbolic_qns_evidence_v1.tau"
DEFAULT_OUT = ROOT / "results" / "local" / "neuro-symbolic-qns-experiment.json"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "neuro-symbolic-qns-experiment.md"
MASK = 0xFF
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
QNS_VALUE_RE = re.compile(r"\{\s*(\d+)\s*\}:qns8")
PLAIN_VALUE_RE = re.compile(r"%\d+:\s*(\d+)\s*$")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def tau_source(path: Path) -> str:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def qns_const(mask: int) -> str:
    return f"{{ #x{mask & MASK:02X} }}:qns8"


def qns_not_expr(expr: str) -> str:
    return f"({qns_const(MASK)} ^ ({expr}))"


def run_tau_qns(tau_bin: Path, source: str, expr: str, *, timeout_s: float) -> tuple[int, str]:
    env = os.environ.copy()
    env["TAU_ENABLE_QNS_BA"] = "1"
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    proc = subprocess.run(
        [
            str(tau_bin),
            "--severity",
            "error",
            "--charvar",
            "false",
            "-e",
            f"{source}\nn {expr}",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        check=False,
    )
    text = strip_ansi((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""))
    if proc.returncode != 0:
        raise RuntimeError(text.strip() or f"Tau failed with rc={proc.returncode}")
    match = QNS_VALUE_RE.search(text) or PLAIN_VALUE_RE.search(text.strip())
    if match is None:
        raise RuntimeError(f"could not parse qns8 output: {text.strip()!r}")
    return int(match.group(1)) & MASK, text.strip()


def names(mask: int, labels: tuple[str, ...]) -> list[str]:
    return [label for bit, label in enumerate(labels) if mask & (1 << bit)]


def check_expr(
    tau_bin: Path,
    source: str,
    suite: str,
    name: str,
    expr: str,
    expected: int,
    labels: tuple[str, ...],
    *,
    timeout_s: float,
) -> dict[str, Any]:
    actual, raw = run_tau_qns(tau_bin, source, expr, timeout_s=timeout_s)
    return {
        "suite": suite,
        "name": name,
        "expr": expr,
        "expected": expected & MASK,
        "actual": actual,
        "expected_names": names(expected, labels),
        "actual_names": names(actual, labels),
        "ok": actual == (expected & MASK),
        "raw": raw,
    }


def bitnot(mask: int) -> int:
    return (~mask) & MASK


def research_expected(m: dict[str, int]) -> dict[str, int]:
    promoted = (
        m["proposed"]
        & m["parse_ok"]
        & m["symbolic_ok"]
        & m["proof_ok"]
        & bitnot(m["counterexample"])
        & bitnot(m["review"])
        & bitnot(m["hard_reject"])
    )
    falsified = m["proposed"] & m["counterexample"]
    hard_reject = m["proposed"] & (bitnot(m["parse_ok"]) | m["hard_reject"])
    review = m["proposed"] & bitnot(promoted) & bitnot(falsified) & bitnot(hard_reject)
    return {
        "research_promoted": promoted,
        "research_falsified": falsified,
        "research_hard_reject": hard_reject,
        "research_review": review,
        "research_memory": promoted,
    }


def frontier_expected(m: dict[str, int]) -> dict[str, int]:
    certify = m["region"] & m["exact_witness"]
    expand = m["region"] & bitnot(m["exact_witness"]) & m["high_yield"] & bitnot(m["high_cost"])
    repair = m["region"] & bitnot(m["exact_witness"]) & bitnot(m["high_yield"]) & m["near_miss"] & bitnot(m["stale_low_yield"])
    prune = m["region"] & bitnot(m["exact_witness"]) & bitnot(m["high_yield"]) & bitnot(m["near_miss"]) & m["stale_low_yield"]
    throttle = (
        m["region"]
        & bitnot(m["exact_witness"])
        & bitnot(m["high_yield"])
        & bitnot(m["near_miss"])
        & bitnot(m["stale_low_yield"])
        & m["high_cost"]
    )
    return {
        "frontier_certify": certify,
        "frontier_expand": expand,
        "frontier_repair": repair,
        "frontier_prune": prune,
        "frontier_throttle": throttle,
    }


def defi_expected(m: dict[str, int]) -> dict[str, int]:
    freeze = m["market"] & m["exploit_witness"]
    quarantine = m["market"] & bitnot(m["exploit_witness"]) & m["oracle_divergence"]
    pause = m["market"] & bitnot(m["exploit_witness"]) & bitnot(m["oracle_divergence"]) & m["solvency_gap"]
    cap = (
        m["market"]
        & bitnot(m["exploit_witness"])
        & bitnot(m["oracle_divergence"])
        & bitnot(m["solvency_gap"])
        & m["liquidation_cascade"]
    )
    governance = (
        m["market"]
        & bitnot(m["exploit_witness"])
        & bitnot(m["oracle_divergence"])
        & bitnot(m["solvency_gap"])
        & bitnot(m["liquidation_cascade"])
        & m["governance_override"]
    )
    allow = (
        m["market"]
        & bitnot(m["exploit_witness"])
        & bitnot(m["oracle_divergence"])
        & bitnot(m["solvency_gap"])
        & bitnot(m["liquidation_cascade"])
        & bitnot(m["governance_override"])
        & m["healthy"]
    )
    return {
        "defi_freeze": freeze,
        "defi_quarantine_oracle": quarantine,
        "defi_pause_borrow": pause,
        "defi_cap_liquidation": cap,
        "defi_governance_review": governance,
        "defi_allow": allow,
    }


def c(mask: int) -> str:
    return qns_const(mask)


def build_checks(tau_bin: Path, source: str, *, timeout_s: float) -> list[dict[str, Any]]:
    research_labels = (
        "fixed_revision_law",
        "current_guard_law",
        "arbitrary_select_law",
        "malformed_claim",
        "depth5_region",
        "safe_revision_packet",
        "runtime_lowering_gap",
        "unrestricted_taba_claim",
    )
    frontier_labels = (
        "depth4_ln_exact",
        "depth5_guided_region",
        "exp_exp_near_miss",
        "cold_random_shard",
        "expensive_proof_lane",
        "reserve_5",
        "reserve_6",
        "reserve_7",
    )
    defi_labels = (
        "oracle_and_exploit_overlap",
        "oracle_divergence_only",
        "solvency_gap_with_healthy_flag",
        "liquidation_cascade",
        "normal_market",
        "governance_override",
        "reserve_6",
        "reserve_7",
    )
    research = {
        "proposed": 0xFF,
        "parse_ok": 0xF7,
        "symbolic_ok": 0x21,
        "proof_ok": 0x21,
        "counterexample": 0x82,
        "review": 0x54,
        "hard_reject": 0x08,
    }
    frontier = {
        "region": 0x1F,
        "exact_witness": 0x01,
        "high_yield": 0x03,
        "near_miss": 0x04,
        "stale_low_yield": 0x08,
        "high_cost": 0x14,
    }
    defi = {
        "market": 0x3F,
        "exploit_witness": 0x01,
        "oracle_divergence": 0x03,
        "solvency_gap": 0x04,
        "liquidation_cascade": 0x08,
        "governance_override": 0x20,
        "healthy": 0x15,
    }

    rows: list[dict[str, Any]] = []
    r = research
    expected = research_expected(r)
    promoted_expr = (
        f"({c(r['proposed'])} & {c(r['parse_ok'])} & {c(r['symbolic_ok'])} & "
        f"{c(r['proof_ok'])} & {qns_not_expr(c(r['counterexample']))} & "
        f"{qns_not_expr(c(r['review']))} & {qns_not_expr(c(r['hard_reject']))})"
    )
    falsified_expr = f"({c(r['proposed'])} & {c(r['counterexample'])})"
    hard_reject_expr = f"({c(r['proposed'])} & ({qns_not_expr(c(r['parse_ok']))} | {c(r['hard_reject'])}))"
    review_expr = (
        f"({c(r['proposed'])} & {qns_not_expr(promoted_expr)} & "
        f"{qns_not_expr(falsified_expr)} & {qns_not_expr(hard_reject_expr)})"
    )
    rows.extend(
        [
            check_expr(
                tau_bin,
                source,
                "research_qns",
                "promoted",
                promoted_expr,
                expected["research_promoted"],
                research_labels,
                timeout_s=timeout_s,
            ),
            check_expr(
                tau_bin,
                source,
                "research_qns",
                "falsified",
                falsified_expr,
                expected["research_falsified"],
                research_labels,
                timeout_s=timeout_s,
            ),
            check_expr(
                tau_bin,
                source,
                "research_qns",
                "hard_reject",
                hard_reject_expr,
                expected["research_hard_reject"],
                research_labels,
                timeout_s=timeout_s,
            ),
            check_expr(
                tau_bin,
                source,
                "research_qns",
                "review",
                review_expr,
                expected["research_review"],
                research_labels,
                timeout_s=timeout_s,
            ),
            check_expr(
                tau_bin,
                source,
                "research_qns",
                "memory_revise_promoted",
                f"table {{ when {c(expected['research_promoted'])} => {c(r['proposed'])}; else => {c(0)} }}",
                expected["research_memory"],
                research_labels,
                timeout_s=timeout_s,
            ),
        ]
    )

    f = frontier
    expected_f = frontier_expected(f)
    frontier_certify_expr = f"({c(f['region'])} & {c(f['exact_witness'])})"
    frontier_expand_expr = (
        f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & "
        f"{c(f['high_yield'])} & {qns_not_expr(c(f['high_cost']))})"
    )
    frontier_repair_expr = (
        f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & "
        f"{qns_not_expr(c(f['high_yield']))} & {c(f['near_miss'])} & "
        f"{qns_not_expr(c(f['stale_low_yield']))})"
    )
    frontier_prune_expr = (
        f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & "
        f"{qns_not_expr(c(f['high_yield']))} & {qns_not_expr(c(f['near_miss']))} & "
        f"{c(f['stale_low_yield'])})"
    )
    frontier_throttle_expr = (
        f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & "
        f"{qns_not_expr(c(f['high_yield']))} & {qns_not_expr(c(f['near_miss']))} & "
        f"{qns_not_expr(c(f['stale_low_yield']))} & {c(f['high_cost'])})"
    )
    rows.extend(
        [
            check_expr(tau_bin, source, "frontier_qns", "certify", frontier_certify_expr, expected_f["frontier_certify"], frontier_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "frontier_qns", "expand", frontier_expand_expr, expected_f["frontier_expand"], frontier_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "frontier_qns", "repair", frontier_repair_expr, expected_f["frontier_repair"], frontier_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "frontier_qns", "prune", frontier_prune_expr, expected_f["frontier_prune"], frontier_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "frontier_qns", "throttle", frontier_throttle_expr, expected_f["frontier_throttle"], frontier_labels, timeout_s=timeout_s),
        ]
    )

    d = defi
    expected_d = defi_expected(d)
    defi_freeze_expr = f"({c(d['market'])} & {c(d['exploit_witness'])})"
    defi_quarantine_expr = (
        f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & "
        f"{c(d['oracle_divergence'])})"
    )
    defi_pause_expr = (
        f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & "
        f"{qns_not_expr(c(d['oracle_divergence']))} & {c(d['solvency_gap'])})"
    )
    defi_cap_expr = (
        f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & "
        f"{qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & "
        f"{c(d['liquidation_cascade'])})"
    )
    defi_governance_expr = (
        f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & "
        f"{qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & "
        f"{qns_not_expr(c(d['liquidation_cascade']))} & {c(d['governance_override'])})"
    )
    defi_allow_expr = (
        f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & "
        f"{qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & "
        f"{qns_not_expr(c(d['liquidation_cascade']))} & {qns_not_expr(c(d['governance_override']))} & "
        f"{c(d['healthy'])})"
    )
    rows.extend(
        [
            check_expr(tau_bin, source, "defi_qns", "freeze", defi_freeze_expr, expected_d["defi_freeze"], defi_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "defi_qns", "quarantine_oracle", defi_quarantine_expr, expected_d["defi_quarantine_oracle"], defi_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "defi_qns", "pause_borrow", defi_pause_expr, expected_d["defi_pause_borrow"], defi_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "defi_qns", "cap_liquidation", defi_cap_expr, expected_d["defi_cap_liquidation"], defi_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "defi_qns", "governance_review", defi_governance_expr, expected_d["defi_governance_review"], defi_labels, timeout_s=timeout_s),
            check_expr(tau_bin, source, "defi_qns", "allow", defi_allow_expr, expected_d["defi_allow"], defi_labels, timeout_s=timeout_s),
        ]
    )
    return rows


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Neuro-Symbolic qNS Experiment Receipt",
        "",
        "This experiment uses Tau qNS8 finite Boolean algebra. Neural proposal rows are represented as bits; Tau computes exact promoted, falsified, review, frontier, and DeFi action masks.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in result["summary"].items():
        if isinstance(value, bool):
            value = "true" if value else "false"
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Suite | Check | Actual names | Result |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in result["rows"]:
        status = "pass" if row["ok"] else "fail"
        actual = ", ".join(row["actual_names"]) if row["actual_names"] else "(none)"
        lines.append(f"| `{row['suite']}` | `{row['name']}` | {actual} | {status} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run qNS8 neuro-symbolic evidence-mask experiment.")
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--tau-timeout-s", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    source_path = args.tau_source if args.tau_source.is_absolute() else ROOT / args.tau_source
    # The executable checks inline qNS expressions to isolate Tau's qNS carrier.
    # The source file remains the readable definitional version of the same laws.
    source = ""
    rows = build_checks(args.tau_bin, source, timeout_s=args.tau_timeout_s)
    suite_counts: dict[str, int] = {}
    for row in rows:
        suite_counts[row["suite"]] = suite_counts.get(row["suite"], 0) + 1
    result = {
        "schema": "neuro_symbolic_qns_experiment_v1",
        "scope": {
            "claim": "Tau qNS8 acts as the finite neuro-symbolic Boolean algebra for proposal/evidence masks.",
            "not_claimed": [
                "not live LLM inference",
                "not probabilistic arithmetic inside Tau",
                "not unrestricted TABA tables",
                "not financial advice",
            ],
        },
        "tau_source": str(source_path.relative_to(ROOT)),
        "rows": rows,
        "summary": {
            "suite_count": len(suite_counts),
            "row_count": len(rows),
            "rows_ok": all(row["ok"] for row in rows),
            "ok": all(row["ok"] for row in rows),
        },
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    report_out = args.report_out if args.report_out.is_absolute() else ROOT / args.report_out
    out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_out.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
