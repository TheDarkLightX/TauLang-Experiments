#!/usr/bin/env python3
"""Restricted Tau Knuth-Bendix-style normalizer demo.

This is an executable companion to the c111 Lean proof. It implements exactly
the seven oriented rewrite rules from the checked restricted system:

  common(a,a)                         -> a
  pointJoin(a,a)                      -> a
  common(a, pointJoin(a,b))           -> a
  pointJoin(a, common(a,b))           -> a
  pointCompl(pointCompl(a))           -> a
  pointCompl(common(a,b))             -> pointJoin(pointCompl(a), pointCompl(b))
  pointCompl(pointJoin(a,b))          -> common(pointCompl(a), pointCompl(b))

Boundary: this is not a complete Boolean-algebra normalizer. It intentionally
does not orient commutativity, associativity, or distributivity.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple["Expr", ...] = ()

    def pretty(self) -> str:
        if not self.args:
            return self.op
        if self.op == "pointCompl":
            return f"pointCompl({self.args[0].pretty()})"
        return f"{self.op}({self.args[0].pretty()}, {self.args[1].pretty()})"

    def size(self) -> int:
        return 1 + sum(arg.size() for arg in self.args)

    def measure(self) -> int:
        if not self.args:
            return 1
        if self.op in {"common", "pointJoin"}:
            return self.args[0].measure() + self.args[1].measure() + 1
        if self.op == "pointCompl":
            return 3 * self.args[0].measure() + 1
        raise ValueError(f"unknown operator: {self.op}")

    def vars(self) -> set[str]:
        if not self.args:
            if self.op in {"0", "1", "false", "true"}:
                return set()
            return {self.op}
        out: set[str] = set()
        for arg in self.args:
            out.update(arg.vars())
        return out


TOKEN_RE = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*|0|1|[,()])")


class Parser:
    def __init__(self, text: str):
        self.tokens = TOKEN_RE.findall(text)
        joined = "".join(self.tokens)
        compact = re.sub(r"\s+", "", text)
        if joined != compact:
            raise ValueError(f"invalid token near: {text!r}")
        self.i = 0

    def parse(self) -> Expr:
        expr = self.expr()
        if self.i != len(self.tokens):
            raise ValueError(f"unexpected trailing token: {self.tokens[self.i]!r}")
        return expr

    def peek(self) -> str | None:
        if self.i >= len(self.tokens):
            return None
        return self.tokens[self.i]

    def take(self, expected: str | None = None) -> str:
        tok = self.peek()
        if tok is None:
            raise ValueError("unexpected end of input")
        if expected is not None and tok != expected:
            raise ValueError(f"expected {expected!r}, got {tok!r}")
        self.i += 1
        return tok

    def expr(self) -> Expr:
        name = self.take()
        if self.peek() != "(":
            return Expr(name)
        self.take("(")
        if name == "pointCompl":
            arg = self.expr()
            self.take(")")
            return Expr(name, (arg,))
        if name in {"common", "pointJoin"}:
            left = self.expr()
            self.take(",")
            right = self.expr()
            self.take(")")
            return Expr(name, (left, right))
        raise ValueError(f"unknown function: {name}")


def parse_expr(text: str) -> Expr:
    return Parser(text).parse()


def root_rewrite(expr: Expr) -> tuple[Expr, str] | None:
    """Apply one root rewrite if possible."""

    if expr.op == "common":
        a, b = expr.args
        if a == b:
            return a, "idem_common"
        if b.op == "pointJoin" and b.args[0] == a:
            return a, "absorb"

    if expr.op == "pointJoin":
        a, b = expr.args
        if a == b:
            return a, "idem_pointJoin"
        if b.op == "common" and b.args[0] == a:
            return a, "dual_absorb"

    if expr.op == "pointCompl":
        (a,) = expr.args
        if a.op == "pointCompl":
            return a.args[0], "double_compl"
        if a.op == "common":
            x, y = a.args
            return Expr("pointJoin", (Expr("pointCompl", (x,)), Expr("pointCompl", (y,)))), "demorgan_meet"
        if a.op == "pointJoin":
            x, y = a.args
            return Expr("common", (Expr("pointCompl", (x,)), Expr("pointCompl", (y,)))), "demorgan_join"

    return None


def normalize_once(expr: Expr) -> tuple[Expr, str] | None:
    """Leftmost innermost one-step normalization."""

    if expr.args:
        new_args = []
        for idx, arg in enumerate(expr.args):
            step = normalize_once(arg)
            if step is not None:
                new_arg, rule = step
                new_args.extend(expr.args[:idx])
                new_args.append(new_arg)
                new_args.extend(expr.args[idx + 1 :])
                return Expr(expr.op, tuple(new_args)), f"under_{expr.op}:{rule}"
    return root_rewrite(expr)


def normalize(expr: Expr) -> tuple[Expr, list[dict[str, object]]]:
    trace: list[dict[str, object]] = []
    current = expr
    while True:
        step = normalize_once(current)
        if step is None:
            return current, trace
        nxt, rule = step
        before = current.measure()
        after = nxt.measure()
        if after >= before:
            raise RuntimeError(f"measure did not decrease for {rule}: {before} -> {after}")
        trace.append(
            {
                "rule": rule,
                "before_measure": before,
                "after_measure": after,
                "before_size": current.size(),
                "after_size": nxt.size(),
                "after": nxt.pretty(),
            }
        )
        current = nxt


def eval_expr(expr: Expr, env: dict[str, bool]) -> bool:
    if not expr.args:
        if expr.op in {"1", "true"}:
            return True
        if expr.op in {"0", "false"}:
            return False
        return env[expr.op]
    if expr.op == "common":
        return eval_expr(expr.args[0], env) and eval_expr(expr.args[1], env)
    if expr.op == "pointJoin":
        return eval_expr(expr.args[0], env) or eval_expr(expr.args[1], env)
    if expr.op == "pointCompl":
        return not eval_expr(expr.args[0], env)
    raise ValueError(f"unknown operator: {expr.op}")


def all_envs(names: Iterable[str]) -> Iterable[dict[str, bool]]:
    ordered = sorted(names)
    for bits in itertools.product([False, True], repeat=len(ordered)):
        yield dict(zip(ordered, bits, strict=True))


def parity_check(before: Expr, after: Expr, max_vars: int = 12) -> dict[str, object]:
    names = sorted(before.vars() | after.vars())
    if len(names) > max_vars:
        samples = 4096
        rng = random.Random(20260413)
        for _ in range(samples):
            env = {name: bool(rng.getrandbits(1)) for name in names}
            if eval_expr(before, env) != eval_expr(after, env):
                return {"ok": False, "mode": "sampled", "vars": len(names), "counterexample": env}
        return {"ok": True, "mode": "sampled", "vars": len(names), "samples": samples}

    for env in all_envs(names):
        if eval_expr(before, env) != eval_expr(after, env):
            return {"ok": False, "mode": "exhaustive", "vars": len(names), "counterexample": env}
    return {"ok": True, "mode": "exhaustive", "vars": len(names), "assignments": 2 ** len(names)}


def random_expr(rng: random.Random, depth: int, names: list[str]) -> Expr:
    if depth <= 0 or rng.random() < 0.18:
        return Expr(rng.choice(names))

    # Bias toward patterns that the c111 rules intentionally simplify.
    p = rng.random()
    if p < 0.18:
        a = random_expr(rng, depth - 1, names)
        return Expr("common", (a, a))
    if p < 0.32:
        a = random_expr(rng, depth - 1, names)
        return Expr("pointJoin", (a, a))
    if p < 0.46:
        a = random_expr(rng, depth - 1, names)
        b = random_expr(rng, depth - 1, names)
        return Expr("common", (a, Expr("pointJoin", (a, b))))
    if p < 0.60:
        a = random_expr(rng, depth - 1, names)
        b = random_expr(rng, depth - 1, names)
        return Expr("pointJoin", (a, Expr("common", (a, b))))
    if p < 0.74:
        a = random_expr(rng, depth - 1, names)
        return Expr("pointCompl", (Expr("pointCompl", (a,)),))
    if p < 0.87:
        return Expr("pointCompl", (Expr("common", (random_expr(rng, depth - 1, names), random_expr(rng, depth - 1, names))),))
    if p < 0.96:
        return Expr("pointCompl", (Expr("pointJoin", (random_expr(rng, depth - 1, names), random_expr(rng, depth - 1, names))),))
    op = rng.choice(["common", "pointJoin"])
    return Expr(op, (random_expr(rng, depth - 1, names), random_expr(rng, depth - 1, names)))


def demo_corpus() -> list[Expr]:
    return [
        parse_expr("common(a, a)"),
        parse_expr("pointJoin(a, common(a, b))"),
        parse_expr("pointCompl(common(a, pointJoin(a, b)))"),
        parse_expr("pointCompl(pointCompl(pointJoin(a, common(a, b))))"),
        parse_expr("common(pointCompl(pointCompl(a)), pointCompl(pointCompl(a)))"),
    ]


def run_benchmark(count: int, depth: int, seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    exprs = demo_corpus() + [random_expr(rng, depth, ["a", "b", "c", "d", "e"]) for _ in range(count)]
    start = time.perf_counter()
    rows = []
    failures = []
    total_before_size = 0
    total_after_size = 0
    total_before_measure = 0
    total_after_measure = 0
    total_steps = 0

    for i, expr in enumerate(exprs):
        nf, trace = normalize(expr)
        parity = parity_check(expr, nf)
        if not parity["ok"]:
            failures.append({"index": i, "expr": expr.pretty(), "nf": nf.pretty(), "parity": parity})
        total_before_size += expr.size()
        total_after_size += nf.size()
        total_before_measure += expr.measure()
        total_after_measure += nf.measure()
        total_steps += len(trace)
        if i < 12:
            rows.append(
                {
                    "index": i,
                    "input": expr.pretty(),
                    "normal_form": nf.pretty(),
                    "steps": len(trace),
                    "size_before": expr.size(),
                    "size_after": nf.size(),
                    "measure_before": expr.measure(),
                    "measure_after": nf.measure(),
                    "parity": parity,
                }
            )

    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "scope": "restricted c111 rewrite theory, not full Boolean equivalence",
        "rules": [
            "idem_common",
            "idem_pointJoin",
            "absorb",
            "dual_absorb",
            "double_compl",
            "demorgan_meet",
            "demorgan_join",
        ],
        "count": len(exprs),
        "elapsed_ms": round(elapsed_ms, 3),
        "total_steps": total_steps,
        "size_before": total_before_size,
        "size_after": total_after_size,
        "measure_before": total_before_measure,
        "measure_after": total_after_measure,
        "size_reduction_percent": round(100 * (total_before_size - total_after_size) / max(total_before_size, 1), 2),
        "measure_reduction_percent": round(
            100 * (total_before_measure - total_after_measure) / max(total_before_measure, 1), 2
        ),
        "parity_failures": failures,
        "examples": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    norm = sub.add_parser("normalize", help="normalize one expression")
    norm.add_argument("expr")
    norm.add_argument("--json", action="store_true")

    bench = sub.add_parser("benchmark", help="run deterministic corpus benchmark")
    bench.add_argument("--count", type=int, default=250)
    bench.add_argument("--depth", type=int, default=5)
    bench.add_argument("--seed", type=int, default=20260413)
    bench.add_argument("--out", type=Path)

    args = parser.parse_args()

    if args.cmd == "normalize":
        expr = parse_expr(args.expr)
        nf, trace = normalize(expr)
        parity = parity_check(expr, nf)
        data = {
            "input": expr.pretty(),
            "normal_form": nf.pretty(),
            "trace": trace,
            "parity": parity,
            "scope": "restricted c111 rewrite theory, not full Boolean equivalence",
        }
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(f"input:       {data['input']}")
            print(f"normal form: {data['normal_form']}")
            print(f"steps:       {len(trace)}")
            print(f"parity:      {parity}")
        return 0 if parity["ok"] else 1

    if args.cmd == "benchmark":
        data = run_benchmark(args.count, args.depth, args.seed)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0 if not data["parity_failures"] else 1

    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
