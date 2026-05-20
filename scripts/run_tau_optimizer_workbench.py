#!/usr/bin/env python3
"""Run the TauEnergy optimizer workbench end to end."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.optimizer import (
    SparseTauWorkload,
    build_optimizer_workbench,
    dumps_receipt,
    receipt_summary,
    verify_optimizer_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/optimizer_workbench.json"))
    parser.add_argument("--factors", type=int, default=24)
    parser.add_argument("--variables", type=int, default=80)
    parser.add_argument("--support-size", type=int, default=2)
    parser.add_argument("--delta-size", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = json.loads(args.verify.read_text(encoding="utf-8"))
        ok = verify_optimizer_receipt(data)
        print(json.dumps({"ok": ok, "summary": receipt_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    workload = SparseTauWorkload(
        factors=args.factors,
        variables=args.variables,
        support_size=args.support_size,
        delta_size=args.delta_size,
        seed=args.seed,
    )
    receipt = build_optimizer_workbench(
        tau_bin=args.tau_bin,
        workload=workload,
        timeout_s=args.timeout_s,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dumps_receipt(receipt), encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **receipt_summary(receipt)}, indent=2, sort_keys=True))
    return 0 if verify_optimizer_receipt(receipt) else 1


if __name__ == "__main__":
    raise SystemExit(main())
