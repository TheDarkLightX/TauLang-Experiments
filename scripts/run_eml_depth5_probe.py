#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

from run_eml_depth4_probe import (
    TARGETS,
    Tree,
    build_layers_upto,
    corpus_counts,
    eml,
    max_abs_error,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "local" / "eml-depth5-probe.json"


def depth4_seed(lower3: list[Tree], seed_limit: int) -> list[Tree]:
    seed: list[Tree] = []
    for left in lower3:
        for right in lower3:
            tree = eml(left, right)
            if tree.depth() != 4:
                continue
            seed.append(tree)
            if len(seed) >= seed_limit:
                return seed
    return seed


def exact_depth5_shard(lower3: list[Tree], depth4: list[Tree], limit: int) -> Iterable[Tree]:
    count = 0
    for d4 in depth4:
        for lower in lower3:
            for tree in (eml(d4, lower), eml(lower, d4)):
                if count >= limit:
                    return
                count += 1
                yield tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Exact-depth-5 shard probe for EML search.")
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--depth4-seed-limit", type=int, default=1000)
    parser.add_argument("--tolerance", type=float, default=1.0e-9)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    counts = corpus_counts(5)
    setup_start = time.perf_counter()
    lower_layers = build_layers_upto(3)
    lower3 = [tree for bucket in lower_layers for tree in bucket]
    depth4 = depth4_seed(lower3, args.depth4_seed_limit)
    setup_elapsed = time.perf_counter() - setup_start

    results = {
        target: {
            "first_fit_at": None,
            "first_fit_expr": None,
            "best_shard_error": None,
            "best_shard_expr": None,
        }
        for target, _fn, _xs in TARGETS
    }
    scanned = 0
    valid_evals = 0
    eval_start = time.perf_counter()
    for scanned, tree in enumerate(exact_depth5_shard(lower3, depth4, args.limit), start=1):
        for target, fn, xs in TARGETS:
            error = max_abs_error(tree, fn, xs)
            if error is None:
                continue
            valid_evals += 1
            row = results[target]
            if row["best_shard_error"] is None or error < row["best_shard_error"]:
                row["best_shard_error"] = error
                row["best_shard_expr"] = tree.pretty()
            if error <= args.tolerance and row["first_fit_at"] is None:
                row["first_fit_at"] = scanned
                row["first_fit_expr"] = tree.pretty()
    eval_elapsed = time.perf_counter() - eval_start

    artifact = {
        "schema": "eml_depth5_probe_v1",
        "scope": {
            "claim": (
                "Exact-depth-5 EML search is too large for default brute force; "
                "this probe samples a bounded shard generated from an early "
                "depth-4 seed."
            ),
            "not_claimed": [
                "not exhaustive over depth 5",
                "not a global prefix of every depth-5 candidate",
                "not GPU accelerated",
                "not full symbolic regression",
            ],
        },
        "parameters": {
            "limit": args.limit,
            "depth4_seed_limit": args.depth4_seed_limit,
            "tolerance": args.tolerance,
        },
        "corpus": {
            "per_exact_depth_counts": counts,
            "depth5_exact_count": counts[5],
            "depth5_total_count": sum(counts),
        },
        "metrics": {
            "setup_elapsed_s": setup_elapsed,
            "eval_elapsed_s": eval_elapsed,
            "scanned": scanned,
            "depth4_seed_count": len(depth4),
            "lower3_count": len(lower3),
            "valid_evals": valid_evals,
            "evals_per_second": valid_evals / eval_elapsed if eval_elapsed > 0 else None,
        },
        "results": results,
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out.relative_to(ROOT)), "scanned": scanned}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
