"""TauEnergy advisory experiment package.

This package is a local research scaffold for ranking Tau Language proposals.
It never certifies Tau syntax, Tau semantics, governance actions, or Tau Net
state changes. Those decisions must stay with Tau, proof receipts, or another
deterministic verifier.
"""

from .core import (
    AUTHORITY_BOUNDARY,
    FEATURE_NAMES,
    TauProposalCandidate,
    TauEnergyModel,
    default_energy_model,
    fit_energy_model,
    label_candidate,
)
from .copilot import build_proposal_packet
from .jepa import TauJepaModel, default_jepa_model
from .optimizer import (
    SparseTauWorkload,
    build_optimizer_workbench,
    verify_optimizer_receipt,
)
from .syntax import build_syntax_corpus, build_tau_syntax_snapshot
from .training import build_training_bundle

__all__ = [
    "AUTHORITY_BOUNDARY",
    "FEATURE_NAMES",
    "TauProposalCandidate",
    "SparseTauWorkload",
    "TauEnergyModel",
    "TauJepaModel",
    "build_proposal_packet",
    "build_optimizer_workbench",
    "build_syntax_corpus",
    "build_tau_syntax_snapshot",
    "build_training_bundle",
    "default_energy_model",
    "default_jepa_model",
    "fit_energy_model",
    "label_candidate",
    "verify_optimizer_receipt",
]
