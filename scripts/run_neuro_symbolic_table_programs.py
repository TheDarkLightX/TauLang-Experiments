#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TAU_BIN = ROOT / "external" / "tau-lang" / "build-Release" / "tau"
DEFAULT_OUT = ROOT / "results" / "local" / "neuro-symbolic-table-programs.json"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "neuro-symbolic-table-programs.md"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


@dataclass(frozen=True)
class TauCheck:
    name: str
    source: str
    diff: str


def tau_source(path: Path) -> str:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def clean_lines(text: str) -> list[str]:
    cleaned = ANSI_RE.sub("", text)
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def run_tau_check(tau_bin: Path, check: TauCheck, *, timeout_s: float) -> dict[str, Any]:
    source_path = ROOT / check.source
    program = f"{tau_source(source_path)}\nsolve --tau ({check.diff})"
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [
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
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        lines = clean_lines(proc.stdout)
        last_line = lines[-1] if lines else ""
        return {
            "name": check.name,
            "source": check.source,
            "returncode": proc.returncode,
            "elapsed_ms": round(elapsed_ms, 3),
            "last_line": last_line,
            "ok": proc.returncode == 0 and last_line == "no solution",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": check.name,
            "source": check.source,
            "returncode": None,
            "elapsed_ms": round((time.perf_counter() - start) * 1000.0, 3),
            "last_line": "timeout",
            "ok": False,
            "timeout_s": timeout_s,
            "stdout": exc.stdout,
        }


def run_tau_group(tau_bin: Path, source: str, checks: list[TauCheck], *, timeout_s: float) -> dict[str, Any]:
    source_path = ROOT / source
    compound_diff = " || ".join(f"({check.diff})" for check in checks)
    program = f"{tau_source(source_path)}\nsolve --tau ({compound_diff})"
    env = os.environ.copy()
    env["TAU_ENABLE_SAFE_TABLES"] = "1"
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [
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
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_s,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        lines = clean_lines(proc.stdout)
        last_line = lines[-1] if lines else ""
        return {
            "source": source,
            "check_names": [check.name for check in checks],
            "returncode": proc.returncode,
            "elapsed_ms": round(elapsed_ms, 3),
            "last_line": last_line,
            "ok": proc.returncode == 0 and last_line == "no solution",
            "law": "unsat(diff_1 || ... || diff_n) implies every listed diff_i is unsat",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "source": source,
            "check_names": [check.name for check in checks],
            "returncode": None,
            "elapsed_ms": round((time.perf_counter() - start) * 1000.0, 3),
            "last_line": "timeout",
            "ok": False,
            "timeout_s": timeout_s,
            "stdout": exc.stdout,
        }


def run_tau_checks(tau_bin: Path, checks: list[TauCheck], *, timeout_s: float, mode: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if mode == "individual":
        rows = [run_tau_check(tau_bin, check, timeout_s=timeout_s) for check in checks]
        return rows, []

    grouped: dict[str, list[TauCheck]] = {}
    for check in checks:
        grouped.setdefault(check.source, []).append(check)
    group_rows = [
        run_tau_group(tau_bin, source, source_checks, timeout_s=timeout_s)
        for source, source_checks in grouped.items()
    ]
    by_source = {row["source"]: row for row in group_rows}
    rows: list[dict[str, Any]] = []
    for check in checks:
        group = by_source[check.source]
        rows.append(
            {
                "name": check.name,
                "source": check.source,
                "returncode": group["returncode"],
                "elapsed_ms": None,
                "group_elapsed_ms": group["elapsed_ms"],
                "last_line": group["last_line"],
                "ok": group["ok"],
                "mode": "grouped",
            }
        )
    return rows, group_rows


def tau_checks() -> list[TauCheck]:
    research = "examples/tau/neuro_symbolic_research_tables_v1.tau"
    defi = "examples/tau/defi_lending_risk_table_v1.tau"
    return [
        TauCheck(
            "counterexample_garden_table_agrees_with_raw",
            research,
            "counterexample_garden_table(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review) != "
            "counterexample_garden_raw(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review)",
        ),
        TauCheck(
            "counterexample_garden_counterexample_priority",
            research,
            "counterexample_garden_counterexample_slice_table(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review) != "
            "counterexample_garden_counterexample_slice_raw(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review)",
        ),
        TauCheck(
            "counterexample_garden_proof_slice",
            research,
            "counterexample_garden_proof_slice_table(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review) != "
            "counterexample_garden_proof_slice_raw(parse_bad,checked_counterexample,unsafe_pattern,proof_checked,needs_more_models,reject_parse,falsified,unsafe_boundary,promoted,search_more,review)",
        ),
        TauCheck(
            "frontier_weather_table_agrees_with_raw",
            research,
            "frontier_weather_table(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe) != "
            "frontier_weather_raw(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe)",
        ),
        TauCheck(
            "frontier_weather_exact_priority",
            research,
            "frontier_weather_exact_slice_table(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe) != "
            "frontier_weather_exact_slice_raw(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe)",
        ),
        TauCheck(
            "frontier_weather_expand_slice",
            research,
            "frontier_weather_expand_slice_table(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe) != "
            "frontier_weather_expand_slice_raw(exact_witness,high_yield,near_miss,stale_low_yield,high_cost,certify,expand,repair,prune,throttle,observe)",
        ),
        TauCheck(
            "proof_debt_ledger_table_agrees_with_raw",
            research,
            "proof_debt_ledger_table(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental) != "
            "proof_debt_ledger_raw(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental)",
        ),
        TauCheck(
            "proof_debt_ledger_falsified_priority",
            research,
            "proof_debt_ledger_falsified_slice_table(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental) != "
            "proof_debt_ledger_falsified_slice_raw(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental)",
        ),
        TauCheck(
            "proof_debt_ledger_verified_slice",
            research,
            "proof_debt_ledger_verified_slice_table(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental) != "
            "proof_debt_ledger_verified_slice_raw(counterexample_found,replay_ok,missing_lean,missing_runtime,boundary_open,falsified,lean_debt,runtime_debt,boundary_debt,verified,experimental)",
        ),
        TauCheck(
            "defi_lending_action_table_agrees_with_raw",
            defi,
            "defi_lending_action_table(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny) != "
            "defi_lending_action_raw(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny)",
        ),
        TauCheck(
            "defi_lending_exploit_priority",
            defi,
            "defi_lending_exploit_priority_slice_table(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny) != "
            "defi_lending_exploit_priority_slice_raw(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny)",
        ),
        TauCheck(
            "defi_lending_oracle_slice",
            defi,
            "defi_lending_oracle_slice_table(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny) != "
            "defi_lending_oracle_slice_raw(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny)",
        ),
        TauCheck(
            "defi_lending_allow_slice",
            defi,
            "defi_lending_allow_slice_table(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny) != "
            "defi_lending_allow_slice_raw(exploit_witness,oracle_divergence,solvency_gap,liquidation_cascade,governance_override,healthy,freeze_market,quarantine_oracle,pause_borrow,cap_liquidation,governance_review,allow,deny)",
        ),
    ]


def classify_counterexample(row: dict[str, Any]) -> str:
    if row["parse_bad"]:
        return "reject_parse"
    if row["checked_counterexample"]:
        return "falsified"
    if row["unsafe_pattern"]:
        return "unsafe_boundary"
    if row["proof_checked"]:
        return "promoted"
    if row["needs_more_models"]:
        return "search_more"
    return "review"


def classify_frontier(row: dict[str, Any]) -> str:
    if row["exact_witness"]:
        return "certify"
    if row["high_yield"] and not row["high_cost"]:
        return "expand"
    if row["near_miss"]:
        return "repair"
    if row["stale_low_yield"]:
        return "prune"
    if row["high_cost"]:
        return "throttle"
    return "observe"


def classify_proof_debt(row: dict[str, Any]) -> str:
    if row["counterexample_found"]:
        return "falsified"
    if row["replay_ok"] and row["missing_lean"]:
        return "lean_debt"
    if row["replay_ok"] and row["missing_runtime"]:
        return "runtime_debt"
    if row["replay_ok"] and row["boundary_open"]:
        return "boundary_debt"
    if row["replay_ok"]:
        return "verified"
    return "experimental"


def classify_defi(row: dict[str, Any]) -> str:
    if row["exploit_witness"]:
        return "freeze_market"
    if row["oracle_divergence"]:
        return "quarantine_oracle"
    if row["solvency_gap"]:
        return "pause_borrow"
    if row["liquidation_cascade"]:
        return "cap_liquidation"
    if row["governance_override"]:
        return "governance_review"
    if row["healthy"]:
        return "allow"
    return "deny"


def finite_fixtures() -> dict[str, dict[str, Any]]:
    counterexample_rows = [
        {
            "id": "law_current_guard_breaks_monotone",
            "parse_bad": False,
            "checked_counterexample": True,
            "unsafe_pattern": True,
            "proof_checked": False,
            "needs_more_models": False,
            "expected": "falsified",
        },
        {
            "id": "law_fixed_revision_monotone",
            "parse_bad": False,
            "checked_counterexample": False,
            "unsafe_pattern": False,
            "proof_checked": True,
            "needs_more_models": False,
            "expected": "promoted",
        },
        {
            "id": "law_arbitrary_select_unknown",
            "parse_bad": False,
            "checked_counterexample": False,
            "unsafe_pattern": True,
            "proof_checked": False,
            "needs_more_models": True,
            "expected": "unsafe_boundary",
        },
        {
            "id": "malformed_neural_claim",
            "parse_bad": True,
            "checked_counterexample": True,
            "unsafe_pattern": True,
            "proof_checked": True,
            "needs_more_models": True,
            "expected": "reject_parse",
        },
        {
            "id": "needs_finite_model_search",
            "parse_bad": False,
            "checked_counterexample": False,
            "unsafe_pattern": False,
            "proof_checked": False,
            "needs_more_models": True,
            "expected": "search_more",
        },
    ]
    frontier_rows = [
        {
            "id": "depth4_ln_exact",
            "exact_witness": True,
            "high_yield": True,
            "near_miss": False,
            "stale_low_yield": False,
            "high_cost": False,
            "expected": "certify",
        },
        {
            "id": "depth5_guided_region_a",
            "exact_witness": False,
            "high_yield": True,
            "near_miss": False,
            "stale_low_yield": False,
            "high_cost": False,
            "expected": "expand",
        },
        {
            "id": "exp_exp_near_miss_cluster",
            "exact_witness": False,
            "high_yield": False,
            "near_miss": True,
            "stale_low_yield": False,
            "high_cost": True,
            "expected": "repair",
        },
        {
            "id": "cold_random_depth5_shard",
            "exact_witness": False,
            "high_yield": False,
            "near_miss": False,
            "stale_low_yield": True,
            "high_cost": False,
            "expected": "prune",
        },
        {
            "id": "expensive_unpromising_proof_lane",
            "exact_witness": False,
            "high_yield": False,
            "near_miss": False,
            "stale_low_yield": False,
            "high_cost": True,
            "expected": "throttle",
        },
    ]
    proof_rows = [
        {
            "id": "safe_revision_packet",
            "counterexample_found": False,
            "replay_ok": True,
            "missing_lean": False,
            "missing_runtime": False,
            "boundary_open": False,
            "expected": "verified",
        },
        {
            "id": "frontier_weather_semantics",
            "counterexample_found": False,
            "replay_ok": True,
            "missing_lean": True,
            "missing_runtime": False,
            "boundary_open": False,
            "expected": "lean_debt",
        },
        {
            "id": "runtime_lowering_gap",
            "counterexample_found": False,
            "replay_ok": True,
            "missing_lean": False,
            "missing_runtime": True,
            "boundary_open": False,
            "expected": "runtime_debt",
        },
        {
            "id": "unrestricted_taba_claim",
            "counterexample_found": True,
            "replay_ok": True,
            "missing_lean": False,
            "missing_runtime": False,
            "boundary_open": False,
            "expected": "falsified",
        },
    ]
    defi_rows = [
        {
            "id": "oracle_and_exploit_overlap",
            "exploit_witness": True,
            "oracle_divergence": True,
            "solvency_gap": True,
            "liquidation_cascade": True,
            "governance_override": False,
            "healthy": True,
            "expected": "freeze_market",
        },
        {
            "id": "oracle_divergence_only",
            "exploit_witness": False,
            "oracle_divergence": True,
            "solvency_gap": False,
            "liquidation_cascade": False,
            "governance_override": False,
            "healthy": True,
            "expected": "quarantine_oracle",
        },
        {
            "id": "solvency_gap_with_healthy_flag",
            "exploit_witness": False,
            "oracle_divergence": False,
            "solvency_gap": True,
            "liquidation_cascade": False,
            "governance_override": False,
            "healthy": True,
            "expected": "pause_borrow",
        },
        {
            "id": "liquidation_cascade",
            "exploit_witness": False,
            "oracle_divergence": False,
            "solvency_gap": False,
            "liquidation_cascade": True,
            "governance_override": False,
            "healthy": False,
            "expected": "cap_liquidation",
        },
        {
            "id": "normal_market",
            "exploit_witness": False,
            "oracle_divergence": False,
            "solvency_gap": False,
            "liquidation_cascade": False,
            "governance_override": False,
            "healthy": True,
            "expected": "allow",
        },
    ]
    suites = {
        "counterexample_garden": {
            "classifier": classify_counterexample,
            "rows": counterexample_rows,
        },
        "frontier_weather": {
            "classifier": classify_frontier,
            "rows": frontier_rows,
        },
        "proof_debt_ledger": {
            "classifier": classify_proof_debt,
            "rows": proof_rows,
        },
        "defi_lending_risk": {
            "classifier": classify_defi,
            "rows": defi_rows,
        },
    }
    results: dict[str, dict[str, Any]] = {}
    for name, suite in suites.items():
        classifier = suite["classifier"]
        rows = []
        for row in suite["rows"]:
            actual = classifier(row)
            rows.append({**row, "actual": actual, "ok": actual == row["expected"]})
        results[name] = {
            "ok": all(row["ok"] for row in rows),
            "row_count": len(rows),
            "rows": rows,
        }
    return results


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Neuro-Symbolic Table Program Receipt",
        "",
        "This receipt runs deterministic proposal fixtures through safe table specifications and checks the Tau table/raw equivalence obligations.",
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
            "## Grouped Tau Obligations",
            "",
            "| Source | Checks | Result | Last line |",
            "| --- | ---: | --- | --- |",
        ]
    )
    group_rows = result.get("grouped_tau_checks", [])
    if group_rows:
        for row in group_rows:
            status = "pass" if row["ok"] else "fail"
            lines.append(f"| `{row['source']}` | {len(row['check_names'])} | {status} | `{row['last_line']}` |")
    else:
        lines.append("| `(individual mode)` | 0 | n/a | n/a |")
    lines.extend(
        [
            "",
            "## Tau Checks",
            "",
            "| Check | Source | Result | Last line |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in result["tau_checks"]:
        status = "pass" if row["ok"] else "fail"
        lines.append(f"| `{row['name']}` | `{row['source']}` | {status} | `{row['last_line']}` |")
    lines.extend(
        [
            "",
            "## Fixture Suites",
            "",
            "| Suite | Rows | Result |",
            "| --- | ---: | --- |",
        ]
    )
    for name, suite in result["fixture_suites"].items():
        status = "pass" if suite["ok"] else "fail"
        lines.append(f"| `{name}` | {suite['row_count']} | {status} |")
    lines.extend(
        [
            "",
            "## DeFi Examples",
            "",
            "| Scenario | Decision |",
            "| --- | --- |",
        ]
    )
    for row in result["fixture_suites"]["defi_lending_risk"]["rows"]:
        lines.append(f"| `{row['id']}` | `{row['actual']}` |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run neuro-symbolic safe table program examples.")
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-timeout-s", type=float, default=60.0)
    parser.add_argument(
        "--tau-mode",
        choices=["grouped", "individual"],
        default="individual",
        help=(
            "individual runs one Tau solve per obligation; grouped proves one "
            "compound unsat obligation per Tau source file."
        ),
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    checks, grouped_checks = run_tau_checks(
        args.tau_bin,
        tau_checks(),
        timeout_s=args.tau_timeout_s,
        mode=args.tau_mode,
    )
    fixture_suites = finite_fixtures()
    fixture_ok = all(suite["ok"] for suite in fixture_suites.values())
    tau_ok = all(check["ok"] for check in checks)
    result = {
        "schema": "neuro_symbolic_table_programs_v1",
        "scope": {
            "claim": "Safe table programs can classify neural proposal rows with symbolic priority and replayable Tau table/raw checks.",
            "not_claimed": [
                "not a live autonomous agent",
                "not unrestricted TABA tables",
                "not financial advice",
                "not proof that neural proposals are true",
            ],
        },
        "tau_checks": checks,
        "grouped_tau_checks": grouped_checks,
        "fixture_suites": fixture_suites,
        "summary": {
            "tau_check_count": len(checks),
            "tau_group_count": len(grouped_checks) if grouped_checks else len(checks),
            "tau_mode": args.tau_mode,
            "tau_checks_ok": tau_ok,
            "fixture_suite_count": len(fixture_suites),
            "fixture_rows": sum(suite["row_count"] for suite in fixture_suites.values()),
            "fixture_suites_ok": fixture_ok,
            "ok": tau_ok and fixture_ok,
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
