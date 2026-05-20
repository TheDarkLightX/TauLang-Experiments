from __future__ import annotations

import json
from pathlib import Path

from tau_energy import (
    AUTHORITY_BOUNDARY,
    SparseTauWorkload,
    TauProposalCandidate,
    build_fragment_training_report,
    build_measured_fragment_training_report,
    build_measured_fragment_stress_report,
    build_optimizer_workbench,
    build_optimizer_training_report,
    build_proposal_packet,
    build_syntax_corpus,
    build_training_bundle,
    default_energy_model,
    verify_fragment_training_report,
    verify_measured_fragment_training_report,
    verify_measured_fragment_stress_report,
    verify_optimizer_receipt,
    verify_optimizer_training_report,
)
from tau_energy.optimizer import (
    build_solve_command,
    expected_impacted,
    make_supports,
    optimizer_candidates,
    rank_optimization_candidates,
)
from tau_energy.syntax import live_tau_syntax_check


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


def test_live_tau_syntax_check_is_optional(tmp_path) -> None:
    missing = tmp_path / "tau"
    result = live_tau_syntax_check(missing, "(a & b != 0)")
    assert result["ok"] is None
    assert result["status"] == "not_run"


def test_optimizer_energy_ranks_indexed_route_first() -> None:
    workload = SparseTauWorkload(factors=24, variables=80, support_size=2, delta_size=1, seed=1701)
    ranking = rank_optimization_candidates(optimizer_candidates(workload))
    assert ranking[0]["candidate_id"] == "indexed_factor_solve"
    assert ranking[-1]["candidate_id"] == "unchecked_cached_answer_negative"


def test_optimizer_world_model_marks_impacted_factors() -> None:
    workload = SparseTauWorkload(factors=8, variables=16, support_size=2, delta_size=1, seed=1701)
    supports, delta = make_supports(workload)
    impacted, raw_hits = expected_impacted(supports, delta)
    assert len(supports) == workload.factors
    assert raw_hits >= len(impacted)
    assert build_solve_command(supports).startswith("solve --tau (")


def test_live_optimizer_workbench_receipt_if_tau_exists() -> None:
    tau_bin = Path("external/tau-lang/build-Release/tau")
    if not tau_bin.exists():
        return
    receipt = build_optimizer_workbench(tau_bin=tau_bin, timeout_s=120)
    assert verify_optimizer_receipt(receipt)
    accepted = receipt["accepted_optimization"]
    assert accepted["candidate_id"] == "indexed_factor_solve"
    assert accepted["solver_call_reduction"] > 1.0
    assert receipt["wes_schedule"]["invalid_accept_count"] == 0


def test_live_optimizer_training_report_if_tau_exists() -> None:
    tau_bin = Path("external/tau-lang/build-Release/tau")
    if not tau_bin.exists():
        return
    report = build_optimizer_training_report(tau_bin=tau_bin, timeout_s=120)
    assert verify_optimizer_training_report(report)
    assert report["fitted_model"]["trained"] is True
    assert report["training_row_count"] >= 18
    assert report["formula_corpus"]["formula_count"] >= 6
    assert "sparse_delta" in report["formula_corpus"]["fragment_counts"]
    assert report["fitted_eval"]["eligible_top1_useful_rate"] == 1.0
    assert report["fitted_eval"]["eligible_mean_calls_to_first_useful"] == 1.0
    assert report["fitted_eval"]["invalid_accept_count"] == 0
    assert (
        report["fitted_eval"]["no_useful_safe_top1_count"]
        == report["fitted_eval"]["no_useful_workload_count"]
    )


def test_live_fragment_training_report_if_tau_exists() -> None:
    tau_bin = Path("external/tau-lang/build-Release/tau")
    if not tau_bin.exists():
        return
    report = build_fragment_training_report(
        tau_bin=tau_bin,
        example_count=25,
        seed=20260521,
        timeout_s=10,
    )
    assert verify_fragment_training_report(report)
    assert report["valid_tau_checked_example_count"] == 25
    assert report["fitted_model"]["trained"] is True
    assert report["fitted_eval_test"]["invalid_accept_count"] == 0
    assert (
        report["fitted_eval_test"]["top1_oracle_route_rate"]
        >= report["hand_eval_test"]["top1_oracle_route_rate"]
    )


def test_live_measured_fragment_training_report_if_tau_exists() -> None:
    tau_bin = Path("external/tau-lang/build-Release/tau")
    if not tau_bin.exists():
        return
    report = build_measured_fragment_training_report(
        tau_bin=tau_bin,
        example_count=25,
        real_spec_limit=2,
        seed=20260523,
        tau_timeout_s=10,
        route_timeout_s=10,
    )
    assert verify_measured_fragment_training_report(report)
    assert report["valid_tau_checked_example_count"] == 27
    assert report["fitted_model"]["trained"] is True
    assert report["fitted_eval_test"]["invalid_accept_count"] == 0
    assert (
        report["fitted_eval_test"]["top1_oracle_route_rate"]
        >= report["hand_eval_test"]["top1_oracle_route_rate"]
    )


def test_live_measured_fragment_stress_report_if_tau_exists() -> None:
    tau_bin = Path("external/tau-lang/build-Release/tau")
    if not tau_bin.exists():
        return
    report = build_measured_fragment_stress_report(
        tau_bin=tau_bin,
        examples_per_seed=20,
        seeds=[20260524, 20260525],
        real_spec_limit=2,
        tau_timeout_s=10,
        route_timeout_s=10,
    )
    assert verify_measured_fragment_stress_report(report)
    assert report["cross_seed"]["seed_count"] == 2
    assert report["family_holdout"]["evaluated_family_count"] >= 4
    assert report["invalid_accept_count"] == 0
