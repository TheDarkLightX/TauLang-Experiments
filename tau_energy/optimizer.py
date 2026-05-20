"""TauEnergy-guided optimizer workbench for Tau developer experiments.

This module wraps one existing Tau optimization lane end to end: sparse
top-level conjunct formulas can be solved by rechecking only factors impacted
by a small variable delta. TauEnergy ranks the route claim, a WES-style
scheduler chooses check order, and live Tau diagnostics decide whether the
optimization claim is accepted.
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OPTIMIZER_RECEIPT_SCHEMA = "tau-energy-optimizer-workbench-v1"
INDEXED_FACTOR_LINE_RE = re.compile(r"^\[indexed_factor_solve\]\s+(?P<body>.*)$", re.MULTILINE)


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


def factor_expr(support: list[str]) -> str:
    term = support[0] if len(support) == 1 else "(" + " & ".join(support) + ")"
    return f"({term} != 0)"


def make_supports(workload: SparseTauWorkload) -> tuple[list[list[str]], list[str]]:
    rng = random.Random(workload.seed)
    variables = [f"v{i}" for i in range(workload.variables)]
    supports = [sorted(rng.sample(variables, workload.support_size)) for _ in range(workload.factors)]
    delta = sorted(rng.sample(variables, workload.delta_size))
    return supports, delta


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


def optimizer_candidates(workload: SparseTauWorkload) -> list[OptimizerCandidate]:
    sparsity = 1.0 - min(1.0, workload.delta_size / max(1.0, float(workload.variables)))
    factor_pressure = min(1.0, workload.factors / 24.0)
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
            },
        ),
    ]


def optimization_energy(candidate: OptimizerCandidate) -> float:
    f = candidate.features
    energy = 3.0
    energy -= 1.4 * f["support_sparsity"]
    energy -= 1.1 * f["factorization"]
    energy -= 1.3 * f["expected_reduction"]
    energy -= 0.7 * f["validation_present"]
    energy += 4.5 * f["unsafe_skip_validation"]
    energy += 0.3 * f["tau_receipt_required"]
    return round(energy, 6)


def rank_optimization_candidates(candidates: list[OptimizerCandidate]) -> list[dict[str, Any]]:
    rows = [
        {
            "candidate_id": candidate.candidate_id,
            "route": candidate.route,
            "title": candidate.title,
            "claim": candidate.claim,
            "features": candidate.features,
            "energy": optimization_energy(candidate),
        }
        for candidate in candidates
    ]
    rows.sort(key=lambda row: (float(row["energy"]), str(row["candidate_id"])))
    return rows


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
    return {
        "status": "passed" if claim_ok else "failed",
        "ok": claim_ok,
        "fields": fields,
        "full_solve_count": full_count,
        "indexed_solve_count": indexed_count,
        "solver_call_reduction": round(full_count / indexed_count, 3),
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
    return {
        "schema": "tau-spec-world-model-v1",
        "kind": "sparse_conjunct_factor_graph",
        "workload": workload.__dict__,
        "solve_command_preview": command[:240] + ("..." if len(command) > 240 else ""),
        "delta_variables": delta,
        "factor_count": len(supports),
        "impacted_factor_indexes": impacted,
        "impacted_factor_count": len(impacted),
        "unimpacted_factor_count": len(supports) - len(impacted),
        "raw_index_hits": raw_hits,
        "support_graph": support_graph,
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
    candidates = optimizer_candidates(selected)
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


def dumps_receipt(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
