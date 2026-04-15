#!/usr/bin/env python3
"""Prototype equality-aware path simplification.

Tau's README names a known normalization issue: path simplification does not use
equalities between variables. This script models the smallest safe optimization:
under assumptions such as `x = y`, replace variables by representatives and
then run local Boolean simplification.

The acceptance check is semantic, not syntactic. The optimized expression must
agree with the original on every environment satisfying the equality
assumptions, and the script also records a counterexample showing why the same
rewrite is unsound without those assumptions.
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


Expr = tuple


def var(name: str) -> Expr:
    return ("var", name)


def const(value: bool) -> Expr:
    return ("const", value)


def neg(x: Expr) -> Expr:
    return ("not", x)


def conj(a: Expr, b: Expr) -> Expr:
    return ("and", a, b)


def disj(a: Expr, b: Expr) -> Expr:
    return ("or", a, b)


def eval_expr(expr: Expr, env: dict[str, bool]) -> bool:
    match expr:
        case ("var", name):
            return env[name]
        case ("const", value):
            return bool(value)
        case ("not", x):
            return not eval_expr(x, env)
        case ("and", a, b):
            return eval_expr(a, env) and eval_expr(b, env)
        case ("or", a, b):
            return eval_expr(a, env) or eval_expr(b, env)
    raise ValueError(f"unknown expression: {expr!r}")


def node_count(expr: Expr) -> int:
    match expr:
        case ("var", _) | ("const", _):
            return 1
        case ("not", x):
            return 1 + node_count(x)
        case ("and", a, b) | ("or", a, b):
            return 1 + node_count(a) + node_count(b)
    raise ValueError(f"unknown expression: {expr!r}")


def substitute(expr: Expr, reps: dict[str, str]) -> Expr:
    match expr:
        case ("var", name):
            return var(reps.get(name, name))
        case ("const", value):
            return const(bool(value))
        case ("not", x):
            return neg(substitute(x, reps))
        case ("and", a, b):
            return conj(substitute(a, reps), substitute(b, reps))
        case ("or", a, b):
            return disj(substitute(a, reps), substitute(b, reps))
    raise ValueError(f"unknown expression: {expr!r}")


def simplify(expr: Expr) -> Expr:
    match expr:
        case ("var", _) | ("const", _):
            return expr
        case ("not", x):
            sx = simplify(x)
            if sx == const(True):
                return const(False)
            if sx == const(False):
                return const(True)
            if sx[0] == "not":
                return sx[1]
            return neg(sx)
        case ("and", a, b):
            sa = simplify(a)
            sb = simplify(b)
            if sa == const(False) or sb == const(False):
                return const(False)
            if is_negation_pair(sa, sb):
                return const(False)
            if sa == const(True):
                return sb
            if sb == const(True):
                return sa
            if sa == sb:
                return sa
            return conj(sa, sb)
        case ("or", a, b):
            sa = simplify(a)
            sb = simplify(b)
            if sa == const(True) or sb == const(True):
                return const(True)
            if is_negation_pair(sa, sb):
                return const(True)
            if sa == const(False):
                return sb
            if sb == const(False):
                return sa
            if sa == sb:
                return sa
            return disj(sa, sb)
    raise ValueError(f"unknown expression: {expr!r}")


def is_negation_pair(a: Expr, b: Expr) -> bool:
    return (a[0] == "not" and a[1] == b) or (b[0] == "not" and b[1] == a)


def expr_vars(expr: Expr) -> set[str]:
    match expr:
        case ("var", name):
            return {name}
        case ("const", _):
            return set()
        case ("not", x):
            return expr_vars(x)
        case ("and", a, b) | ("or", a, b):
            return expr_vars(a) | expr_vars(b)
    raise ValueError(f"unknown expression: {expr!r}")


def envs(names: Iterable[str]) -> Iterable[dict[str, bool]]:
    ordered = sorted(names)
    for values in itertools.product([False, True], repeat=len(ordered)):
        yield dict(zip(ordered, values, strict=True))


def satisfies_equalities(env: dict[str, bool], equalities: list[tuple[str, str]]) -> bool:
    return all(env[a] == env[b] for a, b in equalities)


def expr_to_str(expr: Expr) -> str:
    match expr:
        case ("var", name):
            return name
        case ("const", True):
            return "1"
        case ("const", False):
            return "0"
        case ("not", x):
            return f"!{expr_to_str(x)}"
        case ("and", a, b):
            return f"({expr_to_str(a)} & {expr_to_str(b)})"
        case ("or", a, b):
            return f"({expr_to_str(a)} | {expr_to_str(b)})"
    raise ValueError(f"unknown expression: {expr!r}")


@dataclass(frozen=True)
class Case:
    name: str
    expr: Expr
    equalities: list[tuple[str, str]]
    reps: dict[str, str]


def cases() -> list[Case]:
    return [
        Case(
            name="chain_representative_collapse",
            equalities=[("x1", "x0"), ("x2", "x0")],
            reps={"x1": "x0", "x2": "x0"},
            expr=disj(
                disj(conj(var("x0"), var("x1")), conj(var("x1"), var("x2"))),
                conj(neg(var("x0")), var("x2")),
            ),
        ),
        Case(
            name="guarded_priority_aliases",
            equalities=[("risk_shadow", "risk"), ("manual_shadow", "manual")],
            reps={"risk_shadow": "risk", "manual_shadow": "manual"},
            expr=disj(
                conj(var("risk"), var("risk_shadow")),
                conj(neg(var("risk_shadow")), disj(var("manual"), var("manual_shadow"))),
            ),
        ),
        Case(
            name="state_update_aliases",
            equalities=[("old_borrow", "old_mint"), ("guard_borrow", "guard_mint")],
            reps={"old_borrow": "old_mint", "guard_borrow": "guard_mint"},
            expr=disj(
                conj(var("guard_mint"), var("old_mint")),
                conj(var("guard_borrow"), var("old_borrow")),
            ),
        ),
    ]


def analyze(case: Case) -> dict[str, object]:
    optimized = simplify(substitute(case.expr, case.reps))
    all_vars = expr_vars(case.expr) | set(case.reps.values())
    checked = 0
    violations = []
    outside_counterexample = None
    for env in envs(all_vars):
        original = eval_expr(case.expr, env)
        new = eval_expr(optimized, env)
        if satisfies_equalities(env, case.equalities):
            checked += 1
            if original != new:
                violations.append({"env": env, "original": original, "optimized": new})
        elif outside_counterexample is None and original != new:
            outside_counterexample = {
                "env": env,
                "original": original,
                "optimized": new,
            }
    before = node_count(case.expr)
    after_subst = node_count(substitute(case.expr, case.reps))
    after_simplify = node_count(optimized)
    return {
        "name": case.name,
        "equalities": case.equalities,
        "representatives": case.reps,
        "original": expr_to_str(case.expr),
        "optimized": expr_to_str(optimized),
        "original_nodes": before,
        "after_substitution_nodes": after_subst,
        "optimized_nodes": after_simplify,
        "node_reduction_percent": round(100.0 * (before - after_simplify) / before, 3),
        "satisfying_envs_checked": checked,
        "violations_under_equalities": violations,
        "outside_assumption_counterexample": outside_counterexample,
        "ok": not violations and outside_counterexample is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/local/equality-path-simplification-demo.json"))
    args = parser.parse_args()
    rows = [analyze(case) for case in cases()]
    total_before = sum(int(row["original_nodes"]) for row in rows)
    total_after = sum(int(row["optimized_nodes"]) for row in rows)
    summary = {
        "scope": "bounded equality-aware path simplification model",
        "ok": all(bool(row["ok"]) for row in rows),
        "case_count": len(rows),
        "total_original_nodes": total_before,
        "total_optimized_nodes": total_after,
        "total_node_reduction_percent": round(100.0 * (total_before - total_after) / total_before, 3),
        "rows": rows,
        "law": (
            "If the current path entails x = rep(x), replacing x by rep(x) "
            "preserves evaluation on environments satisfying those equalities."
        ),
        "boundary": (
            "This is a Tau-like model, not Tau's full normalizer. The recorded "
            "counterexamples show that representative substitution is unsound "
            "outside the equality-assumption path."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
