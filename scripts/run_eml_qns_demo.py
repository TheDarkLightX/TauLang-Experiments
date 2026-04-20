#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXACT = ROOT / "examples" / "eml-qns" / "eml_bounded_symbolic_regression.json"
DEFAULT_NOISY = ROOT / "examples" / "eml-qns" / "eml_noisy_regression_certificates.json"
DEFAULT_TAU_BIN = ROOT / "external" / "tau-lang" / "build-Release" / "tau"
DEFAULT_OUT = ROOT / "results" / "local" / "eml-qns-demo-gallery.json"

MASK = 0xFF
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
QNS_VALUE_RE = re.compile(r"\{\s*(\d+)\s*\}:qns(?:8|64)")
PLAIN_VALUE_RE = re.compile(r"%\d+:\s*(\d+)\s*$")

CERT_BITS = {
    "grammar_bounded": 0,
    "fit_passed": 1,
    "holdout_passed": 2,
    "minimality_scoped": 3,
    "proof_receipt": 4,
    "symbolic_identity": 5,
    "residual_certificate": 6,
    "review_required": 7,
}
REQUIRED_MASK = sum(1 << bit for name, bit in CERT_BITS.items() if name != "review_required")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def qns_const(mask: int) -> str:
    return f"{{ #x{mask & MASK:02X} }}:qns8"


def qns_not(expr: str) -> str:
    return f"({qns_const(MASK)} ^ ({expr}))"


def bit(name: str) -> int:
    return 1 << CERT_BITS[name]


def mask_names(mask: int) -> list[str]:
    return [name for name, idx in CERT_BITS.items() if mask & (1 << idx)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def tau_check(tau_bin: Path, accepted_mask: int, review_mask: int, timeout_s: float) -> dict[str, Any]:
    accepted = qns_const(accepted_mask)
    required = qns_const(REQUIRED_MASK)
    review = qns_const(review_mask)
    missing_expr = f"(({required}) & ({qns_not(accepted)}))"
    promoted_expr = f"(({accepted}) & ({required}))"
    blocker_expr = f"(({missing_expr}) | ({review}))"
    missing, missing_raw = run_tau_qns_normalize(tau_bin, missing_expr, timeout_s=timeout_s)
    promoted, promoted_raw = run_tau_qns_normalize(tau_bin, promoted_expr, timeout_s=timeout_s)
    blocker, blocker_raw = run_tau_qns_normalize(tau_bin, blocker_expr, timeout_s=timeout_s)
    return {
        "missing_required_mask": missing,
        "promoted_mask": promoted,
        "blocker_mask": blocker,
        "promoted": missing == 0 and blocker == 0 and promoted == REQUIRED_MASK,
        "raw": {
            "missing_required": missing_raw,
            "promoted": promoted_raw,
            "blocker": blocker_raw,
        },
    }


def validate_exact_result(result: dict[str, Any]) -> dict[str, Any]:
    accepted = 0
    review_reasons: list[str] = []
    best = result.get("best_fit")
    if best is not None:
        accepted |= bit("grammar_bounded")
    else:
        review_reasons.append("missing best_fit")
    if best and best.get("train_ok") is True:
        accepted |= bit("fit_passed")
    else:
        review_reasons.append("training fit did not pass")
    if best and best.get("holdout_ok") is True:
        accepted |= bit("holdout_passed")
    else:
        review_reasons.append("holdout fit did not pass")
    minimal = result.get("minimality_certificate", {})
    if minimal.get("minimal_within_bounded_corpus") is True:
        accepted |= bit("minimality_scoped")
    else:
        review_reasons.append("bounded minimality certificate did not pass")
    if result.get("proof_receipt", {}).get("accepted") is True:
        accepted |= bit("proof_receipt")
    else:
        review_reasons.append("proof receipt did not accept")
    if result.get("symbolic_identity", {}).get("proved_by_simplify") is True:
        accepted |= bit("symbolic_identity")
    else:
        review_reasons.append("symbolic identity check did not accept")
    if best and best.get("train_error") is not None and best.get("holdout_error") is not None:
        accepted |= bit("residual_certificate")
    else:
        review_reasons.append("residual fields are missing")
    review = bit("review_required") if review_reasons else 0
    return {
        "source_kind": "exact_bounded",
        "target": result["target"],
        "expr": best["expr"] if best else None,
        "accepted_mask": accepted,
        "review_mask": review,
        "review_reasons": review_reasons,
    }


def validate_noisy_result(result: dict[str, Any]) -> dict[str, Any]:
    accepted = 0
    review_reasons: list[str] = []
    winner = result.get("winner")
    if winner is not None:
        accepted |= bit("grammar_bounded")
    else:
        review_reasons.append("missing winner")
    if winner and winner.get("train_mse_noisy") is not None:
        accepted |= bit("fit_passed")
    else:
        review_reasons.append("no noisy training objective")
    if winner and winner.get("holdout_mse_clean") is not None:
        accepted |= bit("holdout_passed")
    else:
        review_reasons.append("no holdout objective")
    residual = result.get("residual_certificate", {})
    if residual.get("winner_rank") == 0:
        accepted |= bit("minimality_scoped")
    else:
        review_reasons.append("winner is not rank 0 under declared objective")
    if result.get("proof_receipt", {}).get("accepted") is True:
        accepted |= bit("proof_receipt")
    else:
        review_reasons.append("proof receipt did not accept")
    if result.get("symbolic_identity", {}).get("proved_by_simplify") is True:
        accepted |= bit("symbolic_identity")
    else:
        review_reasons.append("symbolic identity check did not accept")
    if residual.get("winner_train_residual_noisy") and residual.get("winner_holdout_residual_clean"):
        accepted |= bit("residual_certificate")
    else:
        review_reasons.append("residual certificate is missing")
    review = bit("review_required") if review_reasons else 0
    return {
        "source_kind": "noisy_bounded",
        "target": result["clean_target"],
        "expr": winner["expr"] if winner else None,
        "accepted_mask": accepted,
        "review_mask": review,
        "review_reasons": review_reasons,
    }


def build_manifest(exact_path: Path, noisy_path: Path, tau_bin: Path, timeout_s: float) -> dict[str, Any]:
    exact = load_json(exact_path)
    noisy = load_json(noisy_path)
    source_artifacts = {
        "exact_bounded": {
            "path": rel(exact_path),
            "sha256": sha256_file(exact_path),
            "schema": exact.get("schema"),
            "parameters": exact.get("parameters"),
        },
        "noisy_bounded": {
            "path": rel(noisy_path),
            "sha256": sha256_file(noisy_path),
            "schema": noisy.get("schema"),
            "parameters": noisy.get("parameters"),
        },
    }
    rows = [validate_exact_result(result) for result in exact["results"]]
    rows.extend(validate_noisy_result(result) for result in noisy["results"])
    for row in rows:
        source = source_artifacts[row["source_kind"]]
        row["source_artifact"] = source["path"]
        row["source_sha256"] = source["sha256"]
        row["accepted_atoms"] = mask_names(row["accepted_mask"])
        row["review_atoms"] = mask_names(row["review_mask"])
        row["tau_check"] = tau_check(tau_bin, row["accepted_mask"], row["review_mask"], timeout_s)
    return {
        "schema": "eml_regression_certificate_manifest_v1",
        "scope": {
            "claim": (
                "EML regression winners can be wrapped as qNS-style certificates "
                "and promoted only when required finite evidence bits are present."
            ),
            "not_claimed": [
                "not full symbolic regression",
                "not statistical consistency",
                "not native Tau analytic semantics",
                "not proof beyond each source artifact's bounded corpus",
            ],
        },
        "certificate_bits": CERT_BITS,
        "required_mask": REQUIRED_MASK,
        "source_artifacts": source_artifacts,
        "summary": {
            "ok": all(row["tau_check"]["promoted"] for row in rows),
            "certificate_count": len(rows),
            "promoted_count": sum(1 for row in rows if row["tau_check"]["promoted"]),
            "review_count": sum(1 for row in rows if row["review_mask"] != 0),
            "tau_blocker_count": sum(1 for row in rows if row["tau_check"]["blocker_mask"] != 0),
            "exact_source_count": sum(1 for row in rows if row["source_kind"] == "exact_bounded"),
            "noisy_source_count": sum(1 for row in rows if row["source_kind"] == "noisy_bounded"),
        },
        "rows": rows,
    }


def current_source_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        source["path"]: sha256_file(ROOT / source["path"])
        for source in manifest["source_artifacts"].values()
    }


def verify_row(row: dict[str, Any], hashes: dict[str, str], tau_bin: Path, timeout_s: float) -> dict[str, Any]:
    expected_hash = hashes.get(row["source_artifact"])
    hash_ok = expected_hash is not None and row["source_sha256"] == expected_hash
    tau = tau_check(tau_bin, int(row["accepted_mask"]), int(row["review_mask"]), timeout_s)
    accepted_mask = int(row["accepted_mask"])
    missing_required = REQUIRED_MASK & (REQUIRED_MASK ^ (accepted_mask & REQUIRED_MASK))
    promoted = hash_ok and tau["promoted"]
    return {
        "hash_ok": hash_ok,
        "missing_required_mask": missing_required,
        "missing_required_atoms": mask_names(missing_required),
        "review_blocked": int(row["review_mask"]) != 0,
        "tau_check": tau,
        "promoted": promoted,
        "reject_reason": None
        if promoted
        else (
            "stale_source_hash"
            if not hash_ok
            else "tau_missing_required_or_review_blocked"
        ),
    }


def tamper_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tampered: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        for bit_name in ("proof_receipt", "residual_certificate"):
            modified = copy.deepcopy(row)
            modified["tamper_kind"] = f"drop_{bit_name}"
            modified["source_index"] = index
            modified["accepted_mask"] = int(modified["accepted_mask"]) & ~bit(bit_name)
            tampered.append(modified)
        modified = copy.deepcopy(row)
        modified["tamper_kind"] = "force_review_required"
        modified["source_index"] = index
        modified["review_mask"] = int(modified["review_mask"]) | bit("review_required")
        tampered.append(modified)
        modified = copy.deepcopy(row)
        modified["tamper_kind"] = "stale_source_hash"
        modified["source_index"] = index
        modified["source_sha256"] = "0" * 64
        tampered.append(modified)
    return tampered


def build_failclosed(manifest: dict[str, Any], tau_bin: Path, timeout_s: float) -> dict[str, Any]:
    hashes = current_source_hashes(manifest)
    valid_rows = [
        {
            "target": row["target"],
            "expr": row["expr"],
            "check": verify_row(row, hashes, tau_bin, timeout_s),
        }
        for row in manifest["rows"]
    ]
    tampered = []
    for row in tamper_rows(manifest["rows"]):
        tampered.append(
            {
                "target": row["target"],
                "expr": row["expr"],
                "tamper_kind": row["tamper_kind"],
                "source_index": row["source_index"],
                "check": verify_row(row, hashes, tau_bin, timeout_s),
            }
        )
    summary = {
        "ok": all(row["check"]["promoted"] for row in valid_rows)
        and all(not row["check"]["promoted"] for row in tampered),
        "valid_count": len(valid_rows),
        "valid_promoted_count": sum(1 for row in valid_rows if row["check"]["promoted"]),
        "tampered_count": len(tampered),
        "tampered_rejected_count": sum(1 for row in tampered if not row["check"]["promoted"]),
        "tau_rejected_count": sum(
            1
            for row in tampered
            if row["check"]["reject_reason"] == "tau_missing_required_or_review_blocked"
        ),
        "hash_rejected_count": sum(
            1 for row in tampered if row["check"]["reject_reason"] == "stale_source_hash"
        ),
    }
    return {
        "schema": "eml_regression_certificate_failclosed_v1",
        "scope": {
            "claim": (
                "The EML regression qNS certificate wrapper promotes valid rows "
                "and rejects rows with missing required bits, review blockers, "
                "or stale source hashes."
            ),
            "not_claimed": [
                "not full symbolic regression",
                "not a cryptographic attestation scheme",
                "not protection against a compromised verifier",
            ],
        },
        "required_mask": REQUIRED_MASK,
        "certificate_bits": CERT_BITS,
        "source_hashes": hashes,
        "summary": summary,
        "valid_rows": valid_rows,
        "tampered_rows": tampered,
    }


def build_gallery(manifest: dict[str, Any], failclosed: dict[str, Any], tau_bin: Path, timeout_s: float) -> dict[str, Any]:
    demo_rows = []
    for row in manifest["rows"]:
        fast_gate = tau_check(tau_bin, int(row["accepted_mask"]), int(row["review_mask"]), timeout_s)
        demo_rows.append(
            {
                "target": row["target"],
                "expression": row["expr"],
                "source_kind": row["source_kind"],
                "source_artifact": row["source_artifact"],
                "accepted_atoms": row["accepted_atoms"],
                "fast_tau_gate": fast_gate,
                "promoted": fast_gate["promoted"],
            }
        )
    summary = {
        "ok": all(row["promoted"] for row in demo_rows)
        and failclosed["summary"]["tampered_count"]
        == failclosed["summary"]["tampered_rejected_count"],
        "slow_source_count": len(manifest["source_artifacts"]),
        "fast_promoted_count": sum(1 for row in demo_rows if row["promoted"]),
        "negative_rejected_count": failclosed["summary"]["tampered_rejected_count"],
    }
    return {
        "schema": "eml_qns_demo_gallery_v1",
        "scope": {
            "claim": (
                "The EML demo has a slow source lane that searches bounded "
                "formula corpora and a fast Tau qns8 lane that gates returned "
                "certificates before public display."
            ),
            "not_claimed": [
                "not full symbolic regression",
                "not neural proposal generation",
                "not native Tau analytic semantics",
                "not cryptographic attestation",
            ],
        },
        "slow_lane": {
            "description": "bounded exact and noisy EML regression artifacts",
            "source_artifacts": manifest["source_artifacts"],
            "certificate_count": manifest["summary"]["certificate_count"],
        },
        "fast_lane": {
            "description": "Tau qns8 mask gate over certificate evidence bits",
            "required_mask": manifest["required_mask"],
            "promoted_count": summary["fast_promoted_count"],
            "row_count": len(demo_rows),
        },
        "negative_lane": {
            "description": "tampered certificate rejection corpus",
            "tampered_count": failclosed["summary"]["tampered_count"],
            "tampered_rejected_count": failclosed["summary"]["tampered_rejected_count"],
            "tau_rejected_count": failclosed["summary"]["tau_rejected_count"],
            "hash_rejected_count": failclosed["summary"]["hash_rejected_count"],
        },
        "deeper_search_lane": {
            "description": "optional follow-up lane for depth-4 or deeper search",
            "default_depth": 3,
            "depth_3_corpus_size": 1446,
            "depth_4_corpus_size": 2090918,
            "status": "not run by default because it is more than one thousand times larger",
        },
        "rows": demo_rows,
        "summary": summary,
    }


def write_artifacts(out: Path, manifest: dict[str, Any], failclosed: dict[str, Any], gallery: dict[str, Any]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(gallery, indent=2) + "\n", encoding="utf-8")
    stem = out.with_suffix("")
    stem.with_name(stem.name + "-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    stem.with_name(stem.name + "-failclosed.json").write_text(
        json.dumps(failclosed, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the EML/qNS certificate demo.")
    parser.add_argument("--exact", type=Path, default=DEFAULT_EXACT)
    parser.add_argument("--noisy", type=Path, default=DEFAULT_NOISY)
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout-s", type=float, default=10.0)
    parser.add_argument(
        "--refresh-search",
        action="store_true",
        help="Reserved for a future live EML search lane. The public v1 demo uses checked fixtures.",
    )
    args = parser.parse_args()

    if args.refresh_search:
        raise SystemExit(
            "--refresh-search is intentionally not enabled in v1. "
            "Use checked fixture artifacts or add a streaming depth-4 search lane first."
        )

    exact = args.exact if args.exact.is_absolute() else ROOT / args.exact
    noisy = args.noisy if args.noisy.is_absolute() else ROOT / args.noisy
    tau_bin = args.tau_bin if args.tau_bin.is_absolute() else ROOT / args.tau_bin
    out = args.out if args.out.is_absolute() else ROOT / args.out
    if not tau_bin.exists():
        raise SystemExit(f"missing Tau binary: {tau_bin}")

    manifest = build_manifest(exact, noisy, tau_bin, args.timeout_s)
    failclosed = build_failclosed(manifest, tau_bin, args.timeout_s)
    gallery = build_gallery(manifest, failclosed, tau_bin, args.timeout_s)
    write_artifacts(out, manifest, failclosed, gallery)
    summary = gallery["summary"]
    negative = gallery["negative_lane"]
    print("EML/qNS demo passed" if summary["ok"] else "EML/qNS demo failed")
    print(f"slow_source_count = {summary['slow_source_count']}")
    print(f"fast_promoted_count = {summary['fast_promoted_count']}")
    print(f"tampered_count = {negative['tampered_count']}")
    print(f"tampered_rejected_count = {negative['tampered_rejected_count']}")
    print(f"tau_rejected_count = {negative['tau_rejected_count']}")
    print(f"hash_rejected_count = {negative['hash_rejected_count']}")
    print(f"out = {rel(out)}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
