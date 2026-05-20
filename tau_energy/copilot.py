"""Local Tau proposal copilot packet builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import AUTHORITY_BOUNDARY, TauProposalCandidate, default_energy_model
from .jepa import default_jepa_model
from .syntax import build_tau_syntax_snapshot


@dataclass(frozen=True)
class ParsedIntent:
    prompt: str
    wants_training: bool
    mentions_tau_net: bool
    mentions_optimization: bool
    mentions_syntax_drift: bool
    mentions_chatbot: bool


def parse_intent(prompt: str) -> ParsedIntent:
    text = prompt.lower()
    return ParsedIntent(
        prompt=prompt.strip(),
        wants_training=any(token in text for token in ("train", "trained", "sft", "dataset", "synthetic")),
        mentions_tau_net="tau net" in text or "taunet" in text,
        mentions_optimization=any(token in text for token in ("optimize", "optimizer", "speedup", "route")),
        mentions_syntax_drift=any(token in text for token in ("syntax", "grammar", "changed", "drift")),
        mentions_chatbot=any(token in text for token in ("chat", "chatbot", "llm", "user talk")),
    )


def proposal_candidates(intent: ParsedIntent, grammar_hash: str) -> list[TauProposalCandidate]:
    syntax_match = 0.8 if grammar_hash != "missing" and not intent.mentions_syntax_drift else 0.35
    drift_risk = 0.25 if syntax_match >= 0.7 else 0.75
    candidates = [
        TauProposalCandidate(
            candidate_id="semantic_contract",
            kind="contract",
            title="Draft semantic contract",
            text=(
                "Translate the user request into assumptions, inputs, outputs, "
                "safety conditions, and replay obligations before writing Tau."
            ),
            features={
                "semantic_specificity": 0.85,
                "verifier_receipts": 0.3,
                "replay_cases": 0.55,
                "witness_schema_fields": 0.7,
                "syntax_snapshot_match": syntax_match,
                "grammar_drift_risk": drift_risk,
                "host_projection": 0.75,
                "counterexample_coverage": 0.6,
                "authority_overclaim": 0.0,
                "tau_net_blast_radius": 0.3,
                "governance_scope": 0.25,
                "training_traceability": 0.7,
            },
            evidence=("natural language prompt", "explicit assumption list"),
            assumptions=("The prompt is exploratory until Tau receipts exist.",),
        ),
        TauProposalCandidate(
            candidate_id="tau_sketch",
            kind="tau_sketch",
            title="Current-grammar Tau sketch",
            text=(
                "Render a Tau-like sketch from the semantic contract, bind it "
                "to the current grammar hash, then run the real Tau toolchain."
            ),
            features={
                "semantic_specificity": 0.65,
                "verifier_receipts": 0.15,
                "replay_cases": 0.3,
                "witness_schema_fields": 0.45,
                "syntax_snapshot_match": syntax_match,
                "grammar_drift_risk": drift_risk,
                "host_projection": 0.6,
                "counterexample_coverage": 0.35,
                "authority_overclaim": 0.0,
                "tau_net_blast_radius": 0.25,
                "governance_scope": 0.2,
                "training_traceability": 0.85,
            },
            evidence=("grammar snapshot", "surface syntax corpus"),
            assumptions=("Tau syntax changes invalidate older rendered examples.",),
        ),
        TauProposalCandidate(
            candidate_id="receipt_replay_plan",
            kind="verifier_plan",
            title="Tau receipt and replay plan",
            text=(
                "Generate positive and negative witness cases, run current Tau, "
                "and store the receipt with the grammar hash and command version."
            ),
            features={
                "semantic_specificity": 0.75,
                "verifier_receipts": 0.8,
                "replay_cases": 0.85,
                "witness_schema_fields": 0.8,
                "syntax_snapshot_match": syntax_match,
                "grammar_drift_risk": drift_risk * 0.6,
                "host_projection": 0.85,
                "counterexample_coverage": 0.85,
                "authority_overclaim": 0.0,
                "tau_net_blast_radius": 0.2,
                "governance_scope": 0.2,
                "training_traceability": 0.9,
            },
            evidence=("planned Tau receipt", "counterexample replay"),
        ),
        TauProposalCandidate(
            candidate_id="llm_training_lane",
            kind="training_lane",
            title="Grammar-versioned LLM training lane",
            text=(
                "Train a Tau-aware chat model on grammar-versioned examples, "
                "proposal packets, syntax repairs, and receipt explanations."
            ),
            features={
                "semantic_specificity": 0.7,
                "verifier_receipts": 0.35,
                "replay_cases": 0.55,
                "witness_schema_fields": 0.65,
                "syntax_snapshot_match": syntax_match,
                "grammar_drift_risk": drift_risk,
                "host_projection": 0.65,
                "counterexample_coverage": 0.65,
                "authority_overclaim": 0.0,
                "tau_net_blast_radius": 0.3,
                "governance_scope": 0.35,
                "training_traceability": 0.95 if intent.wants_training else 0.65,
            },
            evidence=("synthetic data generator", "grammar hash"),
        ),
    ]
    if intent.mentions_tau_net:
        candidates.append(
            TauProposalCandidate(
                candidate_id="tau_net_experiment_lane",
                kind="tau_net_proposal",
                title="Tau Net experiment lane",
                text=(
                    "Convert broad Tau Net ideas into bounded proposals with "
                    "experiment scope, rollback, governance review, and receipts."
                ),
                features={
                    "semantic_specificity": 0.6,
                    "verifier_receipts": 0.25,
                    "replay_cases": 0.45,
                    "witness_schema_fields": 0.55,
                    "syntax_snapshot_match": syntax_match,
                    "grammar_drift_risk": drift_risk,
                    "host_projection": 0.6,
                    "counterexample_coverage": 0.55,
                    "authority_overclaim": 0.15,
                    "tau_net_blast_radius": 0.8,
                    "governance_scope": 0.8,
                    "training_traceability": 0.75,
                },
                evidence=("bounded rollout rule", "rollback requirement"),
                assumptions=("Tau Net production proposals require separate governance authority.",),
            )
        )
    if "execute" in intent.prompt.lower() or "do stuff" in intent.prompt.lower():
        candidates.append(
            TauProposalCandidate(
                candidate_id="unsafe_direct_execution",
                kind="anti_candidate",
                title="Direct model execution claim",
                text="Let the chatbot or energy model execute Tau actions directly.",
                features={
                    "semantic_specificity": 0.3,
                    "verifier_receipts": 0.0,
                    "replay_cases": 0.0,
                    "witness_schema_fields": 0.0,
                    "syntax_snapshot_match": syntax_match,
                    "grammar_drift_risk": drift_risk,
                    "host_projection": 0.1,
                    "counterexample_coverage": 0.0,
                    "authority_overclaim": 1.0,
                    "tau_net_blast_radius": 0.8,
                    "governance_scope": 0.7,
                    "training_traceability": 0.2,
                },
                evidence=("negative control",),
            )
        )
    return candidates


def repair_rows(candidates: list[TauProposalCandidate]) -> list[dict[str, Any]]:
    repairs: list[dict[str, Any]] = []
    for candidate in candidates:
        f = candidate.features
        if f.get("verifier_receipts", 0.0) < 0.6:
            repairs.append({
                "candidate_id": candidate.candidate_id,
                "repair": "add_tau_receipt_gate",
                "reason": "candidate lacks enough deterministic receipt evidence",
            })
        if f.get("grammar_drift_risk", 0.0) > 0.6:
            repairs.append({
                "candidate_id": candidate.candidate_id,
                "repair": "regenerate_under_current_grammar_hash",
                "reason": "syntax drift risk is high",
            })
        if f.get("authority_overclaim", 0.0) > 0.2:
            repairs.append({
                "candidate_id": candidate.candidate_id,
                "repair": "remove_model_authority_claim",
                "reason": "models may propose only",
            })
    return repairs


def build_proposal_packet(prompt: str, *, root: str = ".") -> dict[str, Any]:
    intent = parse_intent(prompt)
    snapshot = build_tau_syntax_snapshot(root)
    candidates = proposal_candidates(intent, str(snapshot["grammar_hash"]))
    energy = default_energy_model()
    jepa = default_jepa_model()
    ranked = energy.rank(candidates)
    stress = jepa.rank(candidates)[:12]
    return {
        "schema": "tau-energy-proposal-packet-v1",
        "status": "advisory_packet_ready",
        "prompt": prompt,
        "parsed_intent": intent.__dict__,
        "syntax_snapshot": snapshot,
        "model_cards": {
            "tau_energy": energy.card(),
            "tau_jepa": jepa.card(),
        },
        "authority": AUTHORITY_BOUNDARY,
        "candidates": [candidate.canonical().__dict__ for candidate in candidates],
        "energy_ranking": ranked,
        "stress_matrix": stress,
        "repairs": repair_rows(candidates),
        "chat_reply": (
            "A chatbot can collect intent and draft proposals. TauEnergy ranks "
            "candidate work items. TauJEPA ranks likely future failures. Tau or "
            "receipt replay decides what is true."
        ),
        "next_checks": [
            "refresh Tau grammar snapshot",
            "generate syntax-bound examples",
            "run current Tau on proposed sketches",
            "store receipts beside training rows",
        ],
    }
