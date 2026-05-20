from __future__ import annotations

import json

from tau_energy import (
    AUTHORITY_BOUNDARY,
    TauProposalCandidate,
    build_proposal_packet,
    build_syntax_corpus,
    build_training_bundle,
    default_energy_model,
)


def test_authority_boundary_is_closed() -> None:
    assert AUTHORITY_BOUNDARY["llm_can_execute_tau"] is False
    assert AUTHORITY_BOUNDARY["tau_energy_can_accept"] is False
    assert AUTHORITY_BOUNDARY["tau_jepa_can_verify"] is False
    assert AUTHORITY_BOUNDARY["tau_verifier_or_receipt_required"] is True


def test_energy_penalizes_direct_authority_claim() -> None:
    model = default_energy_model()
    safe = TauProposalCandidate(
        candidate_id="safe",
        kind="verifier_plan",
        title="Receipt plan",
        text="Run Tau and record receipts.",
        features={"verifier_receipts": 0.9, "replay_cases": 0.8, "authority_overclaim": 0.0},
    )
    unsafe = TauProposalCandidate(
        candidate_id="unsafe",
        kind="anti_candidate",
        title="Model executes",
        text="Let the model execute Tau actions.",
        features={"authority_overclaim": 1.0, "tau_net_blast_radius": 0.8},
    )
    assert model.energy(safe) < model.energy(unsafe)
    assert model.rank([unsafe, safe])[0]["candidate_id"] == "safe"


def test_packet_contains_no_acceptance_label(tmp_path) -> None:
    packet = build_proposal_packet(
        "Can a chatbot do stuff for Tau Lang and Tau Net with TauEnergy?",
        root=str(tmp_path),
    )
    assert packet["status"] == "advisory_packet_ready"
    assert packet["authority"]["tau_energy_can_accept"] is False
    assert packet["authority"]["tau_jepa_can_verify"] is False
    assert all(row["label"] != "accepted" for row in packet["energy_ranking"])
    assert any(row["repair"] == "remove_model_authority_claim" for row in packet["repairs"])


def test_syntax_corpus_is_grammar_versioned(tmp_path) -> None:
    parser_dir = tmp_path / "external" / "tau-lang" / "parser"
    parser_dir.mkdir(parents=True)
    (parser_dir / "tau.tgf").write_text("claim := NAME\n", encoding="utf-8")
    corpus = build_syntax_corpus(tmp_path)
    assert corpus["snapshot"]["grammar_hash"] != "missing"
    assert corpus["row_count"] > 0
    assert all(row["grammar_hash"] == corpus["snapshot"]["grammar_hash"] for row in corpus["rows"])
    assert all(row["surface_syntax_check"]["ok"] for row in corpus["rows"])


def test_training_bundle_has_trainable_energy_and_sft_rows(tmp_path) -> None:
    bundle = build_training_bundle(["Train a custom LLM for Tau syntax drift."], root=str(tmp_path))
    assert bundle["status"] == "training_bundle_ready"
    assert bundle["fitted_energy_model"]["trained"] is True
    assert bundle["energy_training_row_count"] > 0
    assert bundle["sft_row_count"] > 0
    encoded = json.dumps(bundle)
    assert "/" + "home" + "/" not in encoded
    assert "tau_energy_can_accept" in encoded
