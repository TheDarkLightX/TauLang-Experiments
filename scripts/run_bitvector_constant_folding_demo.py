#!/usr/bin/env python3
"""Fixed-width bitvector constant-folding corpus.

This script pairs with the Lean constant-folding packet. The Lean packet proves
pure constant folding. This executable corpus also tests common identity
rewrites by exhaustive environment checks over small widths.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | int | None = None
    args: tuple["Expr", ...] = ()


def const(value: int) -> Expr:
    return Expr("const", value)


def var(name: str) -> Expr:
    return Expr("var", name)


def add(a: Expr, b: Expr) -> Expr:
    return Expr("add", None, (a, b))


def mul(a: Expr, b: Expr) -> Expr:
    return Expr("mul", None, (a, b))


def bv(width: int, value: int) -> int:
    return value & ((1 << width) - 1)


def eval_expr(width: int, env: dict[str, int], expr: Expr) -> int:
    if expr.kind == "const":
        assert isinstance(expr.value, int)
        return bv(width, expr.value)
    if expr.kind == "var":
        assert isinstance(expr.value, str)
        return bv(width, env[expr.value])
    if expr.kind == "add":
        return bv(width, eval_expr(width, env, expr.args[0]) + eval_expr(width, env, expr.args[1]))
    if expr.kind == "mul":
        return bv(width, eval_expr(width, env, expr.args[0]) * eval_expr(width, env, expr.args[1]))
    raise ValueError(f"unknown expression kind: {expr.kind}")


def size(expr: Expr) -> int:
    return 1 + sum(size(child) for child in expr.args)


def simplify(width: int, expr: Expr, *, identity_rewrites: bool) -> Expr:
    if expr.kind == "const":
        assert isinstance(expr.value, int)
        return const(bv(width, expr.value))
    if expr.kind == "var":
        return expr
    left = simplify(width, expr.args[0], identity_rewrites=identity_rewrites)
    right = simplify(width, expr.args[1], identity_rewrites=identity_rewrites)

    if expr.kind == "add":
        if left.kind == "const" and right.kind == "const":
            assert isinstance(left.value, int) and isinstance(right.value, int)
            return const(bv(width, left.value + right.value))
        if identity_rewrites and left == const(0):
            return right
        if identity_rewrites and right == const(0):
            return left
        return add(left, right)

    if expr.kind == "mul":
        if left.kind == "const" and right.kind == "const":
            assert isinstance(left.value, int) and isinstance(right.value, int)
            return const(bv(width, left.value * right.value))
        if identity_rewrites and (left == const(0) or right == const(0)):
            return const(0)
        if identity_rewrites and left == const(1):
            return right
        if identity_rewrites and right == const(1):
            return left
        return mul(left, right)

    raise ValueError(f"unknown expression kind: {expr.kind}")


def random_expr(rng: random.Random, depth: int, variables: list[str], width: int) -> Expr:
    if depth == 0 or rng.random() < 0.28:
        if rng.random() < 0.55:
            return var(rng.choice(variables))
        constants = [0, 1, (1 << width) - 1, 1 << width, (1 << width) + 1]
        return const(rng.choice(constants))
    left = random_expr(rng, depth - 1, variables, width)
    right = random_expr(rng, depth - 1, variables, width)
    return add(left, right) if rng.random() < 0.5 else mul(left, right)


def envs(width: int, variables: list[str]) -> list[dict[str, int]]:
    domain = range(1 << width)
    return [dict(zip(variables, values, strict=True)) for values in itertools.product(domain, repeat=len(variables))]


def check_expr(width: int, variables: list[str], expr: Expr) -> dict[str, object]:
    folded = simplify(width, expr, identity_rewrites=False)
    simplified = simplify(width, expr, identity_rewrites=True)
    all_envs = envs(width, variables)
    folded_ok = all(eval_expr(width, env, folded) == eval_expr(width, env, expr) for env in all_envs)
    simplified_ok = all(
        eval_expr(width, env, simplified) == eval_expr(width, env, expr) for env in all_envs
    )
    return {
        "original_size": size(expr),
        "constant_folded_size": size(folded),
        "identity_simplified_size": size(simplified),
        "constant_folded_ok": folded_ok,
        "identity_simplified_ok": simplified_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=4)
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260415)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/local/bitvector-constant-folding-demo.json"),
    )
    args = parser.parse_args()

    variables = ["a", "b", "c"]
    rng = random.Random(args.seed)
    rows = [
        check_expr(args.width, variables, random_expr(rng, args.depth, variables, args.width))
        for _ in range(args.count)
    ]
    original_total = sum(int(row["original_size"]) for row in rows)
    folded_total = sum(int(row["constant_folded_size"]) for row in rows)
    simplified_total = sum(int(row["identity_simplified_size"]) for row in rows)
    ok = all(row["constant_folded_ok"] and row["identity_simplified_ok"] for row in rows)
    summary = {
        "scope": "fixed-width bitvector constant folding and identity-simplification corpus",
        "width": args.width,
        "case_count": args.count,
        "ok": ok,
        "original_nodes_total": original_total,
        "constant_folded_nodes_total": folded_total,
        "identity_simplified_nodes_total": simplified_total,
        "constant_folded_reduction_percent": round(
            100.0 * (original_total - folded_total) / original_total, 3
        ),
        "identity_simplified_reduction_percent": round(
            100.0 * (original_total - simplified_total) / original_total, 3
        ),
        "rows": rows,
        "boundary": (
            "Lean proves constant folding and identity simplification for the small "
            "fixed-width expression kernel. This corpus is an executable regression "
            "check, not Tau parser support or CVC5 integration."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
