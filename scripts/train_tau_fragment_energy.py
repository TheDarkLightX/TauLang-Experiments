#!/usr/bin/env python3
"""Train a TauEnergy fragment-route ranker from Tau-checked synthetic formulas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.fragment import (
    build_fragment_training_report,
    dumps_fragment_report,
    fragment_training_summary,
    verify_fragment_training_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--examples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260520)
    parser.add_argument("--timeout-s", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/fragment_training_report.json"))
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = json.loads(args.verify.read_text(encoding="utf-8"))
        ok = verify_fragment_training_report(data)
        print(json.dumps({"ok": ok, "summary": fragment_training_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    report = build_fragment_training_report(
        tau_bin=args.tau_bin,
        example_count=args.examples,
        seed=args.seed,
        timeout_s=args.timeout_s,
        root=ROOT,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps_fragment_report(report), encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **fragment_training_summary(report)}, indent=2, sort_keys=True))
    return 0 if verify_fragment_training_report(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
