"""Training-bundle builders for TauEnergy, TauJEPA, and Tau-aware chat data."""

from __future__ import annotations

import json
from typing import Any

from .copilot import build_proposal_packet
from .core import fit_energy_model
from .syntax import build_syntax_corpus


DEFAULT_PROMPTS: tuple[str, ...] = (
    "Let a user talk to a chatbot, propose Tau Language changes, and verify them with Tau.",
    "Optimize Tau Lang route proposals using receipts and counterexamples.",
    "Draft a Tau Net experiment proposal with rollback and governance checks.",
    "Generate Tau syntax examples after the grammar changes.",
)


def _training_rows_from_packet(packet: dict[str, Any]) -> list[dict[str, Any]]:
    labels = {row["candidate_id"]: row["label"] for row in packet["energy_ranking"]}
    rows: list[dict[str, Any]] = []
    for candidate in packet["candidates"]:
        rows.append({
            "features": candidate["features"],
            "label": labels[candidate["candidate_id"]],
            "candidate_id": candidate["candidate_id"],
            "source": "proposal_packet",
        })
    return rows


def _sft_rows(packet: dict[str, Any], syntax_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "messages": [
                {"role": "system", "content": "You draft Tau proposals. You never claim verifier authority."},
                {"role": "user", "content": packet["prompt"]},
                {"role": "assistant", "content": json.dumps({
                    "schema": packet["schema"],
                    "status": packet["status"],
                    "top_candidate": packet["energy_ranking"][0],
                    "authority": packet["authority"],
                    "next_checks": packet["next_checks"],
                }, sort_keys=True)},
            ],
            "metadata": {
                "kind": "prompt_to_tau_energy_packet",
                "grammar_hash": packet["syntax_snapshot"]["grammar_hash"],
            },
        }
    ]
    for row in syntax_rows:
        rows.append({
            "messages": [
                {"role": "system", "content": "You translate between Tau sketches, semantic IR, and counterexamples."},
                {"role": "user", "content": str(row["semantic_ir"])},
                {"role": "assistant", "content": json.dumps({
                    "tau_text": row["tau_text"],
                    "counterexamples": row["counterexamples"],
                    "authority": row["authority"],
                }, sort_keys=True)},
            ],
            "metadata": {
                "kind": "semantic_ir_to_tau_syntax_row",
                "grammar_hash": row["grammar_hash"],
                "template_id": row["template_id"],
            },
        })
    return rows


def build_training_bundle(
    prompts: list[str] | None = None,
    *,
    root: str = ".",
    syntax_limit: int | None = None,
) -> dict[str, Any]:
    selected_prompts = prompts or list(DEFAULT_PROMPTS)
    packets = [build_proposal_packet(prompt, root=root) for prompt in selected_prompts]
    syntax = build_syntax_corpus(root, limit=syntax_limit)
    training_rows: list[dict[str, Any]] = []
    sft_rows: list[dict[str, Any]] = []
    for packet in packets:
        training_rows.extend(_training_rows_from_packet(packet))
        sft_rows.extend(_sft_rows(packet, syntax["rows"]))
    fitted = fit_energy_model(training_rows)
    return {
        "schema": "tau-energy-training-bundle-v1",
        "status": "training_bundle_ready",
        "authority": packets[0]["authority"],
        "syntax_snapshot": syntax["snapshot"],
        "proposal_packet_count": len(packets),
        "energy_training_row_count": len(training_rows),
        "sft_row_count": len(sft_rows),
        "energy_training_rows": training_rows,
        "sft_rows": sft_rows,
        "fitted_energy_model": fitted.card() | {"weights": fitted.weights, "bias": fitted.bias},
        "packets": packets,
        "syntax_corpus": syntax,
    }
