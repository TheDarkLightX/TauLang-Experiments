#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "local" / "eml-depth4-probe.json"
MAX_ABS = 1.0e80


@dataclass(frozen=True)
class Tree:
    kind: str
    left: "Tree | None" = None
    right: "Tree | None" = None

    def depth(self) -> int:
        if self.kind in {"x", "one"}:
            return 0
        assert self.left is not None and self.right is not None
        return 1 + max(self.left.depth(), self.right.depth())

    def size(self) -> int:
        if self.kind in {"x", "one"}:
            return 1
        assert self.left is not None and self.right is not None
        return 1 + self.left.size() + self.right.size()

    def pretty(self) -> str:
        if self.kind == "x":
            return "x"
        if self.kind == "one":
            return "1"
        assert self.left is not None and self.right is not None
        return f"eml({self.left.pretty()},{self.right.pretty()})"

    def eval(self, x: float) -> float:
        if self.kind == "x":
            return x
        if self.kind == "one":
            return 1.0
        assert self.left is not None and self.right is not None
        a = self.left.eval(x)
        b = self.right.eval(x)
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("non-finite child")
        if b <= 0.0:
            raise ValueError("real log domain failure")
        if abs(a) > 180.0:
            raise ValueError("exp guard failure")
        out = math.exp(a) - math.log(b)
        if not math.isfinite(out) or abs(out) > MAX_ABS:
            raise ValueError("non-finite output")
        return out


X = Tree("x")
ONE = Tree("one")


def eml(left: Tree, right: Tree) -> Tree:
    return Tree("eml", left, right)


def build_layers_upto(max_depth: int) -> list[list[Tree]]:
    by_depth: list[list[Tree]] = [[X, ONE]]
    seen = {X.pretty(), ONE.pretty()}
    for depth in range(1, max_depth + 1):
        current: list[Tree] = []
        lower = [tree for bucket in by_depth for tree in bucket]
        for left in lower:
            for right in lower:
                tree = eml(left, right)
                key = tree.pretty()
                if tree.depth() == depth and key not in seen:
                    seen.add(key)
                    current.append(tree)
        by_depth.append(current)
    return by_depth


def corpus_counts(max_depth: int) -> list[int]:
    counts = [2]
    total_before = 2
    total_before_previous = 0
    for _depth in range(1, max_depth + 1):
        count = total_before * total_before - total_before_previous * total_before_previous
        counts.append(count)
        total_before_previous = total_before
        total_before += count
    return counts


def iter_depth4_prefix(max_depth: int, limit: int | None) -> Iterable[Tree]:
    count = 0
    materialized_depth = min(max_depth, 3)
    by_depth = build_layers_upto(materialized_depth)
    for bucket in by_depth:
        for tree in bucket:
            if limit is not None and count >= limit:
                return
            count += 1
            yield tree
    if max_depth < 4:
        return
    lower = [tree for bucket in by_depth for tree in bucket]
    for left in lower:
        for right in lower:
            tree = eml(left, right)
            if tree.depth() != 4:
                continue
            if limit is not None and count >= limit:
                return
            count += 1
            yield tree


def exp_exp(x: float) -> float:
    return math.exp(math.exp(x))


TARGETS: tuple[tuple[str, Callable[[float], float], tuple[float, ...]], ...] = (
    ("x", lambda x: x, (0.5, 1.0, 2.0)),
    ("exp(x)", math.exp, (0.5, 1.0, 2.0)),
    ("ln(x)", math.log, (0.5, 1.0, 2.0)),
    ("exp(exp(x))", exp_exp, (0.1, 0.2, 0.3)),
)


def max_abs_error(tree: Tree, fn: Callable[[float], float], xs: tuple[float, ...]) -> float | None:
    errors: list[float] = []
    try:
        for x in xs:
            errors.append(abs(tree.eval(x) - fn(x)))
    except (OverflowError, ValueError):
        return None
    return max(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Streaming depth-4 feasibility probe for EML search.")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--limit", type=int, default=250000)
    parser.add_argument("--tolerance", type=float, default=1.0e-9)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.max_depth > 4:
        raise SystemExit("this probe is intentionally capped at depth 4")

    start = time.perf_counter()
    counts = corpus_counts(args.max_depth)
    generation_elapsed = time.perf_counter() - start
    results = {
        target: {
            "first_fit_at": None,
            "first_fit_expr": None,
            "best_prefix_error": None,
            "best_prefix_expr": None,
        }
        for target, _fn, _xs in TARGETS
    }
    scanned = 0
    valid_evals = 0
    eval_start = time.perf_counter()
    for scanned, tree in enumerate(iter_depth4_prefix(args.max_depth, args.limit), start=1):
        for target, fn, xs in TARGETS:
            error = max_abs_error(tree, fn, xs)
            if error is None:
                continue
            valid_evals += 1
            row = results[target]
            if row["best_prefix_error"] is None or error < row["best_prefix_error"]:
                row["best_prefix_error"] = error
                row["best_prefix_expr"] = tree.pretty()
            if error <= args.tolerance and row["first_fit_at"] is None:
                row["first_fit_at"] = scanned
                row["first_fit_expr"] = tree.pretty()
    eval_elapsed = time.perf_counter() - eval_start
    artifact = {
        "schema": "eml_depth4_probe_v1",
        "scope": {
            "claim": (
                "Depth-4 EML search is feasible only as a streaming, pruned, or "
                "batched lane, not as the default public brute-force demo."
            ),
            "not_claimed": [
                "not exhaustive if limit is below corpus size",
                "not GPU accelerated",
                "not full symbolic regression",
            ],
        },
        "parameters": {
            "max_depth": args.max_depth,
            "limit": args.limit,
            "tolerance": args.tolerance,
        },
        "corpus": {
            "per_exact_depth_counts": counts,
            "total_corpus_size": sum(counts),
            "depth3_total": sum(counts[:4]) if len(counts) >= 4 else None,
            "depth4_total": sum(counts[:5]) if len(counts) >= 5 else None,
        },
        "metrics": {
            "generation_elapsed_s": generation_elapsed,
            "eval_elapsed_s": eval_elapsed,
            "scanned": scanned,
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
