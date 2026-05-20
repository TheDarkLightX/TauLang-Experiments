"""TauEnergy-guided optimizer workbench for Tau developer experiments.

This module wraps one existing Tau optimization lane end to end: sparse
top-level conjunct formulas can be solved by rechecking only factors impacted
by a small variable delta. TauEnergy ranks the route claim, a WES-style
scheduler chooses check order, and live Tau diagnostics decide whether the
optimization claim is accepted.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OPTIMIZER_RECEIPT_SCHEMA = "tau-energy-optimizer-workbench-v1"
OPTIMIZER_TRAINING_REPORT_SCHEMA = "tau-energy-optimizer-training-report-v1"
INDEXED_FACTOR_LINE_RE = re.compile(r"^\[indexed_factor_solve\]\s+(?P<body>.*)$", re.MULTILINE)
OPTIMIZER_FEATURE_NAMES: tuple[str, ...] = (
    "support_sparsity",
    "factorization",
    "tau_receipt_required",
    "expected_reduction",
    "validation_present",
    "unsafe_skip_validation",
    "impact_ratio",
    "saved_factor_ratio",
    "full_solver_pressure",
    "nonzero_impact",
    "noop_update",
)
DEFAULT_OPTIMIZER_WEIGHTS: dict[str, float] = {
    "support_sparsity": -1.4,
    "factorization": -1.1,
    "tau_receipt_required": 0.3,
    "expected_reduction": -1.3,
    "validation_present": -0.7,
    "unsafe_skip_validation": 4.5,
    "impact_ratio": 1.6,
    "saved_factor_ratio": -1.2,
    "full_solver_pressure": -0.7,
    "nonzero_impact": -0.5,
    "noop_update": 2.0,
}


@dataclass(frozen=True)
class SparseTauWorkload:
    name: str = "tau_energy_sparse_24_delta1"
    factors: int = 24
    variables: int = 80
    support_size: int = 2
    delta_size: int = 1
    seed: int = 1701


@dataclass(frozen=True)
class OptimizerCandidate:
    candidate_id: str
    route: str
    title: str
    claim: str
    features: dict[str, float]


@dataclass(frozen=True)
class OptimizerEnergyModel:
    weights: dict[str, float]
    bias: float = 3.0
    model_id: str = "tau-optimizer-energy-hand-v0"
    trained: bool = False
    training_rows: int = 0

    def energy(self, candidate: OptimizerCandidate | dict[str, Any]) -> float:
        features = optimizer_feature_vector(candidate.features if isinstance(candidate, OptimizerCandidate) else candidate)
        value = self.bias
        if features["unsafe_skip_validation"] >= 0.5:
            value += 3.0
        if features["noop_update"] >= 0.5:
            value += 1.5
        for name in OPTIMIZER_FEATURE_NAMES:
            value += self.weights.get(name, 0.0) * features[name]
        return round(value, 6)

    def rank(self, candidates: list[OptimizerCandidate]) -> list[dict[str, Any]]:
        rows = [
            {
                "candidate_id": candidate.candidate_id,
                "route": candidate.route,
                "title": candidate.title,
                "claim": candidate.claim,
                "features": optimizer_feature_vector(candidate.features),
                "energy": self.energy(candidate),
            }
            for candidate in candidates
        ]
        rows.sort(key=lambda row: (float(row["energy"]), str(row["candidate_id"])))
        return rows

    def card(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "trained": self.trained,
            "training_rows": self.training_rows,
            "feature_names": list(OPTIMIZER_FEATURE_NAMES),
            "feature_source": "formula fragment profile plus route safety metadata",
            "authority": "advisory route ordering only; live Tau decides labels",
        }


def factor_expr(support: list[str]) -> str:
    term = support[0] if len(support) == 1 else "(" + " & ".join(support) + ")"
    return f"({term} != 0)"


def make_supports(workload: SparseTauWorkload) -> tuple[list[list[str]], list[str]]:
    rng = random.Random(workload.seed)
    variables = [f"v{i}" for i in range(workload.variables)]
    supports = [sorted(rng.sample(variables, workload.support_size)) for _ in range(workload.factors)]
    delta = sorted(rng.sample(variables, workload.delta_size))
    return supports, delta


def optimizer_feature_vector(features: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name in OPTIMIZER_FEATURE_NAMES:
        value = float(features.get(name, 0.0))
        out[name] = min(1.0, max(0.0, value))
    return out


def build_solve_command(supports: list[list[str]]) -> str:
    return "solve --tau (" + " && ".join(factor_expr(support) for support in supports) + ")"


def expected_impacted(supports: list[list[str]], delta: list[str]) -> tuple[list[int], int]:
    delta_set = set(delta)
    impacted = [
        index
        for index, support in enumerate(supports)
        if delta_set.intersection(support)
    ]
    raw_hits = sum(1 for support in supports for var in delta if var in support)
    return impacted, raw_hits


def formula_fragment_profile(
    *,
    command: str,
    supports: list[list[str]],
    delta: list[str],
    impacted: list[int],
    raw_hits: int,
) -> dict[str, Any]:
    variables = sorted({var for support in supports for var in support})
    support_sizes = [len(support) for support in supports]
    factor_count = len(supports)
    impacted_count = len(impacted)
    impact_ratio = impacted_count / max(1.0, float(factor_count))
    mean_support = sum(support_sizes) / max(1.0, float(len(support_sizes)))
    fragment_tags = [
        "top_level_conjunction",
        "nonzero_factor_constraints",
        "finite_bitvector_atoms",
    ]
    if impact_ratio < 0.5:
        fragment_tags.append("sparse_delta")
    if impacted_count == 0:
        fragment_tags.append("no_impacted_factor")
    return {
        "schema": "tau-formula-fragment-profile-v1",
        "source": "synthetic_sparse_conjunct_tau_formula",
        "formula_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "formula_preview": command[:240] + ("..." if len(command) > 240 else ""),
        "fragment_tags": fragment_tags,
        "factor_count": factor_count,
        "distinct_variable_count": len(variables),
        "delta_variable_count": len(delta),
        "support_size_min": min(support_sizes) if support_sizes else 0,
        "support_size_max": max(support_sizes) if support_sizes else 0,
        "support_size_mean": round(mean_support, 6),
        "impacted_factor_count": impacted_count,
        "impact_ratio": round(impact_ratio, 6),
        "raw_index_hits": raw_hits,
        "feature_source": {
            "support_sparsity": "delta variables divided by distinct formula variables",
            "factorization": "top-level conjunct factor count",
            "impact_ratio": "impacted conjunct factors divided by total conjunct factors",
            "saved_factor_ratio": "unimpacted conjunct factors divided by total conjunct factors",
        },
        "syntax_drift_policy": "regenerate this profile and relabel rows with the current Tau binary",
    }


def optimizer_candidates(
    workload: SparseTauWorkload,
    *,
    impacted_count: int | None = None,
) -> list[OptimizerCandidate]:
    sparsity = 1.0 - min(1.0, workload.delta_size / max(1.0, float(workload.variables)))
    factor_pressure = min(1.0, workload.factors / 24.0)
    impact_ratio = (
        min(1.0, impacted_count / max(1.0, float(workload.factors)))
        if impacted_count is not None
        else min(1.0, workload.delta_size * workload.support_size / max(1.0, float(workload.variables)))
    )
    saved_factor_ratio = max(0.0, 1.0 - impact_ratio)
    full_solver_pressure = min(1.0, workload.factors / 96.0)
    nonzero_impact = 1.0 if impact_ratio > 0.0 else 0.0
    noop_update = 1.0 if impact_ratio == 0.0 else 0.0
    return [
        OptimizerCandidate(
            candidate_id="indexed_factor_solve",
            route="indexed_impacted_factor_solve",
            title="Use indexed impacted-factor solving",
            claim=(
                "For a sparse variable delta, solve only impacted conjunct "
                "factors and compare against a full factor scan."
            ),
            features={
                "support_sparsity": sparsity,
                "factorization": factor_pressure,
                "tau_receipt_required": 1.0,
                "expected_reduction": sparsity,
                "validation_present": 1.0,
                "unsafe_skip_validation": 0.0,
                "impact_ratio": impact_ratio,
                "saved_factor_ratio": saved_factor_ratio,
                "full_solver_pressure": full_solver_pressure,
                "nonzero_impact": nonzero_impact,
                "noop_update": noop_update,
            },
        ),
        OptimizerCandidate(
            candidate_id="full_factor_scan_control",
            route="full_factor_scan",
            title="Use full factor scan",
            claim="Solve every top-level conjunct factor, then compare with indexed selection.",
            features={
                "support_sparsity": sparsity,
                "factorization": factor_pressure,
                "tau_receipt_required": 1.0,
                "expected_reduction": 0.0,
                "validation_present": 1.0,
                "unsafe_skip_validation": 0.0,
                "impact_ratio": 1.0,
                "saved_factor_ratio": 0.0,
                "full_solver_pressure": full_solver_pressure,
                "nonzero_impact": 1.0,
                "noop_update": 0.0,
            },
        ),
        OptimizerCandidate(
            candidate_id="unchecked_cached_answer_negative",
            route="unchecked_cache_reuse",
            title="Reuse cached answer without Tau validation",
            claim="Skip the full scan and trust cached factor status.",
            features={
                "support_sparsity": sparsity,
                "factorization": factor_pressure,
                "tau_receipt_required": 1.0,
                "expected_reduction": 1.0,
                "validation_present": 0.0,
                "unsafe_skip_validation": 1.0,
                "impact_ratio": impact_ratio,
                "saved_factor_ratio": saved_factor_ratio,
                "full_solver_pressure": full_solver_pressure,
                "nonzero_impact": nonzero_impact,
                "noop_update": noop_update,
            },
        ),
    ]


def optimization_energy(candidate: OptimizerCandidate) -> float:
    return default_optimizer_energy_model().energy(candidate)


def rank_optimization_candidates(candidates: list[OptimizerCandidate]) -> list[dict[str, Any]]:
    return default_optimizer_energy_model().rank(candidates)


def default_optimizer_energy_model() -> OptimizerEnergyModel:
    return OptimizerEnergyModel(weights=dict(DEFAULT_OPTIMIZER_WEIGHTS))


def parse_indexed_factor_line(stderr: str) -> dict[str, str]:
    match = INDEXED_FACTOR_LINE_RE.search(stderr)
    if not match:
        raise AssertionError("Tau did not emit an [indexed_factor_solve] diagnostic line")
    fields: dict[str, str] = {}
    for part in match.group("body").split():
        if "=" not in part:
            raise AssertionError(f"malformed Tau diagnostic field: {part!r}")
        key, value = part.split("=", 1)
        fields[key] = value
    return fields


def run_indexed_factor_tau_check(
    *,
    tau_bin: Path,
    command: str,
    delta: list[str],
    timeout_s: int,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["TAU_INDEXED_FACTOR_SOLVE_STATS"] = "1"
    env["TAU_INDEXED_IMPACT_DELTA"] = ",".join(delta)
    proc = subprocess.run(
        [
            str(tau_bin),
            "--charvar",
            "false",
            "--severity",
            "error",
            "--color",
            "false",
            "--status",
            "false",
            "--evaluate",
            command,
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=timeout_s,
    )
    if proc.returncode != 0:
        return {
            "status": "tau_failed",
            "ok": False,
            "returncode": proc.returncode,
            "stderr_tail": proc.stderr[-1000:],
        }
    fields = parse_indexed_factor_line(proc.stderr)
    full_count = int(fields["full_solve_count"])
    indexed_count = int(fields["indexed_solve_count"])
    speedup = int(fields["speedup_x1000"]) / 1000.0
    claim_ok = (
        fields["scan_equals_indexed"] == "1"
        and int(fields["full_errors"]) == 0
        and int(fields["indexed_errors"]) == 0
        and 0 < indexed_count < full_count
    )
    reduction = round(full_count / indexed_count, 3) if indexed_count > 0 else None
    return {
        "status": "passed" if claim_ok else "failed",
        "ok": claim_ok,
        "fields": fields,
        "full_solve_count": full_count,
        "indexed_solve_count": indexed_count,
        "solver_call_reduction": reduction,
        "inprocess_solver_speedup": round(speedup, 3),
        "stdout_first_line": proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else "",
    }


def check_candidate(
    *,
    candidate: OptimizerCandidate,
    tau_bin: Path,
    command: str,
    delta: list[str],
    timeout_s: int,
) -> dict[str, Any]:
    if candidate.candidate_id == "unchecked_cached_answer_negative":
        return {
            "status": "rejected",
            "ok": False,
            "useful": False,
            "reason": "candidate lacks live Tau validation",
        }
    if candidate.candidate_id == "full_factor_scan_control":
        return {
            "status": "control",
            "ok": True,
            "useful": False,
            "reason": "full scan is the deterministic baseline, not the optimization",
        }
    if candidate.candidate_id != "indexed_factor_solve":
        return {
            "status": "unknown_candidate",
            "ok": False,
            "useful": False,
            "reason": candidate.candidate_id,
        }
    result = run_indexed_factor_tau_check(
        tau_bin=tau_bin,
        command=command,
        delta=delta,
        timeout_s=timeout_s,
    )
    return {
        **result,
        "useful": bool(result["ok"]),
        "reason": "live Tau confirmed scan/index parity and reduced solver calls",
    }


def build_world_model(
    *,
    workload: SparseTauWorkload,
    supports: list[list[str]],
    delta: list[str],
    impacted: list[int],
    raw_hits: int,
    command: str,
) -> dict[str, Any]:
    support_graph = [
        {
            "factor": f"f{index}",
            "support": support,
            "impacted_by_delta": index in set(impacted),
        }
        for index, support in enumerate(supports)
    ]
    profile = formula_fragment_profile(
        command=command,
        supports=supports,
        delta=delta,
        impacted=impacted,
        raw_hits=raw_hits,
    )
    return {
        "schema": "tau-spec-world-model-v1",
        "kind": "sparse_conjunct_factor_graph",
        "workload": workload.__dict__,
        "solve_command_preview": command[:240] + ("..." if len(command) > 240 else ""),
        "formula_profile": profile,
        "delta_variables": delta,
        "factor_count": len(supports),
        "impacted_factor_indexes": impacted,
        "impacted_factor_count": len(impacted),
        "unimpacted_factor_count": len(supports) - len(impacted),
        "raw_index_hits": raw_hits,
        "support_graph": support_graph,
        "state_space_summary": {
            "ambient_variable_count": workload.variables,
            "ambient_state_count_power_of_two": workload.variables,
            "touched_variable_count": len(delta),
            "touched_state_count_power_of_two": len(delta),
            "factor_state_spaces": [
                {
                    "factor": f"f{index}",
                    "local_variable_count": len(support),
                    "local_state_count_power_of_two": len(support),
                    "impacted": index in set(impacted),
                }
                for index, support in enumerate(supports)
            ],
        },
        "state_transitions": [
            {
                "from": "tau_formula",
                "to": "factor_graph",
                "meaning": "parse top-level conjunction into factor supports",
            },
            {
                "from": "factor_graph",
                "to": "delta_impact_index",
                "meaning": "find factors whose support intersects changed variables",
            },
            {
                "from": "delta_impact_index",
                "to": "route_candidates",
                "meaning": "construct full-scan, indexed-solve, and negative-control routes",
            },
            {
                "from": "route_candidates",
                "to": "tau_receipt",
                "meaning": "check selected route with live Tau diagnostics",
            },
        ],
        "discussion_handles": [
            "Which variables changed?",
            "Which factors are impacted?",
            "What is the fallback path?",
            "Does Tau report scan/index parity?",
            "How many solver calls were saved?",
        ],
        "discussion_trace": [
            {
                "question": "What part of the Tau state space changed?",
                "answer": f"The delta touches {len(delta)} variable(s): {', '.join(delta)}.",
            },
            {
                "question": "Why can the indexed route save work?",
                "answer": (
                    f"Only {len(impacted)} of {len(supports)} top-level factors intersect the delta; "
                    "the rest can be skipped for this impacted-factor check."
                ),
            },
            {
                "question": "What would make this unsafe?",
                "answer": "Accepting cached or indexed results without Tau's scan/index parity check.",
            },
        ],
    }


def build_wes_style_schedule(
    *,
    ranked_candidates: list[dict[str, Any]],
    check_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_useful_rank: int | None = None
    invalid_accept_count = 0
    for rank, row in enumerate(ranked_candidates, start=1):
        result = check_results[row["candidate_id"]]
        useful = bool(result.get("useful"))
        if useful and first_useful_rank is None:
            first_useful_rank = rank
        if row["candidate_id"] == "unchecked_cached_answer_negative" and result.get("ok"):
            invalid_accept_count += 1
        rows.append({
            "rank": rank,
            "candidate_id": row["candidate_id"],
            "energy": row["energy"],
            "checked": True,
            "check_status": result["status"],
            "useful": useful,
            "reason": result.get("reason"),
        })
    return {
        "schema": "tau-energy-wes-style-schedule-v1",
        "policy": "energy_ordered_checker_calls",
        "useful_at_1": first_useful_rank == 1,
        "calls_to_first_useful": first_useful_rank,
        "invalid_accept_count": invalid_accept_count,
        "rows": rows,
        "boundary": "WES-style scheduling changes checker order only; live Tau decides labels.",
    }


def build_optimizer_workbench(
    *,
    tau_bin: Path | str = Path("external/tau-lang/build-Release/tau"),
    workload: SparseTauWorkload | None = None,
    timeout_s: int = 120,
) -> dict[str, Any]:
    selected = workload or SparseTauWorkload()
    path = Path(tau_bin)
    if not path.exists():
        raise FileNotFoundError(f"Tau binary not found: {path}")
    supports, delta = make_supports(selected)
    impacted, raw_hits = expected_impacted(supports, delta)
    command = build_solve_command(supports)
    candidates = optimizer_candidates(selected, impacted_count=len(impacted))
    ranked = rank_optimization_candidates(candidates)
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    check_results = {
        row["candidate_id"]: check_candidate(
            candidate=by_id[row["candidate_id"]],
            tau_bin=path,
            command=command,
            delta=delta,
            timeout_s=timeout_s,
        )
        for row in ranked
    }
    schedule = build_wes_style_schedule(
        ranked_candidates=ranked,
        check_results=check_results,
    )
    accepted = [
        row
        for row in ranked
        if check_results[row["candidate_id"]].get("useful") is True
    ]
    accepted_candidate = accepted[0] if accepted else None
    optimization = check_results.get(accepted_candidate["candidate_id"], {}) if accepted_candidate else {}
    world_model = build_world_model(
        workload=selected,
        supports=supports,
        delta=delta,
        impacted=impacted,
        raw_hits=raw_hits,
        command=command,
    )
    status = "passed" if accepted_candidate and schedule["invalid_accept_count"] == 0 else "failed"
    return {
        "schema": OPTIMIZER_RECEIPT_SCHEMA,
        "status": status,
        "objective": "energy-ranked Tau optimizer route search with live Tau evidence",
        "authority": {
            "tau_energy_can_optimize_without_tau": False,
            "wes_can_accept_without_checker": False,
            "live_tau_required": True,
            "fallback_full_scan_available": True,
        },
        "workload": selected.__dict__,
        "world_model": world_model,
        "candidate_ranking": ranked,
        "check_results": check_results,
        "wes_schedule": schedule,
        "accepted_optimization": {
            "candidate_id": accepted_candidate["candidate_id"] if accepted_candidate else None,
            "route": accepted_candidate["route"] if accepted_candidate else None,
            "genuine_tau_optimization": bool(accepted_candidate),
            "live_tau_checked": bool(optimization.get("ok")),
            "solver_call_reduction": optimization.get("solver_call_reduction"),
            "inprocess_solver_speedup": optimization.get("inprocess_solver_speedup"),
        },
        "limits": [
            "This proves one feature-flagged optimization claim for the generated workload.",
            "It does not promote the route as a default Tau optimizer.",
            "A production route needs broader benchmark coverage and drift checks.",
        ],
    }


def verify_optimizer_receipt(data: dict[str, Any]) -> bool:
    if data.get("schema") != OPTIMIZER_RECEIPT_SCHEMA:
        return False
    if data.get("status") != "passed":
        return False
    accepted = data.get("accepted_optimization", {})
    if accepted.get("candidate_id") != "indexed_factor_solve":
        return False
    if accepted.get("live_tau_checked") is not True:
        return False
    if float(accepted.get("solver_call_reduction") or 0.0) <= 1.0:
        return False
    schedule = data.get("wes_schedule", {})
    if schedule.get("useful_at_1") is not True:
        return False
    if int(schedule.get("invalid_accept_count", -1)) != 0:
        return False
    indexed = data.get("check_results", {}).get("indexed_factor_solve", {})
    fields = indexed.get("fields", {})
    return bool(
        indexed.get("ok") is True
        and fields.get("scan_equals_indexed") == "1"
        and int(fields.get("full_errors", -1)) == 0
        and int(fields.get("indexed_errors", -1)) == 0
        and int(fields.get("full_solve_count", 0)) > int(fields.get("indexed_solve_count", 0)) > 0
    )


def optimizer_label(candidate_id: str, check_result: dict[str, Any]) -> str:
    if candidate_id == "unchecked_cached_answer_negative":
        return "reject_unsafe_no_validation"
    if bool(check_result.get("useful")):
        return "useful_verified_optimization"
    if candidate_id == "full_factor_scan_control":
        return "safe_baseline_control"
    return "not_useful"


def optimizer_target_energy(label: str) -> float:
    if label == "useful_verified_optimization":
        return 0.0
    if label == "safe_baseline_control":
        return 1.6
    if label == "not_useful":
        return 3.2
    return 5.0


def optimizer_training_weight(label: str) -> float:
    if label == "useful_verified_optimization":
        return 1.5
    if label == "not_useful":
        return 4.0
    if label == "reject_unsafe_no_validation":
        return 3.0
    return 1.0


def default_training_workloads() -> list[SparseTauWorkload]:
    return [
        SparseTauWorkload(
            name="train_sparse_12_delta1_seed1701",
            factors=12,
            variables=48,
            support_size=2,
            delta_size=1,
            seed=1701,
        ),
        SparseTauWorkload(
            name="train_sparse_24_delta1_seed1702",
            factors=24,
            variables=80,
            support_size=2,
            delta_size=1,
            seed=1702,
        ),
        SparseTauWorkload(
            name="train_sparse_24_delta2_seed1703",
            factors=24,
            variables=96,
            support_size=3,
            delta_size=2,
            seed=1703,
        ),
        SparseTauWorkload(
            name="train_sparse_48_delta2_seed1704",
            factors=48,
            variables=160,
            support_size=3,
            delta_size=2,
            seed=1704,
        ),
        SparseTauWorkload(
            name="train_sparse_48_delta4_seed1705",
            factors=48,
            variables=160,
            support_size=3,
            delta_size=4,
            seed=1705,
        ),
        SparseTauWorkload(
            name="train_dense_24_delta8_seed1706",
            factors=24,
            variables=48,
            support_size=3,
            delta_size=8,
            seed=1706,
        ),
    ]


def formula_corpus_summary(workload_receipts: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [
        receipt["formula_profile"]
        for receipt in workload_receipts
        if "formula_profile" in receipt
    ]
    fragment_counts: dict[str, int] = {}
    for profile in profiles:
        for tag in profile.get("fragment_tags", []):
            fragment_counts[tag] = fragment_counts.get(tag, 0) + 1
    hashes = sorted({str(profile["formula_sha256"]) for profile in profiles})
    return {
        "schema": "tau-formula-corpus-summary-v1",
        "formula_count": len(profiles),
        "unique_formula_count": len(hashes),
        "formula_sha256": hashes,
        "fragment_counts": dict(sorted(fragment_counts.items())),
        "feature_source": "formula fragment profile, generated delta, route safety metadata",
        "label_source": "live Tau indexed_factor_solve diagnostics",
        "route_families": [
            "indexed_impacted_factor_solve",
            "full_factor_scan",
            "unchecked_cache_reuse_negative_control",
        ],
        "syntax_drift_policy": "synthetic rows are disposable; regenerate and relabel after Tau syntax changes",
    }


def labeled_optimizer_rows_for_workload(
    *,
    tau_bin: Path,
    workload: SparseTauWorkload,
    timeout_s: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    supports, delta = make_supports(workload)
    impacted, raw_hits = expected_impacted(supports, delta)
    command = build_solve_command(supports)
    profile = formula_fragment_profile(
        command=command,
        supports=supports,
        delta=delta,
        impacted=impacted,
        raw_hits=raw_hits,
    )
    candidates = optimizer_candidates(workload, impacted_count=len(impacted))
    rows: list[dict[str, Any]] = []
    check_results: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        check = check_candidate(
            candidate=candidate,
            tau_bin=tau_bin,
            command=command,
            delta=delta,
            timeout_s=timeout_s,
        )
        check_results[candidate.candidate_id] = check
        label = optimizer_label(candidate.candidate_id, check)
        rows.append({
            "schema": "tau-optimizer-energy-training-row-v1",
            "workload": workload.__dict__,
            "candidate_id": candidate.candidate_id,
            "route": candidate.route,
            "features": optimizer_feature_vector(candidate.features),
            "formula_profile": profile,
            "feature_source": "candidate route features derived from the Tau formula fragment profile",
            "label": label,
            "target_energy": optimizer_target_energy(label),
            "training_weight": optimizer_training_weight(label),
            "tau_check": check,
            "world_summary": {
                "delta": delta,
                "factor_count": len(supports),
                "impacted_factor_count": len(impacted),
                "raw_index_hits": raw_hits,
            },
        })
    return rows, {
        "workload": workload.__dict__,
        "formula_profile": profile,
        "world_summary": {
            "delta": delta,
            "factor_count": len(supports),
            "impacted_factor_count": len(impacted),
            "raw_index_hits": raw_hits,
        },
        "check_results": check_results,
    }


def fit_optimizer_energy_model(
    rows: list[dict[str, Any]],
    *,
    epochs: int = 80,
    learning_rate: float = 0.05,
    l2: float = 0.001,
) -> OptimizerEnergyModel:
    weights = dict(DEFAULT_OPTIMIZER_WEIGHTS)
    bias = 3.0
    for _ in range(max(1, epochs)):
        for row in rows:
            features = optimizer_feature_vector(row["features"])
            target = float(row["target_energy"])
            weight = float(row.get("training_weight", 1.0))
            pred = bias + sum(weights[name] * features[name] for name in OPTIMIZER_FEATURE_NAMES)
            err = weight * (pred - target)
            bias -= learning_rate * err
            for name in OPTIMIZER_FEATURE_NAMES:
                weights[name] -= learning_rate * (err * features[name] + l2 * weights[name])
    return OptimizerEnergyModel(
        weights={name: round(weights[name], 6) for name in OPTIMIZER_FEATURE_NAMES},
        bias=round(bias, 6),
        model_id="tau-optimizer-energy-linear-fit-v0",
        trained=True,
        training_rows=len(rows),
    )


def evaluate_optimizer_model(
    *,
    model: OptimizerEnergyModel,
    workloads: list[SparseTauWorkload],
    training_by_workload: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    top1 = 0
    eligible_top1 = 0
    eligible_count = 0
    no_useful_count = 0
    no_useful_safe_top1 = 0
    calls_to_first_useful: list[int] = []
    eligible_calls_to_first_useful: list[int] = []
    invalid_accept_count = 0
    workload_reports: list[dict[str, Any]] = []
    for workload in workloads:
        rows = training_by_workload[workload.name]
        candidates = [
            OptimizerCandidate(
                candidate_id=row["candidate_id"],
                route=row["route"],
                title=row["candidate_id"],
                claim=row["label"],
                features=row["features"],
            )
            for row in rows
        ]
        labels = {row["candidate_id"]: row["label"] for row in rows}
        ranked = model.rank(candidates)
        first_useful = None
        for rank, row in enumerate(ranked, start=1):
            label = labels[row["candidate_id"]]
            if row["candidate_id"] == "unchecked_cached_answer_negative" and label != "reject_unsafe_no_validation":
                invalid_accept_count += 1
            if label == "useful_verified_optimization" and first_useful is None:
                first_useful = rank
        if first_useful == 1:
            top1 += 1
            eligible_top1 += 1
        if first_useful is not None:
            eligible_count += 1
            eligible_calls_to_first_useful.append(first_useful)
        else:
            no_useful_count += 1
            if labels[ranked[0]["candidate_id"]] == "safe_baseline_control":
                no_useful_safe_top1 += 1
        calls_to_first_useful.append(first_useful or len(ranked) + 1)
        workload_reports.append({
            "workload": workload.name,
            "top_candidate": ranked[0]["candidate_id"],
            "first_useful_rank": first_useful,
            "ranking": [
                {
                    "candidate_id": row["candidate_id"],
                    "energy": row["energy"],
                    "label": labels[row["candidate_id"]],
                }
                for row in ranked
            ],
        })
    count = len(workloads)
    return {
        "workload_count": count,
        "top1_useful_rate": round(top1 / count, 6) if count else 0.0,
        "eligible_workload_count": eligible_count,
        "eligible_top1_useful_rate": round(eligible_top1 / eligible_count, 6) if eligible_count else None,
        "mean_calls_to_first_useful": round(sum(calls_to_first_useful) / count, 6) if count else None,
        "eligible_mean_calls_to_first_useful": (
            round(sum(eligible_calls_to_first_useful) / eligible_count, 6)
            if eligible_count
            else None
        ),
        "max_calls_to_first_useful": max(calls_to_first_useful) if calls_to_first_useful else None,
        "no_useful_workload_count": no_useful_count,
        "no_useful_safe_top1_count": no_useful_safe_top1,
        "invalid_accept_count": invalid_accept_count,
        "workloads": workload_reports,
    }


def build_optimizer_training_report(
    *,
    tau_bin: Path | str = Path("external/tau-lang/build-Release/tau"),
    workloads: list[SparseTauWorkload] | None = None,
    timeout_s: int = 120,
) -> dict[str, Any]:
    path = Path(tau_bin)
    if not path.exists():
        raise FileNotFoundError(f"Tau binary not found: {path}")
    selected = workloads or default_training_workloads()
    rows: list[dict[str, Any]] = []
    workload_receipts: list[dict[str, Any]] = []
    rows_by_workload: dict[str, list[dict[str, Any]]] = {}
    for workload in selected:
        workload_rows, receipt = labeled_optimizer_rows_for_workload(
            tau_bin=path,
            workload=workload,
            timeout_s=timeout_s,
        )
        rows.extend(workload_rows)
        workload_receipts.append(receipt)
        rows_by_workload[workload.name] = workload_rows
    hand_model = default_optimizer_energy_model()
    fitted = fit_optimizer_energy_model(rows)
    hand_eval = evaluate_optimizer_model(
        model=hand_model,
        workloads=selected,
        training_by_workload=rows_by_workload,
    )
    fitted_eval = evaluate_optimizer_model(
        model=fitted,
        workloads=selected,
        training_by_workload=rows_by_workload,
    )
    live_useful = [
        row for row in rows
        if row["label"] == "useful_verified_optimization"
        and row["tau_check"].get("ok") is True
    ]
    return {
        "schema": OPTIMIZER_TRAINING_REPORT_SCHEMA,
        "status": "passed",
        "authority": {
            "trained_ranker_can_accept": False,
            "live_tau_required": True,
            "deterministic_fallback_required": True,
        },
        "training_status": "linear_ranker_fit_from_live_tau_labels",
        "training_row_count": len(rows),
        "workload_count": len(selected),
        "live_tau_useful_row_count": len(live_useful),
        "formula_corpus": formula_corpus_summary(workload_receipts),
        "label_counts": {
            label: sum(1 for row in rows if row["label"] == label)
            for label in sorted({row["label"] for row in rows})
        },
        "hand_model": hand_model.card() | {"weights": hand_model.weights, "bias": hand_model.bias},
        "fitted_model": fitted.card() | {"weights": fitted.weights, "bias": fitted.bias},
        "hand_eval": hand_eval,
        "fitted_eval": fitted_eval,
        "workload_receipts": workload_receipts,
        "training_rows": rows,
        "limits": [
            "This is a small live-Tau-labeled linear ranker, not a large neural EBRM.",
            "It trains route ordering only. Tau diagnostics decide whether a route claim is useful.",
            "More route families and harder negative controls are needed before promotion claims.",
        ],
    }


def verify_optimizer_training_report(data: dict[str, Any]) -> bool:
    if data.get("schema") != OPTIMIZER_TRAINING_REPORT_SCHEMA:
        return False
    if data.get("status") != "passed":
        return False
    if data.get("authority", {}).get("trained_ranker_can_accept") is not False:
        return False
    if int(data.get("training_row_count") or 0) <= 0:
        return False
    if int(data.get("live_tau_useful_row_count") or 0) <= 0:
        return False
    formula_corpus = data.get("formula_corpus", {})
    if int(formula_corpus.get("unique_formula_count") or 0) <= 0:
        return False
    fitted_eval = data.get("fitted_eval", {})
    no_useful = int(fitted_eval.get("no_useful_workload_count") or 0)
    no_useful_safe = int(fitted_eval.get("no_useful_safe_top1_count") or 0)
    return bool(
        fitted_eval.get("eligible_top1_useful_rate") == 1.0
        and int(fitted_eval.get("invalid_accept_count", -1)) == 0
        and float(fitted_eval.get("eligible_mean_calls_to_first_useful") or 999.0) <= 1.0
        and no_useful == no_useful_safe
    )


def receipt_summary(data: dict[str, Any]) -> dict[str, Any]:
    accepted = data.get("accepted_optimization", {})
    world = data.get("world_model", {})
    schedule = data.get("wes_schedule", {})
    return {
        "status": data.get("status"),
        "accepted_route": accepted.get("route"),
        "genuine_tau_optimization": accepted.get("genuine_tau_optimization"),
        "solver_call_reduction": accepted.get("solver_call_reduction"),
        "inprocess_solver_speedup": accepted.get("inprocess_solver_speedup"),
        "factor_count": world.get("factor_count"),
        "impacted_factor_count": world.get("impacted_factor_count"),
        "calls_to_first_useful": schedule.get("calls_to_first_useful"),
        "invalid_accept_count": schedule.get("invalid_accept_count"),
    }


def training_report_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": data.get("status"),
        "training_status": data.get("training_status"),
        "training_row_count": data.get("training_row_count"),
        "workload_count": data.get("workload_count"),
        "formula_count": data.get("formula_corpus", {}).get("formula_count"),
        "unique_formula_count": data.get("formula_corpus", {}).get("unique_formula_count"),
        "live_tau_useful_row_count": data.get("live_tau_useful_row_count"),
        "hand_top1_useful_rate": data.get("hand_eval", {}).get("top1_useful_rate"),
        "fitted_top1_useful_rate": data.get("fitted_eval", {}).get("top1_useful_rate"),
        "fitted_eligible_top1_useful_rate": data.get("fitted_eval", {}).get("eligible_top1_useful_rate"),
        "fitted_mean_calls_to_first_useful": data.get("fitted_eval", {}).get("mean_calls_to_first_useful"),
        "fitted_eligible_mean_calls_to_first_useful": data.get("fitted_eval", {}).get("eligible_mean_calls_to_first_useful"),
        "no_useful_workload_count": data.get("fitted_eval", {}).get("no_useful_workload_count"),
        "no_useful_safe_top1_count": data.get("fitted_eval", {}).get("no_useful_safe_top1_count"),
        "invalid_accept_count": data.get("fitted_eval", {}).get("invalid_accept_count"),
    }


def dumps_receipt(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
