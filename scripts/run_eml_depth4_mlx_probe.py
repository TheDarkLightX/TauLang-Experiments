#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np

from run_eml_depth4_probe import (
    MAX_ABS,
    TARGETS,
    Tree,
    build_layers_upto,
    corpus_counts,
    eml,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "local" / "eml-depth4-mlx-probe.json"


def lower3_trees() -> list[Tree]:
    layers = build_layers_upto(3)
    return [tree for bucket in layers for tree in bucket]


def lower3_values(trees: list[Tree], xs: tuple[float, ...]) -> mx.array:
    rows: list[list[float]] = []
    for tree in trees:
        row: list[float] = []
        for x in xs:
            try:
                row.append(float(tree.eval(x)))
            except (OverflowError, ValueError):
                row.append(float("nan"))
        rows.append(row)
    return mx.array(np.asarray(rows, dtype=np.float32))


def exact_depth4_pairs(
    *,
    start: int,
    stop: int,
    lower_count: int,
    depth_lt3_count: int,
    depth3_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(start, stop, dtype=np.int64)
    first_block = depth_lt3_count * depth3_count
    left = np.empty_like(indices)
    right = np.empty_like(indices)

    first = indices < first_block
    if np.any(first):
        first_indices = indices[first]
        left[first] = first_indices // depth3_count
        right[first] = depth_lt3_count + (first_indices % depth3_count)

    if np.any(~first):
        rest = indices[~first] - first_block
        offset = depth_lt3_count * lower_count + rest
        left[~first] = offset // lower_count
        right[~first] = offset % lower_count

    return left.astype(np.int32, copy=False), right.astype(np.int32, copy=False)


def eval_batch(
    values: mx.array,
    target: mx.array,
    left_idx: np.ndarray,
    right_idx: np.ndarray,
) -> np.ndarray:
    left = mx.take(values, mx.array(left_idx), axis=0)
    right = mx.take(values, mx.array(right_idx), axis=0)
    valid = mx.isfinite(left) & mx.isfinite(right) & (right > 0.0) & (mx.abs(left) <= 180.0)
    out = mx.exp(left) - mx.log(right)
    valid = valid & mx.isfinite(out) & (mx.abs(out) <= MAX_ABS)
    errors = mx.abs(out - target)
    row_error = mx.max(mx.where(valid, errors, mx.inf), axis=1)
    row_valid = mx.all(valid, axis=1)
    row_error = mx.where(row_valid, row_error, mx.inf)
    mx.eval(row_error)
    return np.asarray(row_error, dtype=np.float64)


def candidate_expr(trees: list[Tree], left: int, right: int) -> str:
    return eml(trees[int(left)], trees[int(right)]).pretty()


def main() -> int:
    parser = argparse.ArgumentParser(description="MLX/Metal exact-depth-4 EML batch scoring probe.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=262144)
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.0e-6,
        help="Float32 MLX scoring tolerance. Exact candidates still need host/Tau certificate checks.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be positive")

    setup_start = time.perf_counter()
    counts = corpus_counts(4)
    trees = lower3_trees()
    depth_lt3_count = sum(1 for tree in trees if tree.depth() < 3)
    depth3_count = len(trees) - depth_lt3_count
    exact_depth4_count = counts[4]
    limit = exact_depth4_count if args.limit is None else min(args.limit, exact_depth4_count)
    value_tables: dict[str, mx.array] = {}
    target_values: dict[str, mx.array] = {}
    for target, fn, xs in TARGETS:
        value_tables[target] = lower3_values(trees, xs)
        target_values[target] = mx.array(np.asarray([fn(x) for x in xs], dtype=np.float32))
    setup_elapsed = time.perf_counter() - setup_start

    results: dict[str, dict[str, Any]] = {
        target: {
            "first_fit_at": None,
            "first_fit_expr": None,
            "best_error": math.inf,
            "best_expr": None,
        }
        for target, _fn, _xs in TARGETS
    }
    valid_evals = 0
    eval_start = time.perf_counter()
    for start in range(0, limit, args.batch_size):
        stop = min(limit, start + args.batch_size)
        left_idx, right_idx = exact_depth4_pairs(
            start=start,
            stop=stop,
            lower_count=len(trees),
            depth_lt3_count=depth_lt3_count,
            depth3_count=depth3_count,
        )
        for target, _fn, _xs in TARGETS:
            errors = eval_batch(value_tables[target], target_values[target], left_idx, right_idx)
            finite = np.isfinite(errors)
            valid_evals += int(np.count_nonzero(finite))
            if not np.any(finite):
                continue
            target_result = results[target]
            finite_positions = np.flatnonzero(finite)
            best_local = int(finite_positions[np.argmin(errors[finite])])
            best_error = float(errors[best_local])
            if best_error < float(target_result["best_error"]):
                target_result["best_error"] = best_error
                target_result["best_expr"] = candidate_expr(trees, left_idx[best_local], right_idx[best_local])
            fit_positions = np.flatnonzero(errors <= args.tolerance)
            if fit_positions.size and target_result["first_fit_at"] is None:
                first_local = int(fit_positions[0])
                target_result["first_fit_at"] = start + first_local + 1
                target_result["first_fit_expr"] = candidate_expr(trees, left_idx[first_local], right_idx[first_local])
    eval_elapsed = time.perf_counter() - eval_start

    for row in results.values():
        if not math.isfinite(float(row["best_error"])):
            row["best_error"] = None

    artifact = {
        "schema": "eml_depth4_mlx_probe_v1",
        "scope": {
            "claim": "Exact-depth-4 EML candidate scoring can be batched on Apple GPU through MLX.",
            "not_claimed": [
                "not a proof of full symbolic regression",
                "float32 GPU scoring is an approximate screen",
                "not a replacement for Tau/qNS certificate gating",
                "not exhaustive if limit is below exact_depth4_count",
            ],
        },
        "parameters": {
            "limit": limit,
            "batch_size": args.batch_size,
            "tolerance": args.tolerance,
        },
        "corpus": {
            "per_exact_depth_counts": counts,
            "depth3_total": sum(counts[:4]),
            "exact_depth4_count": exact_depth4_count,
            "depth4_total": sum(counts),
            "lower3_count": len(trees),
            "depth_lt3_count": depth_lt3_count,
            "depth3_count": depth3_count,
        },
        "metrics": {
            "device": str(mx.default_device()),
            "setup_elapsed_s": setup_elapsed,
            "eval_elapsed_s": eval_elapsed,
            "scanned": limit,
            "valid_evals": valid_evals,
            "evals_per_second": valid_evals / eval_elapsed if eval_elapsed > 0 else None,
        },
        "results": results,
    }
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out.relative_to(ROOT)), "scanned": limit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
