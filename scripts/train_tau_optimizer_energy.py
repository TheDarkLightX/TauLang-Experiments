#!/usr/bin/env python3
"""Train and evaluate a tiny TauEnergy route ranker from live Tau labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.optimizer import (
    build_optimizer_training_report,
    dumps_receipt,
    training_report_summary,
    verify_optimizer_training_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/optimizer_training_report.json"))
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = json.loads(args.verify.read_text(encoding="utf-8"))
        ok = verify_optimizer_training_report(data)
        print(json.dumps({"ok": ok, "summary": training_report_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    report = build_optimizer_training_report(
        tau_bin=args.tau_bin,
        timeout_s=args.timeout_s,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps_receipt(report), encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **training_report_summary(report)}, indent=2, sort_keys=True))
    return 0 if verify_optimizer_training_report(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
