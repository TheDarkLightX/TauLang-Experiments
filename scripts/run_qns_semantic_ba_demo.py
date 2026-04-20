#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MASK = 0xFF
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
QNS_VALUE_RE = re.compile(r"\{\s*(\d+)\s*\}:qns(?:8|64)")
PLAIN_VALUE_RE = re.compile(r"%\d+:\s*(\d+)\s*$")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def qns_const(mask: int) -> str:
    return f"{{ #x{mask & MASK:02X} }}:qns8"


def qns64_const(mask: int) -> str:
    return f"{{ #x{mask & ((1 << 64) - 1):016X} }}:qns64"


def qns_not(expr: str) -> str:
    return f"({qns_const(MASK)} ^ ({expr}))"


def run_tau_qns_normalize(tau_bin: Path, expr: str, *, timeout_s: float) -> tuple[int, str]:
    env = dict(os.environ)
    env["TAU_ENABLE_QNS_BA"] = "1"
    proc = subprocess.run(
        [
            str(tau_bin),
            "--severity",
            "error",
            "--charvar",
            "false",
            "-e",
            f"n {expr}",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        env=env,
        cwd=str(ROOT),
    )
    text = strip_ansi((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""))
    if proc.returncode != 0:
        raise RuntimeError(text.strip() or f"tau normalize failed with rc={proc.returncode}")
    match = QNS_VALUE_RE.search(text) or PLAIN_VALUE_RE.search(text.strip())
    if not match:
        raise RuntimeError(f"could not parse qns result from Tau output: {text.strip()!r}")
    return int(match.group(1)), text.strip()


def check_qns_rejected_without_flag(tau_bin: Path, *, timeout_s: float) -> dict[str, Any]:
    env = dict(os.environ)
    env.pop("TAU_ENABLE_QNS_BA", None)
    proc = subprocess.run(
        [
            str(tau_bin),
            "--severity",
            "error",
            "--charvar",
            "false",
            "-e",
            f"n {qns_const(1)}",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        env=env,
        cwd=str(ROOT),
    )
    text = strip_ansi((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else ""))
    parsed_value = QNS_VALUE_RE.search(text) or PLAIN_VALUE_RE.search(text.strip())
    rejected = (
        parsed_value is None
        and (
            "qns8 constants require TAU_ENABLE_QNS_BA=1" in text
            or "Parsing constant" in text
            or "Incompatible or absent type information" in text
        )
    )
    return {
        "name": "qns8_rejected_without_feature_flag",
        "ok": rejected,
        "returncode": proc.returncode,
        "raw": text.strip(),
    }


@dataclass(frozen=True)
class Atom:
    bit: int
    name: str

    @property
    def mask(self) -> int:
        return 1 << self.bit


CANDIDATES = (
    Atom(0, "approve_low_risk_loan"),
    Atom(1, "manual_review_high_amount"),
    Atom(2, "reject_sanctioned_wallet"),
    Atom(3, "quarantine_oracle_anomaly"),
    Atom(4, "reward_contributor"),
    Atom(5, "tax_extractor"),
    Atom(6, "freeze_governance_compromise"),
    Atom(7, "escalate_human_council"),
)

CONCEPTS = (
    Atom(0, "registry_verified"),
    Atom(1, "liquidity_deep"),
    Atom(2, "token_old_enough"),
    Atom(3, "provenance_clean"),
    Atom(4, "governance_separated"),
    Atom(5, "oracle_stable"),
    Atom(6, "sanction_risk"),
    Atom(7, "human_review_required"),
)

TRACE_CLASSES = (
    Atom(0, "login_then_trade"),
    Atom(1, "trade_without_login"),
    Atom(2, "oracle_update_then_trade"),
    Atom(3, "trade_before_oracle_update"),
    Atom(4, "patch_then_admit_collateral"),
    Atom(5, "admit_before_patch"),
    Atom(6, "liquidation_after_price_drop"),
    Atom(7, "liquidation_before_price_drop"),
)


def mask_from_flags(atoms: tuple[Atom, ...], flags: tuple[bool, ...]) -> int:
    out = 0
    for atom, flag in zip(atoms, flags, strict=True):
        if flag:
            out |= atom.mask
    return out & MASK


def names_for_mask(atoms: tuple[Atom, ...], mask: int) -> list[str]:
    return [atom.name for atom in atoms if mask & atom.mask]


def normalize_scores(scores: tuple[float, ...]) -> tuple[float, ...]:
    total = sum(scores)
    if total <= 0:
        raise ValueError("neural scores must have positive mass")
    return tuple(score / total for score in scores)


def proposed_mask(scores: tuple[float, ...], threshold: float) -> int:
    out = 0
    for atom, score in zip(CANDIDATES, scores, strict=True):
        if score >= threshold:
            out |= atom.mask
    return out & MASK


def qns_distribution(scores: tuple[float, ...], survivor_mask: int) -> dict[str, float]:
    qn = normalize_scores(scores)
    mass = sum(score for atom, score in zip(CANDIDATES, qn, strict=True) if survivor_mask & atom.mask)
    if mass == 0:
        return {}
    return {
        atom.name: round(score / mass, 6)
        for atom, score in zip(CANDIDATES, qn, strict=True)
        if survivor_mask & atom.mask
    }


def candidate_exprs(step: dict[str, int]) -> dict[str, str]:
    universe = qns_const(step["universe"])
    proposed = qns_const(step["proposed"])
    allowed = qns_const(step["allowed"])
    review = qns_const(step["review"])
    hard = qns_const(step["hard"])
    proposed_expr = f"(({universe}) & ({proposed}))"
    eligible = f"(({proposed_expr}) & ({allowed}) & ({qns_not(hard)}))"
    auto_accept = f"(({eligible}) & ({qns_not(review)}))"
    human_review = f"(({eligible}) & ({review}))"
    symbolic_reject = f"(({proposed_expr}) & (({qns_not(allowed)}) | ({hard})))"
    return {
        "eligible": eligible,
        "auto_accept": auto_accept,
        "human_review": human_review,
        "symbolic_reject": symbolic_reject,
        "partition": f"(({auto_accept}) | ({human_review}) | ({symbolic_reject}))",
        "unsafe_leak": f"(({auto_accept}) & ({hard}))",
    }


def concept_exprs(step: dict[str, int]) -> dict[str, str]:
    observed = qns_const(step["observed"])
    required = qns_const(step["required"])
    risk = qns_const(step["risk"])
    review = qns_const(step["review"])
    return {
        "present_required": f"(({observed}) & ({required}))",
        "missing_required": f"(({required}) & ({qns_not(observed)}))",
        "risk_hits": f"(({observed}) & ({risk}))",
        "review_hits": f"(({observed}) & ({review}))",
        "safe_atoms": f"(({observed}) & ({qns_not(risk)}))",
    }


def trace_exprs(step: dict[str, int]) -> dict[str, str]:
    observed = qns_const(step["observed"])
    safe = qns_const(step["safe"])
    forbidden = qns_const(step["forbidden"])
    classified = f"(({safe}) | ({forbidden}))"
    return {
        "safe_observed": f"(({observed}) & ({safe}))",
        "forbidden_hits": f"(({observed}) & ({forbidden}))",
        "unclassified": f"(({observed}) & ({qns_not(classified)}))",
        "accepted_trace": f"(({observed}) & ({safe}) & ({qns_not(forbidden)}))",
    }


def expected_candidate(step: dict[str, int]) -> dict[str, int]:
    universe = step["universe"] & MASK
    proposed = step["proposed"] & MASK
    allowed = step["allowed"] & MASK
    review = step["review"] & MASK
    hard = step["hard"] & MASK
    eligible = universe & proposed & allowed & ((~hard) & MASK)
    auto_accept = eligible & ((~review) & MASK)
    human_review = eligible & review
    symbolic_reject = universe & proposed & (((~allowed) & MASK) | hard)
    return {
        "eligible": eligible,
        "auto_accept": auto_accept,
        "human_review": human_review,
        "symbolic_reject": symbolic_reject,
        "partition": auto_accept | human_review | symbolic_reject,
        "unsafe_leak": auto_accept & hard,
    }


def expected_concept(step: dict[str, int]) -> dict[str, int]:
    observed = step["observed"] & MASK
    required = step["required"] & MASK
    risk = step["risk"] & MASK
    review = step["review"] & MASK
    return {
        "present_required": observed & required,
        "missing_required": required & ((~observed) & MASK),
        "risk_hits": observed & risk,
        "review_hits": observed & review,
        "safe_atoms": observed & ((~risk) & MASK),
    }


def expected_trace(step: dict[str, int]) -> dict[str, int]:
    observed = step["observed"] & MASK
    safe = step["safe"] & MASK
    forbidden = step["forbidden"] & MASK
    classified = safe | forbidden
    return {
        "safe_observed": observed & safe,
        "forbidden_hits": observed & forbidden,
        "unclassified": observed & ((~classified) & MASK),
        "accepted_trace": observed & safe & ((~forbidden) & MASK),
    }


def eval_exprs(tau_bin: Path, exprs: dict[str, str], *, timeout_s: float) -> tuple[dict[str, int], list[dict[str, Any]]]:
    actual: dict[str, int] = {}
    checks: list[dict[str, Any]] = []
    for name, expr in exprs.items():
        value, raw = run_tau_qns_normalize(tau_bin, expr, timeout_s=timeout_s)
        actual[name] = value
        checks.append({"output": name, "expr": expr, "value": value, "raw": raw})
    return actual, checks


def public_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run qns8/qns64 neuro-symbolic BA demos.")
    parser.add_argument("--tau-bin", type=Path, default=ROOT / "external" / "tau-lang" / "build-Release" / "tau")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "local" / "qns-semantic-ba-demo.json")
    parser.add_argument("--timeout-s", type=float, default=10.0)
    args = parser.parse_args()

    candidate_scenarios = [
        {
            "name": "post_agi_tokenomics",
            "scores": (0.05, 0.08, 0.03, 0.07, 0.30, 0.34, 0.04, 0.09),
            "allowed": (True, True, True, True, True, False, True, True),
            "review": (False, True, False, True, False, False, True, True),
            "hard": (False, False, False, False, False, True, False, False),
        },
        {
            "name": "collateral_admission",
            "scores": (0.19, 0.26, 0.20, 0.08, 0.05, 0.02, 0.07, 0.13),
            "allowed": (False, True, True, True, False, False, True, True),
            "review": (False, True, False, True, False, False, True, True),
            "hard": (True, False, False, False, False, True, False, False),
        },
    ]
    concept_scenarios = [
        {
            "name": "clean_collateral_report",
            "observed": (True, True, True, True, True, True, False, False),
            "required": (True, True, True, True, True, True, False, False),
            "risk": (False, False, False, False, False, False, True, False),
            "review": (False, False, False, False, False, False, False, True),
        },
        {
            "name": "carbonvote_like_report",
            "observed": (True, False, False, False, False, True, False, True),
            "required": (True, True, True, True, True, True, False, False),
            "risk": (False, False, False, True, True, False, True, False),
            "review": (False, False, False, False, False, False, False, True),
        },
    ]
    trace_scenarios = [
        {
            "name": "ordinary_trade_session",
            "observed": (True, False, True, False, False, False, False, False),
            "safe": (True, False, True, False, True, False, True, False),
            "forbidden": (False, True, False, True, False, True, False, True),
        },
        {
            "name": "collateral_admission_race",
            "observed": (False, False, False, False, False, True, False, False),
            "safe": (True, False, True, False, True, False, True, False),
            "forbidden": (False, True, False, True, False, True, False, True),
        },
    ]

    smoke_cases = [
        ("meet", f"({qns_const(0x03)} & {qns_const(0x05)})", 0x01),
        ("join", f"({qns_const(0x03)} | {qns_const(0x05)})", 0x07),
        ("prime_as_xor_top", f"({qns_const(MASK)} ^ {qns_const(0xF0)})", 0x0F),
        (
            "qns64_high_bit_join",
            f"(({qns64_const(0x03)} & {qns64_const(0x05)}) | {qns64_const(1 << 63)})",
            (1 << 63) | 1,
        ),
        (
            "qns64_prime_as_xor_top",
            f"({qns64_const((1 << 64) - 1)} ^ {qns64_const(0xFFFFFFFFFFFFFFF0)})",
            0x0F,
        ),
    ]
    smoke_rows = []
    mismatches: list[dict[str, Any]] = []
    feature_flag_check = check_qns_rejected_without_flag(
        args.tau_bin, timeout_s=args.timeout_s
    )
    if not feature_flag_check["ok"]:
        mismatches.append(feature_flag_check)
    for name, expr, expected in smoke_cases:
        actual, raw = run_tau_qns_normalize(args.tau_bin, expr, timeout_s=args.timeout_s)
        row = {"name": name, "expected": expected, "actual": actual, "ok": actual == expected, "raw": raw}
        smoke_rows.append(row)
        if actual != expected:
            mismatches.append(row)

    candidate_rows = []
    concept_rows = []
    trace_rows = []
    tau_checks: list[dict[str, Any]] = []

    for scenario in candidate_scenarios:
        step = {
            "universe": MASK,
            "proposed": proposed_mask(scenario["scores"], 0.08),
            "allowed": mask_from_flags(CANDIDATES, scenario["allowed"]),
            "review": mask_from_flags(CANDIDATES, scenario["review"]),
            "hard": mask_from_flags(CANDIDATES, scenario["hard"]),
        }
        actual, checks = eval_exprs(args.tau_bin, candidate_exprs(step), timeout_s=args.timeout_s)
        expected = expected_candidate(step)
        tau_checks.extend({"scenario": scenario["name"], **check} for check in checks)
        row = {
            "scenario": scenario["name"],
            "input_masks": step,
            "expected": expected,
            "actual": actual,
            "ok": actual == expected,
            "sets": {name: names_for_mask(CANDIDATES, mask) for name, mask in actual.items()},
            "qNS": qns_distribution(scenario["scores"], actual["eligible"]),
        }
        candidate_rows.append(row)
        if not row["ok"]:
            mismatches.append(row)

    for scenario in concept_scenarios:
        step = {
            "observed": mask_from_flags(CONCEPTS, scenario["observed"]),
            "required": mask_from_flags(CONCEPTS, scenario["required"]),
            "risk": mask_from_flags(CONCEPTS, scenario["risk"]),
            "review": mask_from_flags(CONCEPTS, scenario["review"]),
        }
        actual, checks = eval_exprs(args.tau_bin, concept_exprs(step), timeout_s=args.timeout_s)
        expected = expected_concept(step)
        tau_checks.extend({"scenario": scenario["name"], **check} for check in checks)
        row = {
            "scenario": scenario["name"],
            "input_masks": step,
            "expected": expected,
            "actual": actual,
            "ok": actual == expected,
            "sets": {name: names_for_mask(CONCEPTS, mask) for name, mask in actual.items()},
        }
        concept_rows.append(row)
        if not row["ok"]:
            mismatches.append(row)

    for scenario in trace_scenarios:
        step = {
            "observed": mask_from_flags(TRACE_CLASSES, scenario["observed"]),
            "safe": mask_from_flags(TRACE_CLASSES, scenario["safe"]),
            "forbidden": mask_from_flags(TRACE_CLASSES, scenario["forbidden"]),
        }
        actual, checks = eval_exprs(args.tau_bin, trace_exprs(step), timeout_s=args.timeout_s)
        expected = expected_trace(step)
        tau_checks.extend({"scenario": scenario["name"], **check} for check in checks)
        row = {
            "scenario": scenario["name"],
            "input_masks": step,
            "expected": expected,
            "actual": actual,
            "ok": actual == expected,
            "sets": {name: names_for_mask(TRACE_CLASSES, mask) for name, mask in actual.items()},
        }
        trace_rows.append(row)
        if not row["ok"]:
            mismatches.append(row)

    result = {
        "ok": not mismatches,
        "mismatch_count": len(mismatches),
        "scope": "finite qns8/qns64 powerset BAs over audited atoms",
        "tau_bin": public_path(args.tau_bin),
        "feature_flag_check": feature_flag_check,
        "smoke_checks": smoke_rows,
        "candidate_rows": candidate_rows,
        "concept_rows": concept_rows,
        "trace_rows": trace_rows,
        "tau_checks": tau_checks,
        "mismatches": mismatches,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"ok": result["ok"], "mismatch_count": len(mismatches)}, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
