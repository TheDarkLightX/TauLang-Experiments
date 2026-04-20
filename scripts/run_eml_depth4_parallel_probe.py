#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from run_eml_depth4_probe import (
    TARGETS,
    Tree,
    build_layers_upto,
    corpus_counts,
    eml,
    max_abs_error,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "local" / "eml-depth4-parallel-probe.json"


LOWER3: list[Tree] = []
LOWER3_N = 0
LOWER3_DEPTH_LT3 = 0
LOWER3_DEPTH3 = 0
LOWER3_FIRST_BLOCK = 0


def init_worker(lower3: list[Tree]) -> None:
    global LOWER3, LOWER3_N, LOWER3_DEPTH_LT3, LOWER3_DEPTH3, LOWER3_FIRST_BLOCK
    LOWER3 = lower3
    LOWER3_N = len(lower3)
    LOWER3_DEPTH_LT3 = sum(1 for tree in lower3 if tree.depth() < 3)
    LOWER3_DEPTH3 = LOWER3_N - LOWER3_DEPTH_LT3
    LOWER3_FIRST_BLOCK = LOWER3_DEPTH_LT3 * LOWER3_DEPTH3


def exact_depth4_raw_offset(exact_index: int) -> int:
    """Map an exact-depth-4 candidate index to the row-major lower3 pair offset."""
    if exact_index < LOWER3_FIRST_BLOCK:
        row = exact_index // LOWER3_DEPTH3
        col = LOWER3_DEPTH_LT3 + (exact_index % LOWER3_DEPTH3)
        return row * LOWER3_N + col
    return LOWER3_DEPTH_LT3 * LOWER3_N + (exact_index - LOWER3_FIRST_BLOCK)


def evaluate_range(start: int, stop: int, tolerance: float) -> dict[str, Any]:
    results = {
        target: {
            "first_fit_at": None,
            "first_fit_expr": None,
            "best_error": math.inf,
            "best_expr": None,
        }
        for target, _fn, _xs in TARGETS
    }
    valid_evals = 0
    n = len(LOWER3)
    for exact_index in range(start, stop):
        offset = exact_depth4_raw_offset(exact_index)
        if offset >= n * n:
            break
        left = LOWER3[offset // n]
        right = LOWER3[offset % n]
        tree = eml(left, right)
        absolute_index = exact_index + 1
        for target, fn, xs in TARGETS:
            error = max_abs_error(tree, fn, xs)
            if error is None:
                continue
            valid_evals += 1
            row = results[target]
            if error < row["best_error"]:
                row["best_error"] = error
                row["best_expr"] = tree.pretty()
            if error <= tolerance and row["first_fit_at"] is None:
                row["first_fit_at"] = absolute_index
                row["first_fit_expr"] = tree.pretty()
    return {
        "start": start,
        "stop": stop,
        "scanned": max(0, stop - start),
        "valid_evals": valid_evals,
        "results": results,
    }


def evaluate_range_tuple(args: tuple[int, int, float]) -> dict[str, Any]:
    return evaluate_range(*args)


def merge_results(parts: list[dict[str, Any]]) -> dict[str, Any]:
    merged = {
        target: {
            "first_fit_at": None,
            "first_fit_expr": None,
            "best_prefix_error": None,
            "best_prefix_expr": None,
        }
        for target, _fn, _xs in TARGETS
    }
    for part in parts:
        for target, row in part["results"].items():
            out = merged[target]
            if row["first_fit_at"] is not None and (
                out["first_fit_at"] is None or row["first_fit_at"] < out["first_fit_at"]
            ):
                out["first_fit_at"] = row["first_fit_at"]
                out["first_fit_expr"] = row["first_fit_expr"]
            if math.isfinite(row["best_error"]) and (
                out["best_prefix_error"] is None or row["best_error"] < out["best_prefix_error"]
            ):
                out["best_prefix_error"] = row["best_error"]
                out["best_prefix_expr"] = row["best_expr"]
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel CPU exact-depth-4 feasibility probe for EML search.")
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--chunk-size", type=int, default=25000)
    parser.add_argument("--tolerance", type=float, default=1.0e-9)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be positive")

    counts = corpus_counts(4)
    lower_layers = build_layers_upto(3)
    lower3 = [tree for bucket in lower_layers for tree in bucket]
    ranges = [
        (start, min(args.limit, start + args.chunk_size), args.tolerance)
        for start in range(0, args.limit, args.chunk_size)
    ]
    start_time = time.perf_counter()
    with ProcessPoolExecutor(
        max_workers=args.workers,
        initializer=init_worker,
        initargs=(lower3,),
    ) as pool:
        parts = list(pool.map(evaluate_range_tuple, ranges))
    elapsed = time.perf_counter() - start_time
    scanned = sum(part["scanned"] for part in parts)
    valid_evals = sum(part["valid_evals"] for part in parts)
    artifact = {
        "schema": "eml_depth4_parallel_probe_v1",
        "scope": {
            "claim": "Exact-depth-4 EML scoring can be sharded across CPU worker processes.",
            "not_claimed": [
                "not GPU accelerated",
                "not a proof of full symbolic regression",
                "not a replacement for canonicalization or pruning",
            ],
        },
        "parameters": {
            "limit": args.limit,
            "workers": args.workers,
            "chunk_size": args.chunk_size,
            "tolerance": args.tolerance,
            "indexing": "exact-depth-4 candidate prefix, one-based fit positions in that prefix",
        },
        "corpus": {
            "per_exact_depth_counts": counts,
            "total_corpus_size": sum(counts),
            "depth3_total": sum(counts[:4]),
            "depth4_total": sum(counts[:5]),
        },
        "metrics": {
            "elapsed_s": elapsed,
            "scanned": scanned,
            "valid_evals": valid_evals,
            "evals_per_second": valid_evals / elapsed if elapsed > 0 else None,
        },
        "results": merge_results(parts),
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out.relative_to(ROOT)), "scanned": scanned}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
