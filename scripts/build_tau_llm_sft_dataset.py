#!/usr/bin/env python3
"""Export Tau-aware chat SFT rows from the TauEnergy training bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tau_energy.export import write_json, write_jsonl
from tau_energy.training import DEFAULT_PROMPTS, build_training_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="append", dest="prompts", default=None)
    parser.add_argument("--format", choices=("json", "jsonl"), default="jsonl")
    parser.add_argument("--tau-bin", type=Path)
    parser.add_argument("--require-live-syntax", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("results/local/tau-energy/tau_llm_sft.jsonl"))
    args = parser.parse_args()

    bundle = build_training_bundle(
        args.prompts or list(DEFAULT_PROMPTS),
        root=str(ROOT),
        tau_bin=str(args.tau_bin) if args.tau_bin else None,
        require_live_syntax=args.require_live_syntax,
    )
    rows = bundle["sft_rows"]
    if args.format == "jsonl":
        write_jsonl(args.out, rows)
    else:
        write_json(args.out, {"schema": "tau-llm-sft-dataset-v1", "rows": rows})
    print(json.dumps({
        "status": "tau_llm_sft_dataset_ready",
        "out": args.out.as_posix(),
        "format": args.format,
        "row_count": len(rows),
        "grammar_hash": bundle["syntax_snapshot"]["grammar_hash"],
        "authority": bundle["authority"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
