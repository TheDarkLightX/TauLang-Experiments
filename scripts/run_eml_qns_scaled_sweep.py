#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from run_eml_qns_llm_memory_demo import (
    DEFAULT_TAU_BIN,
    ParseError,
    build_prompt,
    call_ollama,
    extract_json_object,
    parse_tree_expr,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROPOSAL_OUT = ROOT / "results" / "local" / "eml-qns-scaled-sweep-proposals.json"
DEFAULT_RECEIPT_OUT = ROOT / "results" / "local" / "eml-qns-scaled-sweep-receipt.json"
DEFAULT_REPORT_OUT = ROOT / "results" / "local" / "eml-qns-scaled-sweep-receipt.md"


def report_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def canonical_expr(expr: Any) -> tuple[str | None, str | None]:
    if not isinstance(expr, str):
        return None, "expr is not a string"
    try:
        return parse_tree_expr(expr).pretty(), None
    except ParseError as exc:
        return None, str(exc)


def add_candidate(
    candidates: list[dict[str, Any]],
    seen: set[tuple[str, str]],
    rejects: list[dict[str, Any]],
    item: dict[str, Any],
    *,
    origin: str,
    source_round: int | None = None,
) -> None:
    target = item.get("target")
    expr = item.get("expr")
    if target not in {"exp(x)", "ln(x)", "exp(exp(x))"}:
        rejects.append(
            {
                "origin": origin,
                "source_round": source_round,
                "target": target,
                "expr": expr,
                "reason": "unsupported target",
            }
        )
        return
    canonical, error = canonical_expr(expr)
    if canonical is None:
        rejects.append(
            {
                "origin": origin,
                "source_round": source_round,
                "target": target,
                "expr": expr,
                "reason": error,
            }
        )
        return
    key = (str(target), canonical)
    if key in seen:
        return
    seen.add(key)
    candidates.append(
        {
            "target": target,
            "origin": origin,
            "expr": canonical,
            "note": str(item.get("note", "") or f"deduped from {origin}"),
            "source_round": source_round,
        }
    )


def novelty_prompt(round_index: int, rounds: int, candidate_count: int, seen: set[tuple[str, str]]) -> str:
    by_target: dict[str, list[str]] = {"exp(x)": [], "ln(x)": [], "exp(exp(x))": []}
    for target, expr in sorted(seen):
        if target in by_target:
            by_target[target].append(expr)
    avoid_lines = []
    for target, exprs in by_target.items():
        shown = ", ".join(exprs[-12:]) if exprs else "(none yet)"
        avoid_lines.append(f"- {target}: {shown}")
    return (
        build_prompt(candidate_count)
        + "\n"
        + f"This is sweep round {round_index} of {rounds}.\n"
        + "Prefer candidates that are syntactically different from previous candidates.\n"
        + "Do not include unsupported constants or operators. The only terminals are x and 1.\n"
        + "Avoid these canonical expressions when possible:\n"
        + "\n".join(avoid_lines)
        + "\n"
    )


def read_mlx_candidates(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for target, result in data.get("results", {}).items():
        if target == "x":
            continue
        for key in ("first_fit_expr", "best_expr"):
            expr = result.get(key)
            if expr:
                rows.append(
                    {
                        "target": target,
                        "origin": "mlx_depth4",
                        "expr": expr,
                        "note": f"{key} from {report_path(path)}",
                    }
                )
    return rows


def run_gate(args: argparse.Namespace, proposal_path: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_eml_qns_llm_memory_demo.py"),
        "--tau-bin",
        str(args.tau_bin),
        "--llm-output",
        str(proposal_path),
        "--tau-timeout-s",
        str(args.tau_timeout_s),
        "--out",
        str(args.receipt_out),
        "--report-out",
        str(args.report_out),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    verify_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "verify_eml_qns_memory_receipt.py"),
        "--receipt",
        str(args.receipt_out),
        "--proposal-file",
        str(proposal_path),
        "--self-test",
    ]
    subprocess.run(verify_cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deduped multi-round EML/qNS proposal sweep.")
    parser.add_argument("--model", default=os.environ.get("QNS_LOCAL_MODEL", "qwen3.6:35b"))
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--candidate-count", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.35)
    parser.add_argument("--temperature-step", type=float, default=0.05)
    parser.add_argument("--num-predict", type=int, default=4096)
    parser.add_argument("--num-gpu", type=int, default=999)
    parser.add_argument("--ollama-url", default=os.environ.get("QNS_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"))
    parser.add_argument("--ollama-timeout-s", type=float, default=900.0)
    parser.add_argument("--include-mlx", type=Path, default=None)
    parser.add_argument("--proposal-out", type=Path, default=DEFAULT_PROPOSAL_OUT)
    parser.add_argument("--run-gate", action="store_true")
    parser.add_argument("--tau-bin", type=Path, default=DEFAULT_TAU_BIN)
    parser.add_argument("--tau-timeout-s", type=float, default=30.0)
    parser.add_argument("--receipt-out", type=Path, default=DEFAULT_RECEIPT_OUT)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()
    if args.rounds < 1:
        raise SystemExit("--rounds must be positive")
    if args.candidate_count < 1:
        raise SystemExit("--candidate-count must be positive")

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    rejects: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []

    if args.include_mlx is not None:
        for item in read_mlx_candidates(args.include_mlx):
            add_candidate(candidates, seen, rejects, item, origin="mlx_depth4")

    for round_index in range(1, args.rounds + 1):
        temperature = args.temperature + (round_index - 1) * args.temperature_step
        prompt = novelty_prompt(round_index, args.rounds, args.candidate_count, seen)
        model_meta = call_ollama(
            args.model,
            prompt,
            url=args.ollama_url,
            timeout_s=args.ollama_timeout_s,
            num_gpu=args.num_gpu,
            num_predict=args.num_predict,
            temperature=temperature,
        )
        try:
            data = extract_json_object(str(model_meta["raw_response"]))
        except Exception as exc:
            rounds.append(
                {
                    "round": round_index,
                    "temperature": temperature,
                    "model": {k: v for k, v in model_meta.items() if k != "raw_response"},
                    "error": str(exc),
                    "accepted_new": 0,
                }
            )
            continue
        before = len(candidates)
        for item in data.get("candidates", []):
            if isinstance(item, dict):
                add_candidate(
                    candidates,
                    seen,
                    rejects,
                    item,
                    origin="local_llm_sweep",
                    source_round=round_index,
                )
        rounds.append(
            {
                "round": round_index,
                "temperature": temperature,
                "model": {k: v for k, v in model_meta.items() if k != "raw_response"},
                "raw_candidate_count": len(data.get("candidates", [])) if isinstance(data.get("candidates"), list) else None,
                "accepted_new": len(candidates) - before,
            }
        )

    proposal = {
        "schema": "eml_candidate_proposals_v1",
        "meta": {
            "generator": "scripts/run_eml_qns_scaled_sweep.py",
            "model": args.model,
            "rounds": rounds,
            "dedupe_key": "target + canonical EML expression",
            "rejects": rejects,
            "include_mlx": report_path(args.include_mlx) if args.include_mlx is not None else None,
        },
        "candidates": candidates,
    }
    proposal_out = args.proposal_out if args.proposal_out.is_absolute() else ROOT / args.proposal_out
    proposal_out.parent.mkdir(parents=True, exist_ok=True)
    proposal_out.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")

    summary = {
        "ok": True,
        "proposal_out": report_path(proposal_out),
        "candidate_count": len(candidates),
        "reject_count": len(rejects),
        "rounds": rounds,
    }
    print(json.dumps(summary, indent=2))
    if args.run_gate:
        run_gate(args, proposal_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
