#!/usr/bin/env python3
"""Policy-shaped qelim corpus with residual-formula semantic validation.

The string canonicalizer in `run_qelim_policy_shape_corpus.py` is deliberately
simple. This script adds a stronger validation layer for the residual formulas
that Tau prints after qelim: parse the Boolean formula over atoms of the form
`name = 0`, evaluate both residuals over every atom valuation, and compare the
truth tables.

This is a translation-validation harness, not a proof of arbitrary Tau syntax.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path

from run_qelim_policy_shape_corpus import MODES, atom, cases as base_cases
from run_qelim_policy_shape_corpus import choice, dp_guard, qprefix, run_tau, summarize


TOKEN_RE = re.compile(r"\s*(&&|\|\||!|\(|\)|=|0|1|[A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    value: bool


@dataclass(frozen=True)
class Not:
    child: "Expr"


@dataclass(frozen=True)
class And:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Or:
    left: "Expr"
    right: "Expr"


Expr = Var | Const | Not | And | Or


class Parser:
    def __init__(self, text: str) -> None:
        self.tokens = self._tokens(text)
        self.pos = 0

    @staticmethod
    def _tokens(text: str) -> list[str]:
        tokens = []
        pos = 0
        while pos < len(text):
            match = TOKEN_RE.match(text, pos)
            if not match:
                raise ValueError(f"cannot tokenize near: {text[pos:pos + 30]!r}")
            tokens.append(match.group(1))
            pos = match.end()
        return tokens

    def peek(self) -> str | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def take(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of formula")
        if expected is not None and token != expected:
            raise ValueError(f"expected {expected!r}, got {token!r}")
        self.pos += 1
        return token

    def parse(self) -> Expr:
        expr = self.parse_or()
        if self.peek() is not None:
            raise ValueError(f"unexpected token: {self.peek()!r}")
        return expr

    def parse_or(self) -> Expr:
        expr = self.parse_and()
        while self.peek() == "||":
            self.take("||")
            expr = Or(expr, self.parse_and())
        return expr

    def parse_and(self) -> Expr:
        expr = self.parse_not()
        while self.peek() == "&&":
            self.take("&&")
            expr = And(expr, self.parse_not())
        return expr

    def parse_not(self) -> Expr:
        if self.peek() == "!":
            self.take("!")
            return Not(self.parse_not())
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        token = self.peek()
        if token == "(":
            self.take("(")
            expr = self.parse_or()
            self.take(")")
            return expr
        left = self.take()
        if left in {"0", "1"} and self.peek() != "=":
            return Const(left == "1")
        self.take("=")
        right = self.take()
        if right not in {"0", "1"}:
            raise ValueError(f"expected Boolean constant after '=', got {right!r}")
        if left in {"0", "1"}:
            return Const(left == right)
        return Var(left) if right == "0" else Not(Var(left))


def extract_formula(stdout: str) -> str:
    for line in stdout.strip().splitlines():
        if line.startswith("%1:"):
            return line.removeprefix("%1:").strip()
    raise ValueError("missing %1 qelim output line")


def names(expr: Expr) -> set[str]:
    if isinstance(expr, Var):
        return {expr.name}
    if isinstance(expr, Const):
        return set()
    if isinstance(expr, Not):
        return names(expr.child)
    if isinstance(expr, And | Or):
        return names(expr.left) | names(expr.right)
    raise TypeError(expr)


def eval_expr(expr: Expr, env: dict[str, bool]) -> bool:
    if isinstance(expr, Var):
        return env[expr.name]
    if isinstance(expr, Const):
        return expr.value
    if isinstance(expr, Not):
        return not eval_expr(expr.child, env)
    if isinstance(expr, And):
        return eval_expr(expr.left, env) and eval_expr(expr.right, env)
    if isinstance(expr, Or):
        return eval_expr(expr.left, env) or eval_expr(expr.right, env)
    raise TypeError(expr)


def signature(expr: Expr, universe: list[str]) -> list[bool]:
    out = []
    for bits in itertools.product([False, True], repeat=len(universe)):
        env = dict(zip(universe, bits, strict=True))
        out.append(eval_expr(expr, env))
    return out


def semantically_equal(left_stdout: str, right_stdout: str) -> bool:
    left = Parser(extract_formula(left_stdout)).parse()
    right = Parser(extract_formula(right_stdout)).parse()
    universe = sorted(names(left) | names(right))
    return signature(left, universe) == signature(right, universe)


def extra_cases() -> list[dict[str, str]]:
    table_with_dp_child = choice(
        "incident_gate",
        f"({dp_guard('witness', 'freeze', 'review')} && {atom('audit')})",
        choice("clear_gate", atom("allow"), atom("monitor")),
    )
    return [
        {
            "name": "table_with_dp_child_semantic",
            "command": f"qelim {qprefix(['incident_gate', 'witness', 'clear_gate'])} {table_with_dp_child}",
        }
    ]


def cases() -> list[dict[str, str]]:
    return base_cases() + extra_cases()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-policy-semantic-corpus.json"))
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    per_mode: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
    ok = True
    syntactic_fail_semantic_pass = 0
    for case in cases():
        case_runs: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
        for _ in range(args.reps):
            for mode in MODES:
                result = run_tau(args.tau_bin, case["command"], mode)
                case_runs[mode.name].append(result)
                per_mode[mode.name].append(result)

        default = case_runs["default"][0]
        default_returncode = default["returncode"]
        semantic_parity = {}
        syntactic_parity = {}
        for mode in MODES:
            sem_ok = True
            syn_ok = True
            for run in case_runs[mode.name]:
                sem_ok = sem_ok and run["returncode"] == default_returncode
                syn_ok = syn_ok and run["returncode"] == default_returncode
                if run["returncode"] == default_returncode == 0:
                    sem_ok = sem_ok and semantically_equal(str(default["stdout"]), str(run["stdout"]))
                    syn_ok = syn_ok and run["normalized_stdout"] == default["normalized_stdout"]
            semantic_parity[mode.name] = sem_ok
            syntactic_parity[mode.name] = syn_ok
            if sem_ok and not syn_ok:
                syntactic_fail_semantic_pass += 1
        ok = ok and default_returncode == 0 and all(semantic_parity.values())
        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "semantic_default_parity": semantic_parity,
                "syntactic_default_parity": syntactic_parity,
                "summary": {mode.name: summarize(case_runs[mode.name]) for mode in MODES},
            }
        )

    summary = {
        "scope": "policy-shaped qelim corpus with residual truth-table validation",
        "ok": ok,
        "case_count": len(cases()),
        "reps": args.reps,
        "syntactic_fail_semantic_pass_count": syntactic_fail_semantic_pass,
        "mode_summary": {mode.name: summarize(per_mode[mode.name]) for mode in MODES},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
