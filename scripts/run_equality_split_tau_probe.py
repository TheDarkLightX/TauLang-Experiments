#!/usr/bin/env python3
"""Probe Tau's current equality-split recombination boundary.

This script does not patch Tau. It asks the current Tau binary to normalize
formulas where a split on an equality leaves branches that can be recombined
after path simplification. Each proposed shorter target is checked by Tau's
solver:

    solve --tau !(original <-> target)

The expected answer is `no solution`.
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


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class Probe:
    name: str
    original: str
    target: str


def probes() -> list[Probe]:
    return [
        Probe(
            name="equality_split_leq_absorption",
            original=(
                "((x = y:sbf && ((x & y') = 0)) || "
                "(x != y:sbf && ((x & y') = 0)))"
            ),
            target="((x & y') = 0)",
        ),
        Probe(
            name="equality_split_nonzero_absorption",
            original=(
                "((x = y:sbf && (((x & y) | (x' & y)) != 0)) || "
                "(x != y:sbf && (((x & y) | (x' & y)) != 0)))"
            ),
            target="(y != 0)",
        ),
        Probe(
            name="equality_split_zero_absorption",
            original=(
                "((x = y:sbf && (((x & y) | (x' & y)) = 0)) || "
                "(x != y:sbf && (((x & y) | (x' & y)) = 0)))"
            ),
            target="(y = 0)",
        ),
        Probe(
            name="three_alias_nonzero_absorption",
            original=(
                "((x = y:sbf && y = z:sbf && "
                "((((x & y) | (y & z)) | (x' & z)) != 0)) || "
                "(!(x = y:sbf && y = z:sbf) && "
                "((((x & y) | (y & z)) | (x' & z)) != 0)))"
            ),
            target="((((x & y) | (y & z)) | (x' & z)) != 0)",
        ),
    ]


def extended_probes() -> list[Probe]:
    base = probes()
    aliases = [
        ("xy_yz", "x = y:sbf && y = z:sbf"),
        ("yx_zy", "y = x:sbf && z = y:sbf"),
        ("zy_xy", "z = y:sbf && x = y:sbf"),
        ("xz_zy", "x = z:sbf && z = y:sbf"),
    ]
    residual = "((((x & y) | (y & z)) | (x' & z)) != 0)"
    for name, guard in aliases:
        base.append(
            Probe(
                name=f"three_alias_permutation_{name}",
                original=f"(({guard} && {residual}) || (!({guard}) && {residual}))",
                target=residual,
            )
        )
    return base


def clean(text: str) -> str:
    return ANSI_RE.sub("", text).strip()


def tau_cmd(tau_bin: Path, command: str) -> dict[str, object]:
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
    proc = subprocess.run(argv, text=True, capture_output=True, check=False)
    elapsed_ms = (time.perf_counter() - start) * 1000
    output = clean(proc.stdout + proc.stderr)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return {
        "returncode": proc.returncode,
        "elapsed_ms": round(elapsed_ms, 3),
        "output": output,
        "last_line": lines[-1] if lines else "",
    }


def normalize_with(tau_bin: Path, command: str, formula: str) -> dict[str, object]:
    result = tau_cmd(tau_bin, f"{command} {formula}")
    normalized = str(result["last_line"])
    if normalized.startswith("%1:"):
        normalized = normalized[3:].strip()
    return {**result, "normalized": normalized}


def normalize(tau_bin: Path, formula: str) -> dict[str, object]:
    return normalize_with(tau_bin, "normalize", formula)


def solve_equiv(tau_bin: Path, original: str, target: str) -> dict[str, object]:
    return tau_cmd(tau_bin, f"solve --tau !({original} <-> {target})")


def analyze(tau_bin: Path, probe: Probe) -> dict[str, object]:
    original_norm = normalize(tau_bin, probe.original)
    target_norm = normalize(tau_bin, probe.target)
    original_dnf = normalize_with(tau_bin, "dnf", probe.original)
    target_dnf = normalize_with(tau_bin, "dnf", probe.target)
    original_mnf = normalize_with(tau_bin, "mnf", probe.original)
    target_mnf = normalize_with(tau_bin, "mnf", probe.target)
    equiv = solve_equiv(tau_bin, probe.original, probe.target)
    original_text = str(original_norm["normalized"])
    target_text = str(target_norm["normalized"])
    dnf_matches = str(original_dnf["normalized"]) == str(target_dnf["normalized"])
    mnf_matches = str(original_mnf["normalized"]) == str(target_mnf["normalized"])
    return {
        "name": probe.name,
        "original": probe.original,
        "target": probe.target,
        "tau_normalized": original_text,
        "target_normalized": target_text,
        "tau_normalized_matches_target": original_text == target_text,
        "dnf_matches_target": dnf_matches,
        "mnf_matches_target": mnf_matches,
        "tau_normalized_chars": len(original_text),
        "target_normalized_chars": len(target_text),
        "char_reduction_if_targeted_percent": (
            round(100.0 * (len(original_text) - len(target_text)) / len(original_text), 3)
            if original_text
            else 0.0
        ),
        "target_equiv_check": equiv,
        "ok": (
            int(original_norm["returncode"]) == 0
            and int(target_norm["returncode"]) == 0
            and int(original_dnf["returncode"]) == 0
            and int(target_dnf["returncode"]) == 0
            and int(original_mnf["returncode"]) == 0
            and int(target_mnf["returncode"]) == 0
            and int(equiv["returncode"]) == 0
            and equiv["last_line"] == "no solution"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/equality-split-tau-probe.json"))
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Include extra alias-order permutations beyond the public four-case receipt.",
    )
    args = parser.parse_args()
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    corpus = extended_probes() if args.extended else probes()
    rows = [analyze(args.tau_bin, probe) for probe in corpus]
    useful = [
        row for row in rows
        if int(row["tau_normalized_chars"]) > int(row["target_normalized_chars"])
    ]
    matched = [row for row in rows if bool(row["tau_normalized_matches_target"])]
    dnf_matched = [row for row in rows if bool(row["dnf_matches_target"])]
    mnf_matched = [row for row in rows if bool(row["mnf_matches_target"])]
    target_sized = [
        row for row in rows
        if int(row["tau_normalized_chars"]) <= int(row["target_normalized_chars"])
    ]
    total_tau = sum(int(row["tau_normalized_chars"]) for row in rows)
    total_target = sum(int(row["target_normalized_chars"]) for row in rows)
    summary = {
        "scope": "Tau normalize probes for equality-split branch recombination",
        "ok": all(bool(row["ok"]) for row in rows),
        "feature_flag": os.environ.get("TAU_EQUALITY_SPLIT_RECOMBINE", ""),
        "case_count": len(rows),
        "extended": args.extended,
        "useful_reduction_cases": len(useful),
        "matched_target_cases": len(matched),
        "dnf_matched_target_cases": len(dnf_matched),
        "mnf_matched_target_cases": len(mnf_matched),
        "target_sized_cases": len(target_sized),
        "tau_normalized_chars": total_tau,
        "target_normalized_chars": total_target,
        "char_reduction_if_targeted_percent": (
            round(100.0 * (total_tau - total_target) / total_tau, 3)
            if total_tau
            else 0.0
        ),
        "rows": rows,
        "boundary": (
            "Targets are solver-checked equivalent to the originals. This script "
            "is a branch-recombination probe; with TAU_EQUALITY_SPLIT_RECOMBINE=1 "
            "it also measures the experimental Tau normalizer patch. DNF/MNF "
            "matches distinguish semantic canonical agreement from normalize-text "
            "presentation differences."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
