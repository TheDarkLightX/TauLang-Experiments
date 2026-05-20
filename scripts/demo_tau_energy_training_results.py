#!/usr/bin/env python3
"""Print a compact TauEnergy training demo from local result artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACTS = {
    "optimizer": Path("results/local/tau-energy/optimizer_workbench.json"),
    "measured": Path("results/local/tau-energy/measured_fragment_training_report.json"),
    "stress": Path("results/local/tau-energy/measured_fragment_stress_report.json"),
    "bdd": Path("results/local/tau-energy/ordered_bdd_curriculum_report.json"),
}


def load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optimizer", type=Path, default=DEFAULT_ARTIFACTS["optimizer"])
    parser.add_argument("--measured", type=Path, default=DEFAULT_ARTIFACTS["measured"])
    parser.add_argument("--stress", type=Path, default=DEFAULT_ARTIFACTS["stress"])
    parser.add_argument("--bdd", type=Path, default=DEFAULT_ARTIFACTS["bdd"])
    args = parser.parse_args()

    print("TauEnergy measured-training demo")
    print("Authority: model proposes route order; Tau and certificates decide validity.")

    optimizer = load(args.optimizer)
    if optimizer:
        accepted = optimizer.get("accepted_optimization", {})
        print_section("Genuine Optimization")
        print(f"route: {accepted.get('route')}")
        print(f"solver-call reduction: {accepted.get('solver_call_reduction')}")
        print(f"invalid accepts: {optimizer.get('wes_schedule', {}).get('invalid_accept_count')}")

    measured = load(args.measured)
    if measured:
        print_section("Measured Route Training")
        print(f"checked cases: {measured.get('valid_tau_checked_example_count')}")
        print(f"failed checks: {measured.get('failed_check_count')}")
        print(f"learned top-1: {measured.get('fitted_eval_test', {}).get('top1_oracle_route_rate')}")
        print(f"hand baseline top-1: {measured.get('hand_eval_test', {}).get('top1_oracle_route_rate')}")
        print(f"invalid accepts: {measured.get('fitted_eval_test', {}).get('invalid_accept_count')}")

    stress = load(args.stress)
    if stress:
        print_section("Stress Evidence")
        print(f"cross-seed fitted top-1: {stress.get('cross_seed', {}).get('fitted_top1')}")
        print(f"family-holdout fitted top-1: {stress.get('family_holdout', {}).get('fitted_top1')}")
        weak = sorted(
            [
                row for row in stress.get("family_holdout", {}).get("families", [])
                if row.get("status") == "evaluated"
            ],
            key=lambda row: float(row.get("fitted_top1", 0.0)),
        )
        if weak:
            row = weak[0]
            print(f"weakest family: {row.get('family')} top-1={row.get('fitted_top1')}")

    bdd = load(args.bdd)
    if bdd:
        print_section("Ordered-BDD Curriculum")
        for row in bdd.get("curriculum_steps", []):
            print(
                "bdd_train_cases="
                f"{row.get('bdd_train_case_count')} "
                f"top1={row.get('fitted_top1')} "
                f"mean_calls={row.get('fitted_mean_calls_to_best_route')}"
            )
        print(f"best: {bdd.get('improvement')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
