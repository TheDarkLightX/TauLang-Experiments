#!/usr/bin/env python3
"""Stress TauEnergy measured-route training across seeds and family holdouts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.fragment import (
    build_measured_fragment_stress_report,
    dumps_fragment_report,
    measured_fragment_stress_summary,
    verify_measured_fragment_stress_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--examples-per-seed", type=int, default=120)
    parser.add_argument("--seeds", type=int, nargs="*", default=[20260522, 20260523, 20260524])
    parser.add_argument("--real-spec-limit", type=int, default=4)
    parser.add_argument("--tau-timeout-s", type=int, default=10)
    parser.add_argument("--route-timeout-s", type=int, default=10)
    parser.add_argument("--minisat-bin", default=None)
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/measured_fragment_stress_report.json"))
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = json.loads(args.verify.read_text(encoding="utf-8"))
        ok = verify_measured_fragment_stress_report(data)
        print(json.dumps({"ok": ok, "summary": measured_fragment_stress_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    report = build_measured_fragment_stress_report(
        tau_bin=args.tau_bin,
        examples_per_seed=args.examples_per_seed,
        seeds=args.seeds,
        real_spec_limit=args.real_spec_limit,
        tau_timeout_s=args.tau_timeout_s,
        route_timeout_s=args.route_timeout_s,
        minisat_bin=args.minisat_bin,
        root=ROOT,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps_fragment_report(report), encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **measured_fragment_stress_summary(report)}, indent=2, sort_keys=True))
    return 0 if verify_measured_fragment_stress_report(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
