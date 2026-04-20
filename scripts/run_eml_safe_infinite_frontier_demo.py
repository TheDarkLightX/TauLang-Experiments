#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any

from run_eml_qns_llm_memory_demo import (
    DEFAULT_TAU_BIN,
    TOP,
    evidence_names,
    expected_qns_table_revision,
    format_mask,
    run_tau_table_check,
    sha256_file,
    sha256_json,
)


ROOT = Path(__file__).resolve().parents[1]
FORMAL_ROOT = ROOT.parent / "Formal_Methods_Philosophy"
DEFAULT_PROPOSAL = ROOT / "results" / "local" / "eml-qns-scaled-sweep-proposals-r4-c20.json"
DEFAULT_RECEIPT = ROOT / "results" / "local" / "eml-qns-scaled-sweep-receipt-r4-c20.json"
DEFAULT_MLX_PROBE = ROOT / "results" / "local" / "eml-depth4-mlx-probe-full.json"
DEFAULT_TAU_SOURCE = ROOT / "examples" / "tau" / "eml_safe_infinite_frontier_table_v1.tau"
DEFAULT_OUT = ROOT / "results" / "local" / "eml-safe-infinite-frontier-demo-r4-c20.json"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "eml-safe-infinite-frontier-demo-r4-c20.md"


def root_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return str(resolved)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def proof_bridge_files() -> list[dict[str, Any]]:
    files = [
        (
            ROOT / "docs" / "infinite-tables.md",
            "finite executable lane embeds into completed reference semantics",
        ),
        (
            ROOT / "docs" / "safe-table-select-revision.md",
            "pointwise revision law and fixed-guard discipline",
        ),
        (
            ROOT / "proofs" / "lean" / "infinite_tables" / "CURRENT_STATUS.md",
            "checked monotone omega-continuous safe table syntax status",
        ),
        (
            ROOT
            / "proofs"
            / "lean"
            / "infinite_tables"
            / "safe_table_select_revision"
            / "README.md",
            "select/revision packet for fixed guards and replacement tables",
        ),
        (
            FORMAL_ROOT / "tutorials" / "safe-infinite-tables-in-tau-language.md",
            "tutorial framing for safe infinite-recursive table approximants",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for path, role in files:
        row = {
            "path": root_path(path),
            "role": role,
            "exists": path.exists(),
        }
        if path.exists():
            row["sha256"] = sha256_file(path)
        rows.append(row)
    return rows


def source_round(row: dict[str, Any]) -> int | None:
    value = row.get("source_round")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def stage_for(row: dict[str, Any]) -> tuple[int, str, str]:
    origin = str(row.get("origin") or "unknown")
    round_index = source_round(row)
    if origin == "mlx_depth4":
        return (0, "mlx_depth4_frontier", "MLX depth-4 GPU frontier")
    if round_index is not None:
        return (
            round_index,
            f"qwen36_sweep_round_{round_index}",
            f"Qwen 3.6 sweep round {round_index}",
        )
    return (10_000, f"{origin}_frontier", f"{origin} frontier")


def merge_rows(proposal: dict[str, Any], receipt: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = proposal.get("candidates")
    rows = receipt.get("rows")
    if not isinstance(candidates, list):
        raise SystemExit("proposal candidates must be a list")
    if not isinstance(rows, list):
        raise SystemExit("receipt rows must be a list")
    if len(candidates) != len(rows):
        raise SystemExit(f"proposal/receipt row count mismatch: {len(candidates)} != {len(rows)}")

    merged: list[dict[str, Any]] = []
    for index, (candidate, receipt_row) in enumerate(zip(candidates, rows)):
        if not isinstance(candidate, dict):
            candidate = {}
        if not isinstance(receipt_row, dict):
            raise SystemExit(f"receipt row {index} is not an object")
        if int(receipt_row.get("index", index)) != index:
            raise SystemExit(f"receipt row {index} has nonmatching index {receipt_row.get('index')}")
        merged_row = dict(receipt_row)
        merged_row["source_round"] = candidate.get("source_round")
        merged_row["proposal_note"] = candidate.get("note")
        merged.append(merged_row)
    return merged


def proposal_rounds(proposal: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rounds: dict[int, dict[str, Any]] = {}
    for item in proposal.get("meta", {}).get("rounds", []):
        if not isinstance(item, dict):
            continue
        try:
            rounds[int(item["round"])] = item
        except (KeyError, TypeError, ValueError):
            continue
    return rounds


def stage_screened_count(stage: dict[str, Any], round_meta: dict[int, dict[str, Any]], mlx_probe: dict[str, Any] | None) -> int | None:
    if stage["key"] == "mlx_depth4_frontier":
        if mlx_probe is None:
            return None
        scanned = mlx_probe.get("metrics", {}).get("scanned")
        return int(scanned) if isinstance(scanned, int) else None
    round_index = stage.get("round")
    if isinstance(round_index, int) and round_index in round_meta:
        raw_count = round_meta[round_index].get("raw_candidate_count")
        return int(raw_count) if isinstance(raw_count, int) else None
    return None


def build_frontier_receipt(
    rows: list[dict[str, Any]],
    *,
    round_meta: dict[int, dict[str, Any]],
    mlx_probe: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    stages: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for row in rows:
        order, key, label = stage_for(row)
        stage = stages.setdefault(
            key,
            {
                "order": order,
                "key": key,
                "label": label,
                "round": source_round(row),
                "row_indices": [],
            },
        )
        stage["row_indices"].append(int(row["index"]))

    state: dict[int, int] = {}
    target_promotions: dict[str, int] = defaultdict(int)
    row_receipts: list[dict[str, Any]] = []
    approximants: list[dict[str, Any]] = []

    rows_by_index = {int(row["index"]): row for row in rows}
    for stage_number, stage in enumerate(sorted(stages.values(), key=lambda item: item["order"]), start=1):
        stage_rows = [rows_by_index[index] for index in stage["row_indices"]]
        promoted_new = 0
        review_new = 0
        rejected_new = 0

        for row in stage_rows:
            index = int(row["index"])
            old = state.get(index, 0)
            promoted = bool(row.get("tau_check", {}).get("promoted"))
            guard = TOP if promoted else 0
            replacement = int(row["accepted_mask"])
            new = expected_qns_table_revision(guard, replacement, old)
            state[index] = new
            if promoted:
                promoted_new += 1
                target_promotions[str(row.get("target"))] += 1
            else:
                rejected_new += 1
            if int(row.get("review_mask", 0)) != 0:
                review_new += 1

            row_receipts.append(
                {
                    "index": index,
                    "target": row.get("target"),
                    "origin": row.get("origin"),
                    "source_round": row.get("source_round"),
                    "expr": row.get("expr"),
                    "canonical_expr": row.get("canonical_expr"),
                    "accepted_mask": replacement,
                    "accepted_atoms": evidence_names(replacement),
                    "review_mask": int(row.get("review_mask", 0)),
                    "review_reasons": row.get("review_reasons", []),
                    "promoted": promoted,
                    "safe_table_revision": {
                        "old_mask": old,
                        "guard_mask": guard,
                        "replacement_mask": replacement,
                        "new_mask": new,
                        "pointwise_formula": "(guard & replacement) | (guard' & old)",
                        "guard_fixed_lower_stratum": True,
                        "guard_reads_current_state": False,
                        "tau_qns_gate_ok": bool(row.get("tau_check", {}).get("table_revision", {}).get("ok")),
                    },
                }
            )

        approximants.append(
            {
                "stage": stage_number,
                "key": stage["key"],
                "label": stage["label"],
                "new_rows": len(stage_rows),
                "screened_count": stage_screened_count(stage, round_meta, mlx_probe),
                "promoted_new": promoted_new,
                "review_new": review_new,
                "rejected_new": rejected_new,
                "finite_prefix_rows": len(state),
                "finite_support_rows": sum(1 for value in state.values() if value != 0),
                "cumulative_promoted_rows": sum(target_promotions.values()),
                "target_promotions": dict(sorted(target_promotions.items())),
            }
        )

    final_state = {
        str(index): {
            "mask": mask,
            "atoms": evidence_names(mask),
        }
        for index, mask in sorted(state.items())
    }
    return approximants, row_receipts, final_state


def mlx_summary(mlx_probe: dict[str, Any] | None) -> dict[str, Any] | None:
    if mlx_probe is None:
        return None
    return {
        "schema": mlx_probe.get("schema"),
        "corpus": mlx_probe.get("corpus"),
        "metrics": mlx_probe.get("metrics"),
        "results": mlx_probe.get("results"),
    }


def report_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# EML Safe Infinite-Frontier Table Receipt",
        "",
        "This is the table-native reading of the scaled Qwen/MLX run.",
        "It treats the finite candidate frontier as a prefix of a countable candidate stream.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in [
        "finite_prefix_rows",
        "approximant_count",
        "promoted_rows",
        "review_rows",
        "rejected_rows",
        "tau_frontier_table_check_ok",
        "source_receipt_ok",
        "row_gate_ok",
        "ok",
    ]:
        lines.append(f"| `{key}` | `{report_value(summary.get(key))}` |")

    lines.extend(
        [
            "",
            "## Safe Table Reading",
            "",
            "Candidate indices live in an infinite stream. This run only materializes a finite prefix.",
            "",
            "For each candidate index `i`, the executable frontier update is:",
            "",
            "```text",
            "T_next(i) = table { when G(i) => A(i); else => T_old(i) }",
            "          = (G(i) & A(i)) | (G(i)' & T_old(i))",
            "```",
            "",
            "`G` and `A` are fixed lower-stratum evidence tables from parsing, numeric checks, review status, and the qNS Tau gate. They do not read the current recursive table state.",
            "",
            "## Approximants",
            "",
            "| Stage | Frontier | Rows | Screened | Promoted | Review | Rejected | Prefix | Support |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["approximants"]:
        screened = row["screened_count"] if row["screened_count"] is not None else ""
        lines.append(
            "| "
            f"{row['stage']} | "
            f"{row['label']} | "
            f"{row['new_rows']} | "
            f"{screened} | "
            f"{row['promoted_new']} | "
            f"{row['review_new']} | "
            f"{row['rejected_new']} | "
            f"{row['finite_prefix_rows']} | "
            f"{row['finite_support_rows']} |"
        )

    lines.extend(
        [
            "",
            "## Proof Bridge",
            "",
            "| Artifact | Role | Present |",
            "| --- | --- | --- |",
        ]
    )
    for row in result["proof_bridge"]:
        present = "true" if row["exists"] else "false"
        lines.append(f"| `{row['path']}` | {row['role']} | {present} |")

    lines.extend(
        [
            "",
            "## Tau Witness",
            "",
            f"- Source: `{result['tau_frontier_table_check']['source']}`",
            f"- Universal table/raw equivalence check: `{result['tau_frontier_table_check']['last_line']}`",
            f"- OK: `{report_value(result['tau_frontier_table_check']['ok'])}`",
            "",
            "## Final Nonzero Rows",
            "",
            "| Candidate index | Mask | Evidence atoms |",
            "| ---: | ---: | --- |",
        ]
    )
    for index, row in result["final_state"].items():
        if int(row["mask"]) == 0:
            continue
        atoms = ", ".join(row["atoms"]) if row["atoms"] else "(none)"
        lines.append(f"| {index} | `{format_mask(int(row['mask']))}` | {atoms} |")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Recast the scaled EML/qNS sweep as safe infinite-table approximants.")
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--mlx-probe", type=Path, default=DEFAULT_MLX_PROBE)
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-source", type=Path, default=DEFAULT_TAU_SOURCE)
    parser.add_argument("--tau-timeout-s", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    proposal_path = args.proposal if args.proposal.is_absolute() else ROOT / args.proposal
    receipt_path = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
    mlx_path = args.mlx_probe if args.mlx_probe.is_absolute() else ROOT / args.mlx_probe
    tau_source_path = args.tau_source if args.tau_source.is_absolute() else ROOT / args.tau_source

    proposal = load_json(proposal_path)
    receipt = load_json(receipt_path)
    mlx_probe = load_json(mlx_path) if mlx_path.exists() else None

    if proposal.get("schema") != "eml_candidate_proposals_v1":
        raise SystemExit("proposal schema must be eml_candidate_proposals_v1")
    if receipt.get("schema") != "eml_qns_llm_memory_demo_v1":
        raise SystemExit("receipt schema must be eml_qns_llm_memory_demo_v1")

    rows = merge_rows(proposal, receipt)
    approximants, row_receipts, final_state = build_frontier_receipt(
        rows,
        round_meta=proposal_rounds(proposal),
        mlx_probe=mlx_probe,
    )
    tau_check = run_tau_table_check(args.tau_bin, tau_source_path, timeout_s=args.tau_timeout_s)
    source_receipt_ok = bool(receipt.get("summary", {}).get("ok"))
    row_gate_ok = all(
        bool(row["safe_table_revision"]["tau_qns_gate_ok"])
        and row["safe_table_revision"]["guard_mask"] in {0, TOP}
        for row in row_receipts
    )

    result = {
        "schema": "eml_safe_infinite_frontier_demo_v1",
        "scope": {
            "claim": (
                "The scaled EML/qNS experiment is a finite executable approximant "
                "of a safe infinite candidate table."
            ),
            "not_claimed": [
                "not an unrestricted TABA proof",
                "not a proof that Qwen candidates are true by generation alone",
                "not full analytic Tau semantics for EML",
                "not an exhaustive depth-5 or depth-6 search",
            ],
            "infinite_table_reading": {
                "index_set": "countable candidate stream, modeled by natural-number candidate indices",
                "finite_lane": "this receipt materializes finite frontier prefixes only",
                "state": "T_n(i) is the qNS evidence memory for candidate row i at approximant n",
                "guard": "G_n(i) is fixed lower-stratum evidence: promoted rows get top, rejected rows get bottom",
                "replacement": "A_n(i) is the fixed accepted-evidence qNS mask for row i",
                "update": "T_{n+1}(i) = (G_n(i) & A_n(i)) | (G_n(i)' & T_n(i))",
            },
        },
        "inputs": {
            "proposal": root_path(proposal_path),
            "receipt": root_path(receipt_path),
            "mlx_probe": root_path(mlx_path) if mlx_path.exists() else None,
            "tau_source": root_path(tau_source_path),
            "proposal_sha256": sha256_file(proposal_path),
            "receipt_sha256": sha256_file(receipt_path),
            "mlx_probe_sha256": sha256_file(mlx_path) if mlx_path.exists() else None,
            "tau_source_sha256": sha256_file(tau_source_path),
            "proposal_data_sha256": sha256_json(proposal),
            "receipt_data_sha256": sha256_json(receipt),
        },
        "source_summary": {
            "proposal_rounds": proposal.get("meta", {}).get("rounds", []),
            "receipt_summary": receipt.get("summary", {}),
            "mlx_probe": mlx_summary(mlx_probe),
        },
        "proof_bridge": proof_bridge_files(),
        "tau_frontier_table_check": tau_check,
        "approximants": approximants,
        "rows": row_receipts,
        "final_state": final_state,
        "summary": {
            "finite_prefix_rows": len(row_receipts),
            "approximant_count": len(approximants),
            "promoted_rows": sum(1 for row in row_receipts if row["promoted"]),
            "review_rows": sum(1 for row in row_receipts if row["review_mask"] != 0),
            "rejected_rows": sum(1 for row in row_receipts if not row["promoted"]),
            "tau_frontier_table_check_ok": tau_check["ok"],
            "source_receipt_ok": source_receipt_ok,
            "row_gate_ok": row_gate_ok,
            "ok": tau_check["ok"] and source_receipt_ok and row_gate_ok,
        },
    }

    out = args.out if args.out.is_absolute() else ROOT / args.out
    report_out = args.report_out if args.report_out.is_absolute() else ROOT / args.report_out
    out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report_out.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0 if result["summary"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
