"""License-safe public snapshots for the TauEnergy demo site."""

from __future__ import annotations

import json
from typing import Any


PUBLIC_SITE_SNAPSHOT_SCHEMA = "tau-energy-public-site-snapshot-v1"

FORBIDDEN_PUBLIC_KEYS = {
    "sample_receipts",
    "failed_checks",
    "formula",
    "command",
    "stderr_tail",
    "stdout_first_line",
    "tau_bin",
    "minisat_bin",
}

FORBIDDEN_PUBLIC_TEXT = (
    "/home/",
    "trevormoc",
    "ARISTOTLE_API_KEY",
    "sk-",
    "external/tau-lang",
)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _top1_range(value: Any) -> dict[str, float | None]:
    if not isinstance(value, dict):
        return {"min": None, "mean": None, "max": None}
    return {
        "min": value.get("min"),
        "mean": value.get("mean"),
        "max": value.get("max"),
    }


def _weakest_family(stress: dict[str, Any]) -> dict[str, Any]:
    families = [
        row for row in _dict(stress.get("family_holdout")).get("families", [])
        if isinstance(row, dict) and row.get("status") == "evaluated"
    ]
    if not families:
        return {"family": None, "top1": None}
    row = min(families, key=lambda item: _number(item.get("fitted_top1")))
    return {"family": row.get("family"), "top1": row.get("fitted_top1")}


def _curriculum_steps(bdd: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for row in bdd.get("curriculum_steps", []):
        if not isinstance(row, dict):
            continue
        steps.append({
            "bdd_train_case_count": row.get("bdd_train_case_count"),
            "bdd_test_case_count": row.get("bdd_test_case_count"),
            "fitted_top1": row.get("fitted_top1"),
            "mean_calls_to_best_route": row.get("fitted_mean_calls_to_best_route"),
            "invalid_accept_count": row.get("invalid_accept_count"),
        })
    return steps


def build_public_site_snapshot(
    *,
    optimizer: dict[str, Any],
    measured: dict[str, Any],
    stress: dict[str, Any],
    bdd: dict[str, Any],
) -> dict[str, Any]:
    accepted = _dict(optimizer.get("accepted_optimization"))
    measured_fit = _dict(measured.get("fitted_eval_test"))
    measured_hand = _dict(measured.get("hand_eval_test"))
    measured_improvement = _dict(measured.get("improvement"))
    stress_cross_seed = _dict(_dict(stress.get("cross_seed")).get("fitted_top1"))
    stress_family = _dict(_dict(stress.get("family_holdout")).get("fitted_top1"))
    bdd_improvement = _dict(bdd.get("improvement"))
    bdd_steps = _curriculum_steps(bdd)
    snapshot = {
        "schema": PUBLIC_SITE_SNAPSHOT_SCHEMA,
        "status": "passed",
        "title": "TauEnergy replayable training demo",
        "authority": {
            "tau_energy_can_accept": False,
            "wes_can_accept_without_checker": False,
            "tau_or_certificate_decides": True,
            "reader_replay_required_for_local_claims": True,
        },
        "license_boundary": {
            "redistributes_tau_source": False,
            "redistributes_tau_binary": False,
            "contains_tau_formula_corpus": False,
            "contains_public_metrics_only": True,
            "tau_source": "official IDNI repository, obtained by the reader after license review",
        },
        "replay": {
            "default_replay": "./scripts/run_tau_energy_training_demo.sh --accept-tau-license",
            "quick_mode": "./scripts/run_tau_energy_training_demo.sh --accept-tau-license --quick",
            "full_mode": "./scripts/run_tau_energy_training_demo.sh --accept-tau-license --full",
            "result_dir": "results/local/tau-energy",
            "site_snapshot": "docs/assets/tau-energy-demo-summary.json",
        },
        "source_artifact_schemas": {
            "optimizer": optimizer.get("schema"),
            "measured": measured.get("schema"),
            "stress": stress.get("schema"),
            "bdd": bdd.get("schema"),
        },
        "metrics": {
            "genuine_optimization": {
                "route": accepted.get("route"),
                "live_tau_checked": accepted.get("live_tau_checked"),
                "solver_call_reduction": accepted.get("solver_call_reduction"),
                "inprocess_solver_speedup": accepted.get("inprocess_solver_speedup"),
                "invalid_accept_count": _dict(optimizer.get("wes_schedule")).get("invalid_accept_count"),
            },
            "measured_training": {
                "checked_cases": measured.get("valid_tau_checked_example_count"),
                "failed_check_count": measured.get("failed_check_count"),
                "learned_top1": measured_fit.get("top1_oracle_route_rate"),
                "hand_top1": measured_hand.get("top1_oracle_route_rate"),
                "top1_delta": measured_improvement.get("test_top1_delta"),
                "mean_calls_delta": measured_improvement.get("test_mean_calls_delta"),
                "invalid_accept_count": measured_fit.get("invalid_accept_count"),
            },
            "stress": {
                "failed_check_count": stress.get("failed_check_count"),
                "invalid_accept_count": stress.get("invalid_accept_count"),
                "cross_seed_top1": _top1_range(stress_cross_seed),
                "family_holdout_top1": _top1_range(stress_family),
                "weakest_family": _weakest_family(stress),
            },
            "ordered_bdd_curriculum": {
                "base_examples": bdd.get("base_examples"),
                "bdd_pool_examples": bdd.get("bdd_pool_examples"),
                "failed_check_count": bdd.get("failed_check_count"),
                "invalid_accept_count": bdd.get("invalid_accept_count"),
                "first_top1": bdd_improvement.get("first_fitted_top1"),
                "best_top1": bdd_improvement.get("best_fitted_top1"),
                "best_bdd_train_case_count": bdd_improvement.get("best_bdd_train_case_count"),
                "last_minus_first_top1": bdd_improvement.get("last_minus_first_top1"),
                "steps": bdd_steps,
            },
        },
        "limits": [
            "The snapshot is a public metric summary, not a Tau source or binary distribution.",
            "The learned ranker proposes route order only.",
            "A reader must replay locally before treating any local performance number as current.",
        ],
    }
    return snapshot


def _has_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                return True
            if _has_forbidden_key(nested):
                return True
    elif isinstance(value, list):
        return any(_has_forbidden_key(item) for item in value)
    return False


def verify_public_site_snapshot(data: dict[str, Any]) -> bool:
    if data.get("schema") != PUBLIC_SITE_SNAPSHOT_SCHEMA:
        return False
    if data.get("status") != "passed":
        return False
    authority = _dict(data.get("authority"))
    if authority.get("tau_energy_can_accept") is not False:
        return False
    if authority.get("wes_can_accept_without_checker") is not False:
        return False
    if authority.get("tau_or_certificate_decides") is not True:
        return False
    license_boundary = _dict(data.get("license_boundary"))
    if license_boundary.get("redistributes_tau_source") is not False:
        return False
    if license_boundary.get("redistributes_tau_binary") is not False:
        return False
    if license_boundary.get("contains_public_metrics_only") is not True:
        return False
    metrics = _dict(data.get("metrics"))
    optimization = _dict(metrics.get("genuine_optimization"))
    measured = _dict(metrics.get("measured_training"))
    stress = _dict(metrics.get("stress"))
    bdd = _dict(metrics.get("ordered_bdd_curriculum"))
    if optimization.get("live_tau_checked") is not True:
        return False
    if _number(optimization.get("solver_call_reduction")) <= 1.0:
        return False
    for section in (optimization, measured, stress, bdd):
        if int(section.get("invalid_accept_count") or 0) != 0:
            return False
    for section in (measured, stress, bdd):
        if int(section.get("failed_check_count") or 0) != 0:
            return False
    if not bdd.get("steps"):
        return False
    if _has_forbidden_key(data):
        return False
    encoded = json.dumps(data, sort_keys=True)
    return not any(text in encoded for text in FORBIDDEN_PUBLIC_TEXT)


def public_site_snapshot_summary(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _dict(data.get("metrics"))
    optimization = _dict(metrics.get("genuine_optimization"))
    measured = _dict(metrics.get("measured_training"))
    bdd = _dict(metrics.get("ordered_bdd_curriculum"))
    return {
        "status": data.get("status"),
        "route": optimization.get("route"),
        "solver_call_reduction": optimization.get("solver_call_reduction"),
        "checked_cases": measured.get("checked_cases"),
        "learned_top1": measured.get("learned_top1"),
        "bdd_best_top1": bdd.get("best_top1"),
        "bdd_best_train_cases": bdd.get("best_bdd_train_case_count"),
    }
