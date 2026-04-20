#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from run_neuro_symbolic_qns_experiment import (
    DEFAULT_TAU_BIN,
    ROOT,
    check_expr,
    defi_expected,
    frontier_expected,
    qns_const,
    qns_not_expr,
    research_expected,
)


DEFAULT_OUT = ROOT / "results" / "local" / "neuro-symbolic-qns-llm-experiment.json"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "neuro-symbolic-qns-llm-experiment.md"

RESEARCH_LABELS = (
    "fixed_revision_law",
    "current_guard_law",
    "arbitrary_select_law",
    "malformed_claim",
    "depth5_region",
    "safe_revision_packet",
    "runtime_lowering_gap",
    "unrestricted_taba_claim",
)
FRONTIER_LABELS = (
    "depth4_ln_exact",
    "depth5_guided_region",
    "exp_exp_near_miss",
    "cold_random_shard",
    "expensive_proof_lane",
    "reserve_5",
    "reserve_6",
    "reserve_7",
)
DEFI_LABELS = (
    "oracle_and_exploit_overlap",
    "oracle_divergence_only",
    "solvency_gap_with_healthy_flag",
    "liquidation_cascade",
    "normal_market",
    "governance_override",
    "reserve_6",
    "reserve_7",
)
RESEARCH_FRONTIER_MASK = 0xFF
SEARCH_REGION_MASK = 0x1F
DEFI_MARKET_MASK = 0x3F


def c(mask: int) -> str:
    return qns_const(mask)


def build_prompt() -> str:
    return f"""Return one JSON object only. No Markdown.

You are an untrusted neural proposer for a Tau qNS8 experiment.
Each listed label corresponds to one qNS8 bit. Set boolean evidence fields.
The experiment materializes the fixed row frontier separately:
- all research ids are proposed rows,
- frontier ids through expensive_proof_lane are active search regions,
- DeFi ids through governance_override are active markets.
Tau will compute the actual promoted/rejected/action masks later.

Use conservative, plausible evidence:
- current_guard_law and unrestricted_taba_claim should be counterexample risks.
- fixed_revision_law and safe_revision_packet should be strong proof candidates.
- malformed_claim should fail parse.
- depth5_region and runtime_lowering_gap should need review.
- DeFi exploit should outrank oracle/healthy signals.

Schema:
{{
  "schema": "neuro_symbolic_qns_llm_proposal_v1",
  "research": [
    {{
      "id": "fixed_revision_law",
      "proposed": true,
      "parse_ok": true,
      "symbolic_ok": true,
      "proof_ok": true,
      "counterexample": false,
      "review": false,
      "hard_reject": false,
      "note": "short reason"
    }}
  ],
  "frontier": [
    {{
      "id": "depth4_ln_exact",
      "region": true,
      "exact_witness": true,
      "high_yield": true,
      "near_miss": false,
      "stale_low_yield": false,
      "high_cost": false,
      "note": "short reason"
    }}
  ],
  "defi": [
    {{
      "id": "oracle_and_exploit_overlap",
      "market": true,
      "exploit_witness": true,
      "oracle_divergence": true,
      "solvency_gap": true,
      "liquidation_cascade": true,
      "governance_override": false,
      "healthy": true,
      "note": "short reason"
    }}
  ]
}}

Research ids, exactly once each:
{", ".join(RESEARCH_LABELS)}

Frontier ids, exactly once each:
{", ".join(FRONTIER_LABELS)}

DeFi ids, exactly once each:
{", ".join(DEFI_LABELS)}
"""


def extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start : end + 1])


def call_ollama(
    model: str,
    prompt: str,
    *,
    url: str,
    timeout_s: float,
    num_gpu: int,
    num_predict: int,
    temperature: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
            "num_gpu": num_gpu,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {
        "model": data.get("model", model),
        "raw_response": data.get("response", ""),
        "total_duration_ns": data.get("total_duration"),
        "load_duration_ns": data.get("load_duration"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "temperature": temperature,
        "num_predict": num_predict,
        "num_gpu": num_gpu,
    }


def row_map(rows: Any, labels: tuple[str, ...], fields: tuple[str, ...]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    if not isinstance(rows, list):
        rows = []
    by_id = {str(row.get("id")): row for row in rows if isinstance(row, dict)}
    masks = {field: 0 for field in fields}
    normalized: list[dict[str, Any]] = []
    for bit, label in enumerate(labels):
        row = by_id.get(label, {})
        out: dict[str, Any] = {"id": label, "bit": bit, "note": str(row.get("note", ""))}
        for field in fields:
            value = bool(row.get(field, False))
            out[field] = value
            if value:
                masks[field] |= 1 << bit
        normalized.append(out)
    return masks, normalized


def force_field(rows: list[dict[str, Any]], masks: dict[str, int], field: str, mask: int) -> None:
    masks[field] = mask
    for row in rows:
        bit = int(row["bit"])
        row[field] = bool(mask & (1 << bit))
        row[f"{field}_forced_by_experiment"] = True


def build_tau_rows(
    tau_bin: Path,
    source: str,
    research: dict[str, int],
    frontier: dict[str, int],
    defi: dict[str, int],
    *,
    timeout_s: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    r = research
    expected_r = research_expected(r)
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
            check_expr(tau_bin, source, "llm_research_qns", "promoted", promoted_expr, expected_r["research_promoted"], RESEARCH_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_research_qns", "falsified", falsified_expr, expected_r["research_falsified"], RESEARCH_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_research_qns", "hard_reject", hard_reject_expr, expected_r["research_hard_reject"], RESEARCH_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_research_qns", "review", review_expr, expected_r["research_review"], RESEARCH_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_research_qns", "memory_revise_promoted", f"table {{ when {c(expected_r['research_promoted'])} => {c(r['proposed'])}; else => {c(0)} }}", expected_r["research_memory"], RESEARCH_LABELS, timeout_s=timeout_s),
        ]
    )

    f = frontier
    expected_f = frontier_expected(f)
    rows.extend(
        [
            check_expr(tau_bin, source, "llm_frontier_qns", "certify", f"({c(f['region'])} & {c(f['exact_witness'])})", expected_f["frontier_certify"], FRONTIER_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_frontier_qns", "expand", f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & {c(f['high_yield'])} & {qns_not_expr(c(f['high_cost']))})", expected_f["frontier_expand"], FRONTIER_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_frontier_qns", "repair", f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & {qns_not_expr(c(f['high_yield']))} & {c(f['near_miss'])} & {qns_not_expr(c(f['stale_low_yield']))})", expected_f["frontier_repair"], FRONTIER_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_frontier_qns", "prune", f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & {qns_not_expr(c(f['high_yield']))} & {qns_not_expr(c(f['near_miss']))} & {c(f['stale_low_yield'])})", expected_f["frontier_prune"], FRONTIER_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_frontier_qns", "throttle", f"({c(f['region'])} & {qns_not_expr(c(f['exact_witness']))} & {qns_not_expr(c(f['high_yield']))} & {qns_not_expr(c(f['near_miss']))} & {qns_not_expr(c(f['stale_low_yield']))} & {c(f['high_cost'])})", expected_f["frontier_throttle"], FRONTIER_LABELS, timeout_s=timeout_s),
        ]
    )

    d = defi
    expected_d = defi_expected(d)
    rows.extend(
        [
            check_expr(tau_bin, source, "llm_defi_qns", "freeze", f"({c(d['market'])} & {c(d['exploit_witness'])})", expected_d["defi_freeze"], DEFI_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_defi_qns", "quarantine_oracle", f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & {c(d['oracle_divergence'])})", expected_d["defi_quarantine_oracle"], DEFI_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_defi_qns", "pause_borrow", f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & {qns_not_expr(c(d['oracle_divergence']))} & {c(d['solvency_gap'])})", expected_d["defi_pause_borrow"], DEFI_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_defi_qns", "cap_liquidation", f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & {qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & {c(d['liquidation_cascade'])})", expected_d["defi_cap_liquidation"], DEFI_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_defi_qns", "governance_review", f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & {qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & {qns_not_expr(c(d['liquidation_cascade']))} & {c(d['governance_override'])})", expected_d["defi_governance_review"], DEFI_LABELS, timeout_s=timeout_s),
            check_expr(tau_bin, source, "llm_defi_qns", "allow", f"({c(d['market'])} & {qns_not_expr(c(d['exploit_witness']))} & {qns_not_expr(c(d['oracle_divergence']))} & {qns_not_expr(c(d['solvency_gap']))} & {qns_not_expr(c(d['liquidation_cascade']))} & {qns_not_expr(c(d['governance_override']))} & {c(d['healthy'])})", expected_d["defi_allow"], DEFI_LABELS, timeout_s=timeout_s),
        ]
    )
    return rows


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Neuro-Symbolic qNS LLM Experiment Receipt",
        "",
        "Qwen proposes evidence bits for fixed rows. Tau qNS8 computes exact masks from those bits.",
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
            "## Tau qNS Results",
            "",
            "| Suite | Check | Actual names | Result |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in result["rows"]:
        actual = ", ".join(row["actual_names"]) if row["actual_names"] else "(none)"
        status = "pass" if row["ok"] else "fail"
        lines.append(f"| `{row['suite']}` | `{row['name']}` | {actual} | {status} |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live LLM -> Tau qNS8 neuro-symbolic evidence experiment.")
    parser.add_argument("--model", default=os.environ.get("QNS_LOCAL_MODEL", "qwen3.6:35b"))
    parser.add_argument("--ollama-url", default=os.environ.get("QNS_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"))
    parser.add_argument("--ollama-timeout-s", type=float, default=900.0)
    parser.add_argument("--num-gpu", type=int, default=999)
    parser.add_argument("--num-predict", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-timeout-s", type=float, default=30.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    prompt = build_prompt()
    model_meta = call_ollama(
        args.model,
        prompt,
        url=args.ollama_url,
        timeout_s=args.ollama_timeout_s,
        num_gpu=args.num_gpu,
        num_predict=args.num_predict,
        temperature=args.temperature,
    )
    proposal = extract_json_object(str(model_meta["raw_response"]))
    if proposal.get("schema") != "neuro_symbolic_qns_llm_proposal_v1":
        raise SystemExit("proposal schema must be neuro_symbolic_qns_llm_proposal_v1")

    research_masks, research_rows = row_map(
        proposal.get("research"),
        RESEARCH_LABELS,
        ("proposed", "parse_ok", "symbolic_ok", "proof_ok", "counterexample", "review", "hard_reject"),
    )
    frontier_masks, frontier_rows = row_map(
        proposal.get("frontier"),
        FRONTIER_LABELS,
        ("region", "exact_witness", "high_yield", "near_miss", "stale_low_yield", "high_cost"),
    )
    defi_masks, defi_rows = row_map(
        proposal.get("defi"),
        DEFI_LABELS,
        ("market", "exploit_witness", "oracle_divergence", "solvency_gap", "liquidation_cascade", "governance_override", "healthy"),
    )
    force_field(research_rows, research_masks, "proposed", RESEARCH_FRONTIER_MASK)
    force_field(frontier_rows, frontier_masks, "region", SEARCH_REGION_MASK)
    force_field(defi_rows, defi_masks, "market", DEFI_MARKET_MASK)
    tau_rows = build_tau_rows(
        args.tau_bin,
        "",
        research_masks,
        frontier_masks,
        defi_masks,
        timeout_s=args.tau_timeout_s,
    )
    result = {
        "schema": "neuro_symbolic_qns_llm_experiment_v1",
        "scope": {
            "claim": "A live local LLM can propose evidence bits while Tau qNS8 performs exact symbolic mask computation.",
            "not_claimed": [
                "not trusting model output",
                "not probabilistic arithmetic inside Tau",
                "not unrestricted TABA tables",
                "not financial advice",
            ],
        },
        "prompt": prompt,
        "model": {key: value for key, value in model_meta.items() if key != "raw_response"},
        "proposal": proposal,
        "normalized_rows": {
            "research": research_rows,
            "frontier": frontier_rows,
            "defi": defi_rows,
        },
        "masks": {
            "research": research_masks,
            "frontier": frontier_masks,
            "defi": defi_masks,
        },
        "rows": tau_rows,
        "summary": {
            "model": args.model,
            "tau_row_count": len(tau_rows),
            "tau_rows_ok": all(row["ok"] for row in tau_rows),
            "research_rows": len(research_rows),
            "frontier_rows": len(frontier_rows),
            "defi_rows": len(defi_rows),
            "ok": all(row["ok"] for row in tau_rows),
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
