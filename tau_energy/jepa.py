"""TauJEPA future-tension projections.

TauJEPA scores predictable future failure modes for a proposal. It is an
advisory world-model style ranker. Tau receipts remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .core import TauProposalCandidate, canonical_features


@dataclass(frozen=True)
class StressScenario:
    scenario_id: str
    title: str
    trigger: str
    checks: tuple[str, ...]
    base_risk: float


SCENARIOS: tuple[StressScenario, ...] = (
    StressScenario(
        "syntax_drift_after_tau_grammar_change",
        "Syntax drift after Tau grammar change",
        "A generated sketch was trained against an older grammar snapshot.",
        ("refresh grammar hash", "rerun syntax corpus", "reject stale syntax rows"),
        0.82,
    ),
    StressScenario(
        "semantic_drift_under_ambiguous_intent",
        "Semantic drift under ambiguous intent",
        "The chat request lacks a precise semantic contract.",
        ("extract assumptions", "add counterexample witnesses", "human review"),
        0.68,
    ),
    StressScenario(
        "missing_witness_field_rejects",
        "Missing witness field rejects",
        "The verifier cannot replay a proposed outcome from the witness schema.",
        ("require witness schema", "replay positive and negative cases"),
        0.74,
    ),
    StressScenario(
        "governance_authority_overclaim",
        "Governance authority overclaim",
        "The proposal claims execution or acceptance authority for a model.",
        ("strip execution claim", "route through Tau or governance receipt"),
        0.95,
    ),
    StressScenario(
        "tau_net_blast_radius_escape",
        "Tau Net blast-radius escape",
        "A broad Tau Net proposal is missing a bounded rollout rule.",
        ("scope to experiment lane", "add rollback and receipt gate"),
        0.78,
    ),
    StressScenario(
        "training_data_stale_after_syntax_update",
        "Training data stale after syntax update",
        "The custom LLM or energy model was trained before the grammar changed.",
        ("record grammar hash", "invalidate stale rows", "regenerate synthetic data"),
        0.88,
    ),
)


@dataclass(frozen=True)
class TauJepaModel:
    model_id: str = "tau-jepa-deterministic-v0"

    def tension(self, candidate: TauProposalCandidate, scenario: StressScenario) -> float:
        f = canonical_features(candidate.features)
        risk = scenario.base_risk
        if "syntax" in scenario.scenario_id:
            risk += 0.35 * f["grammar_drift_risk"] - 0.2 * f["syntax_snapshot_match"]
        if "semantic" in scenario.scenario_id:
            risk += 0.3 * (1.0 - f["semantic_specificity"]) - 0.2 * f["counterexample_coverage"]
        if "witness" in scenario.scenario_id:
            risk += 0.3 * (1.0 - f["witness_schema_fields"]) - 0.15 * f["replay_cases"]
        if "governance" in scenario.scenario_id:
            risk += 0.5 * f["authority_overclaim"] + 0.2 * f["governance_scope"]
        if "tau_net" in scenario.scenario_id:
            risk += 0.45 * f["tau_net_blast_radius"] + 0.15 * f["governance_scope"]
        if "training" in scenario.scenario_id:
            risk += 0.3 * (1.0 - f["training_traceability"]) + 0.2 * f["grammar_drift_risk"]
        return round(max(0.0, min(1.0, risk)), 6)

    def rank(self, candidates: list[TauProposalCandidate]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for candidate in candidates:
            for scenario in SCENARIOS:
                rows.append({
                    "candidate_id": candidate.candidate_id,
                    "scenario_id": scenario.scenario_id,
                    "title": scenario.title,
                    "trigger": scenario.trigger,
                    "tension": self.tension(candidate, scenario),
                    "checks": list(scenario.checks),
                })
        rows.sort(key=lambda row: (-float(row["tension"]), str(row["candidate_id"]), str(row["scenario_id"])))
        return rows

    def card(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "objective": "rank future stress scenarios for proposal review",
            "authority": "advisory only; Tau receipts decide semantic acceptance",
        }


def default_jepa_model() -> TauJepaModel:
    return TauJepaModel()
