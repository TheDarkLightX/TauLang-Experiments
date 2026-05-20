#!/usr/bin/env python3
"""Build or verify the public TauEnergy site snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.public_snapshot import (
    build_public_site_snapshot,
    public_site_snapshot_summary,
    verify_public_site_snapshot,
)


DEFAULT_ARTIFACTS = {
    "optimizer": Path("results/local/tau-energy/optimizer_workbench.json"),
    "measured": Path("results/local/tau-energy/measured_fragment_training_report.json"),
    "stress": Path("results/local/tau-energy/measured_fragment_stress_report.json"),
    "bdd": Path("results/local/tau-energy/ordered_bdd_curriculum_report.json"),
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optimizer", type=Path, default=DEFAULT_ARTIFACTS["optimizer"])
    parser.add_argument("--measured", type=Path, default=DEFAULT_ARTIFACTS["measured"])
    parser.add_argument("--stress", type=Path, default=DEFAULT_ARTIFACTS["stress"])
    parser.add_argument("--bdd", type=Path, default=DEFAULT_ARTIFACTS["bdd"])
    parser.add_argument("--out", type=Path, default=Path("docs/assets/tau-energy-demo-summary.json"))
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        data = load_json(args.verify)
        ok = verify_public_site_snapshot(data)
        print(json.dumps({"ok": ok, "summary": public_site_snapshot_summary(data)}, indent=2, sort_keys=True))
        return 0 if ok else 1

    snapshot = build_public_site_snapshot(
        optimizer=load_json(args.optimizer),
        measured=load_json(args.measured),
        stress=load_json(args.stress),
        bdd=load_json(args.bdd),
    )
    if not verify_public_site_snapshot(snapshot):
        print("generated snapshot failed public-site verification", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": args.out.as_posix(), **public_site_snapshot_summary(snapshot)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
