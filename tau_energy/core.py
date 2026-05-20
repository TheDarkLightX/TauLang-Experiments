"""Deterministic and trainable TauEnergy rankers.

TauEnergy is an advisory ranking model over structured proposal candidates.
Lower energy means "check this earlier". The score is never an acceptance
predicate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


AUTHORITY_BOUNDARY: dict[str, bool] = {
    "llm_can_execute_tau": False,
    "tau_energy_can_accept": False,
    "tau_jepa_can_verify": False,
    "tau_verifier_or_receipt_required": True,
    "state_root_mutation_allowed": False,
}

FEATURE_NAMES: tuple[str, ...] = (
    "semantic_specificity",
    "verifier_receipts",
    "replay_cases",
    "witness_schema_fields",
    "syntax_snapshot_match",
    "grammar_drift_risk",
    "host_projection",
    "counterexample_coverage",
    "authority_overclaim",
    "tau_net_blast_radius",
    "governance_scope",
    "training_traceability",
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "semantic_specificity": -1.2,
    "verifier_receipts": -1.8,
    "replay_cases": -1.0,
    "witness_schema_fields": -0.8,
    "syntax_snapshot_match": -0.9,
    "grammar_drift_risk": 1.7,
    "host_projection": -0.6,
    "counterexample_coverage": -1.1,
    "authority_overclaim": 4.0,
    "tau_net_blast_radius": 2.2,
    "governance_scope": 0.8,
    "training_traceability": -0.7,
}


def _bounded(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number < 0.0:
        return 0.0
    if number > 1.0:
        return 1.0
    return number


def canonical_features(features: dict[str, Any] | None) -> dict[str, float]:
    raw = features or {}
    return {name: _bounded(raw.get(name, 0.0)) for name in FEATURE_NAMES}


@dataclass(frozen=True)
class TauProposalCandidate:
    candidate_id: str
    kind: str
    title: str
    text: str
    features: dict[str, float] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def canonical(self) -> "TauProposalCandidate":
        return TauProposalCandidate(
            candidate_id=self.candidate_id,
            kind=self.kind,
            title=self.title,
            text=self.text.strip(),
            features=canonical_features(self.features),
            evidence=tuple(str(item) for item in self.evidence),
            assumptions=tuple(str(item) for item in self.assumptions),
        )


@dataclass(frozen=True)
class TauEnergyModel:
    weights: dict[str, float]
    bias: float = 3.0
    model_id: str = "tau-energy-deterministic-v0"
    trained: bool = False
    training_rows: int = 0

    def energy(self, candidate: TauProposalCandidate | dict[str, Any]) -> float:
        if isinstance(candidate, TauProposalCandidate):
            features = candidate.canonical().features
        else:
            features = canonical_features(candidate.get("features", candidate))
        value = self.bias
        for name in FEATURE_NAMES:
            value += self.weights.get(name, 0.0) * features[name]
        return round(value, 6)

    def rank(self, candidates: Iterable[TauProposalCandidate]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for candidate in candidates:
            item = candidate.canonical()
            rows.append({
                "candidate_id": item.candidate_id,
                "kind": item.kind,
                "title": item.title,
                "energy": self.energy(item),
                "label": label_candidate(item),
                "features": item.features,
                "evidence": list(item.evidence),
                "assumptions": list(item.assumptions),
            })
        rows.sort(key=lambda row: (float(row["energy"]), str(row["candidate_id"])))
        return rows

    def card(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "trained": self.trained,
            "training_rows": self.training_rows,
            "objective": "rank proposal candidates for deterministic Tau checking",
            "authority": AUTHORITY_BOUNDARY,
            "lower_energy_means": "check earlier, not accept",
        }


def default_energy_model() -> TauEnergyModel:
    return TauEnergyModel(weights=dict(DEFAULT_WEIGHTS))


def label_candidate(candidate: TauProposalCandidate | dict[str, Any]) -> str:
    features = canonical_features(candidate.features if isinstance(candidate, TauProposalCandidate) else candidate.get("features", candidate))
    if features["authority_overclaim"] >= 0.65:
        return "reject_authority_overclaim"
    if features["tau_net_blast_radius"] >= 0.75 and features["verifier_receipts"] < 0.4:
        return "needs_governance_receipts"
    if features["grammar_drift_risk"] >= 0.7 and features["syntax_snapshot_match"] < 0.5:
        return "needs_current_grammar_check"
    if features["verifier_receipts"] >= 0.75 and features["replay_cases"] >= 0.65:
        return "ready_for_tau_review"
    return "needs_repair"


def quality_target(label: str) -> float:
    if label == "ready_for_tau_review":
        return 0.1
    if label in {"needs_repair", "needs_current_grammar_check", "needs_governance_receipts"}:
        return 1.5
    return 4.0


def fit_energy_model(
    rows: Iterable[dict[str, Any]],
    *,
    epochs: int = 12,
    learning_rate: float = 0.04,
    l2: float = 0.001,
) -> TauEnergyModel:
    """Fit a tiny deterministic linear scorer from verifier-style labels.

    This is intentionally simple so the experiment has a reproducible baseline
    before using a neural ranker. A later trained EBRM can replace the residual
    term while keeping the same authority boundary.
    """

    training = [
        {
            "features": canonical_features(row.get("features", {})),
            "target": quality_target(str(row.get("label") or "needs_repair")),
        }
        for row in rows
    ]
    weights = dict(DEFAULT_WEIGHTS)
    bias = 3.0
    for _ in range(max(1, epochs)):
        for row in training:
            pred = bias + sum(weights[name] * row["features"][name] for name in FEATURE_NAMES)
            err = pred - row["target"]
            bias -= learning_rate * err
            for name in FEATURE_NAMES:
                weights[name] -= learning_rate * (err * row["features"][name] + l2 * weights[name])
    return TauEnergyModel(
        weights={name: round(weights[name], 6) for name in FEATURE_NAMES},
        bias=round(bias, 6),
        model_id="tau-energy-linear-fit-v0",
        trained=True,
        training_rows=len(training),
    )
