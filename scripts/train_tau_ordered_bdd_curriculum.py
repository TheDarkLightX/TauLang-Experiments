#!/usr/bin/env python3
"""Run the ordered-BDD measured-route curriculum for TauEnergy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.fragment import (
    build_ordered_bdd_curriculum_report,
    dumps_fragment_report,
    ordered_bdd_curriculum_summary,
    verify_ordered_bdd_curriculum_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--base-examples", type=int, default=120)
    parser.add_argument("--bdd-pool-examples", type=int, default=96)
    parser.add_argument("--bdd-train-sizes", type=int, nargs="*", default=[0, 2, 4, 8, 16, 32])
    parser.add_argument("--real-spec-limit", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260526)
    parser.add_argument("--tau-timeout-s", type=int, default=10)
    parser.add_argument("--route-timeout-s", type=int, default=10)
    parser.add_argument("--minisat-bin", default=None)
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/ordered_bdd_curriculum_report.json"))
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = json.loads(args.verify.read_text(encoding="utf-8"))
        ok = verify_ordered_bdd_curriculum_report(data)
        print(json.dumps({"ok": ok, "summary": ordered_bdd_curriculum_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    report = build_ordered_bdd_curriculum_report(
        tau_bin=args.tau_bin,
        base_examples=args.base_examples,
        bdd_pool_examples=args.bdd_pool_examples,
        bdd_train_sizes=args.bdd_train_sizes,
        real_spec_limit=args.real_spec_limit,
        seed=args.seed,
        tau_timeout_s=args.tau_timeout_s,
        route_timeout_s=args.route_timeout_s,
        minisat_bin=args.minisat_bin,
        root=ROOT,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps_fragment_report(report), encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **ordered_bdd_curriculum_summary(report)}, indent=2, sort_keys=True))
    return 0 if verify_ordered_bdd_curriculum_report(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
