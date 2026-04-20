#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT = ROOT / "results" / "local" / "eml-qns-llm-memory-demo.json"
DEFAULT_PROPOSALS = ROOT / "examples" / "eml-qns" / "llm_candidate_proposals_v1.json"
DEFAULT_TAU_SOURCE = ROOT / "examples" / "tau" / "eml_qns_evidence_memory_v1.tau"
DEFAULT_TABLE_SOURCE = ROOT / "examples" / "tau" / "eml_symbolic_memory_table_v1.tau"
POSIX_LOCAL_PREFIXES = ("/" + "home" + "/", "/" + "Users" + "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(walk_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(walk_strings(item))
        return out
    return []


def looks_like_local_path(text: str) -> bool:
    return text.startswith(POSIX_LOCAL_PREFIXES) or (
        len(text) >= 3 and text[1:3] == ":\\"
    )


def validate_receipt(
    receipt: dict[str, Any],
    *,
    proposal_file: Path,
    tau_source: Path,
    table_source: Path,
    skip_file_hashes: bool,
) -> list[str]:
    errors: list[str] = []

    if receipt.get("schema") != "eml_qns_llm_memory_demo_v1":
        errors.append("wrong schema")

    summary = receipt.get("summary", {})
    rows = receipt.get("rows", [])
    if not isinstance(rows, list):
        errors.append("rows is not a list")
        rows = []

    promoted_count = sum(1 for row in rows if row.get("tau_check", {}).get("promoted"))
    review_count = sum(1 for row in rows if row.get("review_mask", 0) != 0)
    memory_updated_count = sum(
        1
        for row in rows
        if row.get("tau_check", {}).get("new_memory_mask")
        != row.get("tau_check", {}).get("old_memory_mask")
    )
    rejected_count = sum(1 for row in rows if not row.get("tau_check", {}).get("promoted"))
    rejected_preserved_count = sum(
        1
        for row in rows
        if not row.get("tau_check", {}).get("promoted")
        and row.get("tau_check", {}).get("new_memory_mask")
        == row.get("tau_check", {}).get("old_memory_mask")
    )

    expected_counts = {
        "candidate_count": len(rows),
        "promoted_count": promoted_count,
        "review_count": review_count,
        "memory_updated_count": memory_updated_count,
        "rejected_count": rejected_count,
        "rejected_preserved_count": rejected_preserved_count,
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            errors.append(f"{key} mismatch: summary={summary.get(key)!r}, expected={expected!r}")

    if rejected_count != rejected_preserved_count:
        errors.append("at least one rejected row changed memory")

    if not summary.get("qns_table_regression_ok"):
        errors.append("qns table regression did not pass")
    if not summary.get("symbolic_tau_table_check_ok"):
        errors.append("symbolic tau table check did not pass")
    if not summary.get("ok"):
        errors.append("receipt summary ok is false")

    for index, row in enumerate(rows):
        revision = row.get("tau_check", {}).get("table_revision", {})
        if revision.get("expected_mask") != revision.get("actual_mask"):
            errors.append(f"row {index} table revision expected/actual mismatch")
        if revision.get("ok") is not True:
            errors.append(f"row {index} table revision ok is not true")

    regression = receipt.get("qns_table_regression", {})
    for index, row in enumerate(regression.get("rows", [])):
        if row.get("ok") is not True:
            errors.append(f"qns table regression row {index} is not ok")
        if row.get("named_actual") != row.get("expected"):
            errors.append(f"qns table regression row {index} named result mismatch")
        if row.get("direct_actual") != row.get("expected"):
            errors.append(f"qns table regression row {index} direct result mismatch")

    hashes = receipt.get("input_hashes", {})
    if not skip_file_hashes:
        proposal_hash = hashes.get("proposal_file")
        if proposal_hash is not None and proposal_hash != sha256_file(proposal_file):
            errors.append("proposal_file hash mismatch")
        if hashes.get("tau_source") != sha256_file(tau_source):
            errors.append("tau_source hash mismatch")
        if hashes.get("table_source") != sha256_file(table_source):
            errors.append("table_source hash mismatch")

    leaked = [text for text in walk_strings(receipt) if looks_like_local_path(text)]
    if leaked:
        errors.append("receipt contains local path fragments")

    return errors


def mutate_receipt_for_self_test(receipt: dict[str, Any]) -> dict[str, Any]:
    mutated = json.loads(json.dumps(receipt))
    rows = mutated.get("rows", [])
    for row in rows:
        tau_check = row.get("tau_check", {})
        if not tau_check.get("promoted"):
            tau_check["new_memory_mask"] = (int(tau_check.get("old_memory_mask", 0)) + 1) & 0xFF
            revision = tau_check.get("table_revision", {})
            revision["actual_mask"] = tau_check["new_memory_mask"]
            return mutated
    if rows:
        rows[0].setdefault("tau_check", {}).setdefault("table_revision", {})["ok"] = False
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an EML/qNS table-memory receipt.")
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--proposal-file", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--tau-source", type=Path, default=DEFAULT_TAU_SOURCE)
    parser.add_argument("--table-source", type=Path, default=DEFAULT_TABLE_SOURCE)
    parser.add_argument(
        "--skip-file-hashes",
        action="store_true",
        help="Skip source-file hash checks, useful for live-model receipts copied elsewhere.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Also mutate the receipt and confirm the verifier rejects the mutation.",
    )
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    errors = validate_receipt(
        receipt,
        proposal_file=args.proposal_file,
        tau_source=args.tau_source,
        table_source=args.table_source,
        skip_file_hashes=args.skip_file_hashes,
    )

    self_test_errors: list[str] = []
    if args.self_test and not errors:
        mutated = mutate_receipt_for_self_test(receipt)
        mutation_errors = validate_receipt(
            mutated,
            proposal_file=args.proposal_file,
            tau_source=args.tau_source,
            table_source=args.table_source,
            skip_file_hashes=True,
        )
        if not mutation_errors:
            self_test_errors.append("mutated receipt was accepted")

    result = {
        "ok": not errors and not self_test_errors,
        "error_count": len(errors) + len(self_test_errors),
        "errors": errors,
        "self_test_errors": self_test_errors,
        "self_test_ran": args.self_test,
        "checked_rows": len(receipt.get("rows", [])) if isinstance(receipt.get("rows"), list) else 0,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
