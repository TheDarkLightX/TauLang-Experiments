#!/usr/bin/env python3
"""Tau-style derivative and finite-equivalence executable corpus.

This script is a standalone companion to the c120-c122 Lean packets. It does
not call Tau and it is not an upstream Tau feature. It checks a small
Tau-shaped expression kernel over a finite Boolean-algebra carrier:

  const table
  common
  pointJoin
  pointCompl

The derivative law checked here is:

  eval(derivative(k,v,e)) = update(eval(e), k, evalConst(e,v))

The finite-equivalence check mirrors the c121/c122 lesson: on a finite carrier,
semantic table equality is decidable, so the restricted expression kernel can
use evaluation-wrapping as a complete equivalence check.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MASK = 0b1111
KEY_COUNT = 4
Table = tuple[int, ...]


@dataclass(frozen=True)
class Expr:
    kind: str
    value: Table | None = None
    args: tuple["Expr", ...] = ()


def table(values: Iterable[int]) -> Table:
    out = tuple(value & MASK for value in values)
    if len(out) != KEY_COUNT:
        raise ValueError(f"table must have {KEY_COUNT} entries")
    return out


def const(values: Iterable[int]) -> Expr:
    return Expr("const", table(values))


def common(a: Expr, b: Expr) -> Expr:
    return Expr("common", None, (a, b))


def point_join(a: Expr, b: Expr) -> Expr:
    return Expr("pointJoin", None, (a, b))


def point_compl(a: Expr) -> Expr:
    return Expr("pointCompl", None, (a,))


def table_meet(a: Table, b: Table) -> Table:
    return tuple(x & y for x, y in zip(a, b, strict=True))


def table_join(a: Table, b: Table) -> Table:
    return tuple(x | y for x, y in zip(a, b, strict=True))


def table_compl(a: Table) -> Table:
    return tuple((~x) & MASK for x in a)


def update_table(t: Table, key: int, value: int) -> Table:
    values = list(t)
    values[key] = value & MASK
    return tuple(values)


def eval_expr(e: Expr) -> Table:
    if e.kind == "const":
        assert e.value is not None
        return e.value
    if e.kind == "common":
        return table_meet(eval_expr(e.args[0]), eval_expr(e.args[1]))
    if e.kind == "pointJoin":
        return table_join(eval_expr(e.args[0]), eval_expr(e.args[1]))
    if e.kind == "pointCompl":
        return table_compl(eval_expr(e.args[0]))
    raise ValueError(f"unknown expression kind: {e.kind}")


def eval_const(e: Expr, value: int) -> int:
    value &= MASK
    if e.kind == "const":
        return value
    if e.kind == "common":
        return eval_const(e.args[0], value) & eval_const(e.args[1], value)
    if e.kind == "pointJoin":
        return eval_const(e.args[0], value) | eval_const(e.args[1], value)
    if e.kind == "pointCompl":
        return (~eval_const(e.args[0], value)) & MASK
    raise ValueError(f"unknown expression kind: {e.kind}")


def derivative(e: Expr, key: int, value: int) -> Expr:
    if e.kind == "const":
        assert e.value is not None
        return Expr("const", update_table(e.value, key, value))
    return Expr(e.kind, None, tuple(derivative(child, key, value) for child in e.args))


def tree_size(e: Expr) -> int:
    return 1 + sum(tree_size(child) for child in e.args)


def random_table(rng: random.Random) -> Table:
    return table(rng.randrange(MASK + 1) for _ in range(KEY_COUNT))


def random_expr(rng: random.Random, depth: int) -> Expr:
    if depth == 0 or rng.random() < 0.3:
        return Expr("const", random_table(rng))
    roll = rng.random()
    if roll < 0.4:
        return common(random_expr(rng, depth - 1), random_expr(rng, depth - 1))
    if roll < 0.8:
        return point_join(random_expr(rng, depth - 1), random_expr(rng, depth - 1))
    return point_compl(random_expr(rng, depth - 1))


def expression_to_obj(e: Expr) -> object:
    if e.kind == "const":
        return {"const": list(e.value or ())}
    if e.kind == "pointCompl":
        return {"pointCompl": expression_to_obj(e.args[0])}
    return {e.kind: [expression_to_obj(child) for child in e.args]}


def derivative_case(rng: random.Random, depth: int) -> dict[str, object]:
    e = random_expr(rng, depth)
    key = rng.randrange(KEY_COUNT)
    value = rng.randrange(MASK + 1)
    deriv = derivative(e, key, value)
    lhs = eval_expr(deriv)
    rhs = update_table(eval_expr(e), key, eval_const(e, value))
    away_ok = all(lhs[i] == eval_expr(e)[i] for i in range(KEY_COUNT) if i != key)
    at_key_ok = lhs[key] == eval_const(e, value)
    return {
        "key": key,
        "value": value,
        "original_size": tree_size(e),
        "derivative_size": tree_size(deriv),
        "size_preserved": tree_size(e) == tree_size(deriv),
        "sound": lhs == rhs,
        "away_from_key_ok": away_ok,
        "at_key_ok": at_key_ok,
    }


def equivalent_pair(rng: random.Random, depth: int) -> tuple[Expr, Expr, bool]:
    e = random_expr(rng, depth)
    # Sound rewrite examples in the checked kernel.
    roll = rng.randrange(4)
    if roll == 0:
        return e, point_compl(point_compl(e)), True
    if roll == 1:
        return e, common(e, e), True
    if roll == 2:
        return e, point_join(e, e), True
    # A likely non-equivalent perturbation. If it coincides semantically, the
    # finite equivalence checker should still classify it correctly.
    other = derivative(e, rng.randrange(KEY_COUNT), rng.randrange(MASK + 1))
    return e, other, eval_expr(e) == eval_expr(other)


def equivalence_case(rng: random.Random, depth: int) -> dict[str, object]:
    left, right, expected_equiv = equivalent_pair(rng, depth)
    left_sem = eval_expr(left)
    right_sem = eval_expr(right)
    equiv_by_eval_wrapping = left_sem == right_sem
    return {
        "left_size": tree_size(left),
        "right_size": tree_size(right),
        "expected_equivalent": expected_equiv,
        "equiv_by_eval_wrapping": equiv_by_eval_wrapping,
        "classification_ok": equiv_by_eval_wrapping == expected_equiv,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--depth", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260415)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/local/tau-derivative-equivalence-demo.json"),
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    derivative_rows = [derivative_case(rng, args.depth) for _ in range(args.count)]
    equivalence_rows = [equivalence_case(rng, args.depth) for _ in range(args.count)]

    derivative_ok = all(
        row["sound"] and row["size_preserved"] and row["away_from_key_ok"] and row["at_key_ok"]
        for row in derivative_rows
    )
    equivalence_ok = all(row["classification_ok"] for row in equivalence_rows)
    equivalent_count = sum(1 for row in equivalence_rows if row["equiv_by_eval_wrapping"])
    non_equivalent_count = len(equivalence_rows) - equivalent_count

    summary = {
        "scope": "Tau-like derivative and finite-carrier equivalence executable corpus",
        "boundary": (
            "Standalone kernel check only. This is not Tau parser support, not a "
            "runtime delta engine, and not arbitrary infinite-carrier equivalence."
        ),
        "case_count": args.count,
        "key_count": KEY_COUNT,
        "carrier": "four-cell Boolean algebra encoded as 4-bit masks",
        "ok": derivative_ok and equivalence_ok,
        "derivative": {
            "sound_cases": sum(1 for row in derivative_rows if row["sound"]),
            "size_preserved_cases": sum(1 for row in derivative_rows if row["size_preserved"]),
            "away_from_key_cases": sum(1 for row in derivative_rows if row["away_from_key_ok"]),
            "at_key_cases": sum(1 for row in derivative_rows if row["at_key_ok"]),
        },
        "equivalence": {
            "classification_ok_cases": sum(
                1 for row in equivalence_rows if row["classification_ok"]
            ),
            "equivalent_cases": equivalent_count,
            "non_equivalent_cases": non_equivalent_count,
            "decision_rule": "eval(e1) == eval(e2) on the finite carrier",
        },
        "sample_derivative_rows": derivative_rows[:5],
        "sample_equivalence_rows": equivalence_rows[:5],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
