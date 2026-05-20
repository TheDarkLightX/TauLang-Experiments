#!/usr/bin/env python3
"""Build a grammar-versioned TauEnergy training bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.export import write_json
from tau_energy.training import DEFAULT_PROMPTS, build_training_bundle


def verify(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    ok = bool(
        data.get("schema") == "tau-energy-training-bundle-v1"
        and data.get("status") == "training_bundle_ready"
        and data.get("authority", {}).get("tau_energy_can_accept") is False
        and data.get("energy_training_row_count", 0) > 0
        and data.get("sft_row_count", 0) > 0
        and data.get("syntax_snapshot", {}).get("grammar_hash")
    )
    print(json.dumps({"ok": ok, "verified": path.as_posix()}, indent=2, sort_keys=True))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="append", dest="prompts", default=None)
    parser.add_argument("--syntax-limit", type=int)
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/training_bundle.json"))
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()

    if args.verify:
        return verify(args.verify)

    bundle = build_training_bundle(args.prompts or list(DEFAULT_PROMPTS), root=str(ROOT), syntax_limit=args.syntax_limit)
    write_json(args.out, bundle)
    print(json.dumps({
        "status": bundle["status"],
        "out": args.out.as_posix(),
        "grammar_hash": bundle["syntax_snapshot"]["grammar_hash"],
        "energy_training_row_count": bundle["energy_training_row_count"],
        "sft_row_count": bundle["sft_row_count"],
        "trained": bundle["fitted_energy_model"]["trained"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
