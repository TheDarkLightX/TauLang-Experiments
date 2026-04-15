#!/usr/bin/env python3
"""Epiplexity-style routing experiment for Tau qelim.

This script tests a narrow hypothesis:

  A cheap structure metric can predict when the restricted KB normalizer is
  useful inside Tau's qelim path.

It does not claim that epiplexity is solved, and it does not promote KB into the
default Tau path. The experiment records three separate things:

  1. semantic parity against the unmodified route,
  2. structural simplification signal, measured as expression-node reduction,
  3. timing regret against the locally fastest route in this generated corpus.

The metric is intentionally transparent. It parses the source Boolean formula,
normalizes it with the same restricted rule family used by the KB lane, and
uses the reduction ratio as a syntax-structure signal. BDD root-node compression
is recorded separately as a carrier-structure signal.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from run_qelim_kb_matrix import build_cases


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Mode:
    name: str
    backend: str = "auto"
    kb: str = ""


MODES = [
    Mode("auto", backend="auto"),
    Mode("auto_kb_guarded", backend="auto", kb="guarded"),
    Mode("bdd", backend="bdd"),
    Mode("bdd_kb_guarded", backend="bdd", kb="guarded"),
]


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple["Expr", ...] = ()

    def nodes(self) -> int:
        return 1 + sum(a.nodes() for a in self.args)

    def atoms(self) -> list[str]:
        if not self.args:
            return [] if self.op in {"T", "F"} else [self.op]
        out: list[str] = []
        for arg in self.args:
            out.extend(arg.atoms())
        return out


class Parser:
    def __init__(self, src: str):
        self.tokens = self._tokenize(src)
        self.pos = 0

    @staticmethod
    def _tokenize(src: str) -> list[str]:
        token_re = re.compile(r"\s*(\!|\&\&|\|\||\(|\)|=|0|1|[A-Za-z_][A-Za-z0-9_]*)")
        out: list[str] = []
        i = 0
        while i < len(src):
            m = token_re.match(src, i)
            if not m:
                raise ValueError(f"cannot tokenize near: {src[i:i+40]!r}")
            out.append(m.group(1))
            i = m.end()
        return out

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self, tok: str | None = None) -> str:
        if self.pos >= len(self.tokens):
            raise ValueError("unexpected end of formula")
        got = self.tokens[self.pos]
        if tok is not None and got != tok:
            raise ValueError(f"expected {tok!r}, got {got!r}")
        self.pos += 1
        return got

    def parse(self) -> Expr:
        expr = self.parse_or()
        if self.peek() is not None:
            raise ValueError(f"trailing token: {self.peek()!r}")
        return expr

    def parse_or(self) -> Expr:
        lhs = self.parse_and()
        while self.peek() == "||":
            self.take("||")
            lhs = Expr("or", (lhs, self.parse_and()))
        return lhs

    def parse_and(self) -> Expr:
        lhs = self.parse_not()
        while self.peek() == "&&":
            self.take("&&")
            lhs = Expr("and", (lhs, self.parse_not()))
        return lhs

    def parse_not(self) -> Expr:
        if self.peek() == "!":
            self.take("!")
            return Expr("not", (self.parse_not(),))
        return self.parse_atom()

    def parse_atom(self) -> Expr:
        if self.peek() == "(":
            self.take("(")
            # Either a parenthesized expression, or an atom of shape (x = 0).
            if (
                self.pos + 2 < len(self.tokens)
                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.tokens[self.pos])
                and self.tokens[self.pos + 1] == "="
            ):
                name = self.take()
                self.take("=")
                value = self.take()
                self.take(")")
                return Expr(f"{name}={value}")
            inner = self.parse_or()
            self.take(")")
            return inner
        name = self.take()
        if name in {"true", "T", "1"}:
            return Expr("T")
        if name in {"false", "F", "0"}:
            return Expr("F")
        if self.peek() == "=":
            self.take("=")
            value = self.take()
            return Expr(f"{name}={value}")
        return Expr(name)


def expr_key(e: Expr) -> tuple:
    return (e.op, tuple(expr_key(a) for a in e.args))


def contains_expr(haystack: Expr, needle: Expr) -> bool:
    if expr_key(haystack) == expr_key(needle):
        return True
    return any(contains_expr(a, needle) for a in haystack.args)


def normalize_once(e: Expr) -> tuple[Expr, dict[str, int]]:
    counts = {"idempotent": 0, "absorption": 0, "double_neg": 0, "demorgan": 0}
    if not e.args:
        return e, counts

    args = []
    for arg in e.args:
        norm, sub = normalize_once(arg)
        args.append(norm)
        for k, v in sub.items():
            counts[k] += v
    e = Expr(e.op, tuple(args))

    if e.op == "not":
        child = e.args[0]
        if child.op == "not":
            counts["double_neg"] += 1
            return child.args[0], counts
        if child.op == "and":
            counts["demorgan"] += 1
            return Expr("or", (Expr("not", (child.args[0],)), Expr("not", (child.args[1],)))), counts
        if child.op == "or":
            counts["demorgan"] += 1
            return Expr("and", (Expr("not", (child.args[0],)), Expr("not", (child.args[1],)))), counts
        return e, counts

    if e.op in {"and", "or"}:
        a, b = e.args
        if expr_key(a) == expr_key(b):
            counts["idempotent"] += 1
            return a, counts
        if e.op == "and":
            if b.op == "or" and (contains_expr(b.args[0], a) or contains_expr(b.args[1], a)):
                counts["absorption"] += 1
                return a, counts
            if a.op == "or" and (contains_expr(a.args[0], b) or contains_expr(a.args[1], b)):
                counts["absorption"] += 1
                return b, counts
        if e.op == "or":
            if b.op == "and" and (contains_expr(b.args[0], a) or contains_expr(b.args[1], a)):
                counts["absorption"] += 1
                return a, counts
            if a.op == "and" and (contains_expr(a.args[0], b) or contains_expr(a.args[1], b)):
                counts["absorption"] += 1
                return b, counts
    return e, counts


def normalize(e: Expr, limit: int = 100) -> tuple[Expr, dict[str, int]]:
    total = {"idempotent": 0, "absorption": 0, "double_neg": 0, "demorgan": 0}
    cur = e
    for _ in range(limit):
        nxt, counts = normalize_once(cur)
        for k, v in counts.items():
            total[k] += v
        if expr_key(nxt) == expr_key(cur):
            return cur, total
        cur = nxt
    raise RuntimeError("normalizer did not converge inside local limit")


def extract_body(command: str) -> str:
    rest = command.strip()
    if not rest.startswith("qelim "):
        raise ValueError(f"expected qelim command: {command}")
    rest = rest[len("qelim ") :].strip()
    while rest.startswith("ex "):
        parts = rest.split(maxsplit=2)
        if len(parts) < 3:
            raise ValueError(f"missing qelim body: {command}")
        rest = parts[2].strip()
    return rest


def syntax_metrics(command: str) -> dict[str, object]:
    body = extract_body(command)
    expr = Parser(body).parse()
    norm, counts = normalize(expr)
    atoms = expr.atoms()
    source_nodes = expr.nodes()
    normalized_nodes = norm.nodes()
    reduction = max(0, source_nodes - normalized_nodes)
    repeat_ratio = 0.0
    if atoms:
        repeat_ratio = 1.0 - (len(set(atoms)) / len(atoms))
    syntax_gain = reduction / source_nodes if source_nodes else 0.0
    # Current Tau guarded KB is absorption-aligned. De Morgan is still recorded
    # as a source feature, but the current guard does not reliably run on pure
    # De Morgan shapes after Tau's earlier compilation simplifications.
    guard_aligned_detector = counts["absorption"] > 0
    raw_syntax_detector = syntax_gain > 0
    return {
        "body": body,
        "source_nodes": source_nodes,
        "normalized_nodes": normalized_nodes,
        "syntax_gain": round(syntax_gain, 6),
        "atom_occurrences": len(atoms),
        "unique_atoms": len(set(atoms)),
        "atom_repeat_ratio": round(repeat_ratio, 6),
        "rewrite_counts": counts,
        "raw_syntax_detector": raw_syntax_detector,
        "guard_aligned_detector": guard_aligned_detector,
    }


def parse_stats(text: str, prefix: str) -> dict[str, str]:
    line = ""
    for candidate in text.splitlines():
        if candidate.startswith(prefix):
            line = candidate
    return dict(STAT_RE.findall(line))


def as_float(d: dict[str, str], key: str) -> float:
    try:
        return float(d.get(key, "0"))
    except ValueError:
        return 0.0


def as_int(d: dict[str, str], key: str) -> int:
    try:
        return int(float(d.get(key, "0")))
    except ValueError:
        return 0


def run_tau(tau_bin: Path, command: str, mode: Mode) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_QELIM_STATS"] = "1"
    env["TAU_QELIM_BDD_STATS"] = "1"
    env["TAU_QELIM_BACKEND"] = mode.backend
    if mode.kb:
        env["TAU_QELIM_BDD_KB_REWRITE"] = mode.kb
    else:
        env.pop("TAU_QELIM_BDD_KB_REWRITE", None)
    argv = [
        str(tau_bin),
        "--charvar",
        "false",
        "-e",
        command,
        "--severity",
        "info",
        "--color",
        "false",
        "--status",
        "true",
    ]
    start = time.perf_counter()
    proc = subprocess.run(argv, env=env, text=True, capture_output=True, check=False)
    elapsed_ms = (time.perf_counter() - start) * 1000
    combined = proc.stdout + proc.stderr
    qelim_stats = parse_stats(combined, "[qelim_cmd]")
    bdd_stats = parse_stats(combined, "[qelim_bdd]")
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "elapsed_ms": round(elapsed_ms, 3),
        "qelim_total_ms": round(as_float(qelim_stats, "total_ms"), 6),
        "bdd_internal_ms": round(
            as_float(bdd_stats, "compile_ms")
            + as_float(bdd_stats, "project_ms")
            + as_float(bdd_stats, "rebuild_ms"),
            6,
        ),
        "qelim_stats": qelim_stats,
        "bdd_stats": bdd_stats,
    }


def summarize(results: list[dict[str, object]]) -> dict[str, object]:
    def values(key: str) -> list[float]:
        return [float(r[key]) for r in results]

    qelim = values("qelim_total_ms")
    bdd = values("bdd_internal_ms")
    elapsed = values("elapsed_ms")
    before = [as_int(r["bdd_stats"], "kb_before_nodes") for r in results]  # type: ignore[arg-type]
    after = [as_int(r["bdd_stats"], "kb_after_nodes") for r in results]  # type: ignore[arg-type]
    root = [as_int(r["bdd_stats"], "root_nodes") for r in results]  # type: ignore[arg-type]
    projected = [as_int(r["bdd_stats"], "projected_nodes") for r in results]  # type: ignore[arg-type]
    return {
        "runs": len(results),
        "returncodes": sorted({int(r["returncode"]) for r in results}),
        "qelim_total_ms_median": round(statistics.median(qelim), 6) if qelim else 0,
        "qelim_total_ms_sum": round(sum(qelim), 6),
        "bdd_internal_ms_median": round(statistics.median(bdd), 6) if bdd else 0,
        "bdd_internal_ms_sum": round(sum(bdd), 6),
        "elapsed_ms_median": round(statistics.median(elapsed), 3) if elapsed else 0,
        "kb_before_nodes_sum": sum(before),
        "kb_after_nodes_sum": sum(after),
        "kb_steps_sum": sum(as_int(r["bdd_stats"], "kb_steps") for r in results),  # type: ignore[arg-type]
        "kb_guard_ran_sum": sum(as_int(r["bdd_stats"], "kb_guard_ran") for r in results),  # type: ignore[arg-type]
        "root_nodes_median": statistics.median(root) if root else 0,
        "projected_nodes_median": statistics.median(projected) if projected else 0,
    }


def extra_cases() -> list[dict[str, str]]:
    def a(name: str) -> str:
        return f"({name} = 0)"

    return [
        {"name": "irrelevant_quantifier", "command": f"qelim ex x {a('a')}"},
        {"name": "tautology_quantifier", "command": f"qelim ex x ({a('x')} || !{a('x')})"},
        {"name": "contradiction_quantifier", "command": f"qelim ex x ({a('x')} && !{a('x')})"},
        {
            "name": "commuted_duplicate_pair",
            "command": f"qelim ex x (({a('x')} && {a('a')}) || ({a('a')} && {a('x')}))",
        },
        {
            "name": "carrier_collapse_wide_tautology",
            "command": "qelim ex x ex y ex z "
            + " && ".join([f"({a(v)} || !{a(v)})" for v in ["x", "y", "z", "a", "b"]]),
        },
        {
            "name": "carrier_collapse_wide_contradiction",
            "command": "qelim ex x ex y ex z "
            + " || ".join([f"({a(v)} && !{a(v)})" for v in ["x", "y", "z", "a", "b"]]),
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-epiplexity-router.json"))
    parser.add_argument("--max-generated-cases", type=int, default=34)
    parser.add_argument("--reps", type=int, default=5)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    cases = build_cases(args.max_generated_cases) + extra_cases()
    rows: list[dict[str, object]] = []
    ok = True
    total_auto_regret = 0.0
    total_bdd_regret = 0.0
    median_auto_regret = 0.0
    median_bdd_regret = 0.0
    detector_true = 0
    detector_false = 0
    detector_node_tp = detector_node_fp = detector_node_tn = detector_node_fn = 0
    detector_work_tp = detector_work_fp = detector_work_tn = detector_work_fn = 0
    raw_detector_node_tp = raw_detector_node_fp = raw_detector_node_tn = raw_detector_node_fn = 0

    for case in cases:
        metrics = syntax_metrics(case["command"])
        case_runs: dict[str, list[dict[str, object]]] = {m.name: [] for m in MODES}
        for _ in range(args.reps):
            for mode in MODES:
                case_runs[mode.name].append(run_tau(args.tau_bin, case["command"], mode))

        baseline_stdout = case_runs["auto"][0]["stdout"]
        baseline_rc = case_runs["auto"][0]["returncode"]
        parity = {
            name: all(r["stdout"] == baseline_stdout and r["returncode"] == baseline_rc for r in runs)
            for name, runs in case_runs.items()
        }
        ok = ok and all(parity.values()) and baseline_rc == 0

        summaries = {name: summarize(runs) for name, runs in case_runs.items()}
        base_bdd = summaries["bdd"]
        kb_bdd = summaries["bdd_kb_guarded"]
        base_auto = summaries["auto"]
        kb_auto = summaries["auto_kb_guarded"]

        source_nodes = int(metrics["source_nodes"])
        root_nodes = float(base_bdd["root_nodes_median"])
        carrier_gain = max(0.0, 1.0 - (root_nodes / max(1, source_nodes)))
        syntax_detector = bool(metrics["guard_aligned_detector"])
        raw_syntax_detector = bool(metrics["raw_syntax_detector"])
        if syntax_detector:
            detector_true += 1
        else:
            detector_false += 1

        kb_work = int(kb_bdd["kb_steps_sum"]) > 0 or int(kb_bdd["kb_guard_ran_sum"]) > 0
        node_reduction = int(kb_bdd["kb_before_nodes_sum"]) > int(kb_bdd["kb_after_nodes_sum"])
        if syntax_detector and kb_work:
            detector_work_tp += 1
        elif syntax_detector and not kb_work:
            detector_work_fp += 1
        elif (not syntax_detector) and kb_work:
            detector_work_fn += 1
        else:
            detector_work_tn += 1

        if raw_syntax_detector and node_reduction:
            raw_detector_node_tp += 1
        elif raw_syntax_detector and not node_reduction:
            raw_detector_node_fp += 1
        elif (not raw_syntax_detector) and node_reduction:
            raw_detector_node_fn += 1
        else:
            raw_detector_node_tn += 1

        if syntax_detector and node_reduction:
            detector_node_tp += 1
        elif syntax_detector and not node_reduction:
            detector_node_fp += 1
        elif (not syntax_detector) and node_reduction:
            detector_node_fn += 1
        else:
            detector_node_tn += 1

        route_auto = "auto_kb_guarded" if syntax_detector else "auto"
        route_bdd = "bdd_kb_guarded" if syntax_detector else "bdd"
        auto_costs_sum = {
            "auto": float(base_auto["qelim_total_ms_sum"]),
            "auto_kb_guarded": float(kb_auto["qelim_total_ms_sum"]),
        }
        bdd_costs_sum = {
            "bdd": float(base_bdd["bdd_internal_ms_sum"]),
            "bdd_kb_guarded": float(kb_bdd["bdd_internal_ms_sum"]),
        }
        auto_costs_median = {
            "auto": float(base_auto["qelim_total_ms_median"]),
            "auto_kb_guarded": float(kb_auto["qelim_total_ms_median"]),
        }
        bdd_costs_median = {
            "bdd": float(base_bdd["bdd_internal_ms_median"]),
            "bdd_kb_guarded": float(kb_bdd["bdd_internal_ms_median"]),
        }
        auto_oracle = min(auto_costs_median, key=auto_costs_median.get)
        bdd_oracle = min(bdd_costs_median, key=bdd_costs_median.get)
        auto_regret = auto_costs_sum[route_auto] - auto_costs_sum[min(auto_costs_sum, key=auto_costs_sum.get)]
        bdd_regret = bdd_costs_sum[route_bdd] - bdd_costs_sum[min(bdd_costs_sum, key=bdd_costs_sum.get)]
        auto_regret_median = auto_costs_median[route_auto] - auto_costs_median[auto_oracle]
        bdd_regret_median = bdd_costs_median[route_bdd] - bdd_costs_median[bdd_oracle]
        total_auto_regret += auto_regret
        total_bdd_regret += bdd_regret
        median_auto_regret += auto_regret_median
        median_bdd_regret += bdd_regret_median

        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "syntax_metrics": metrics,
                "carrier_metrics": {
                    "bdd_root_nodes_median": root_nodes,
                    "bdd_projected_nodes_median": base_bdd["projected_nodes_median"],
                    "carrier_gain_proxy": round(carrier_gain, 6),
                },
                "parity": parity,
                "summaries": summaries,
                "routing": {
                    "raw_syntax_detector": raw_syntax_detector,
                    "guard_aligned_detector": syntax_detector,
                    "kb_work_seen": kb_work,
                    "node_reduction_seen": node_reduction,
                    "auto_route": route_auto,
                    "auto_oracle_by_median": auto_oracle,
                    "auto_oracle_by_sum": min(auto_costs_sum, key=auto_costs_sum.get),
                    "auto_regret_ms_median": round(auto_regret_median, 6),
                    "auto_regret_ms_sum": round(auto_regret, 6),
                    "bdd_route": route_bdd,
                    "bdd_oracle_by_median": bdd_oracle,
                    "bdd_oracle_by_sum": min(bdd_costs_sum, key=bdd_costs_sum.get),
                    "bdd_regret_ms_median": round(bdd_regret_median, 6),
                    "bdd_regret_ms_sum": round(bdd_regret, 6),
                },
            }
        )

    summary = {
        "scope": "patched Tau qelim epiplexity-style routing experiment; generated corpus only",
        "ok": ok,
        "case_count": len(cases),
        "generated_case_count": min(args.max_generated_cases, len(build_cases(args.max_generated_cases))),
        "extra_case_count": len(extra_cases()),
        "reps": args.reps,
        "detector_true": detector_true,
        "detector_false": detector_false,
        "syntax_detector_vs_node_reduction": {
            "true_positive": detector_node_tp,
            "false_positive": detector_node_fp,
            "true_negative": detector_node_tn,
            "false_negative": detector_node_fn,
        },
        "syntax_detector_vs_kb_work": {
            "true_positive": detector_work_tp,
            "false_positive": detector_work_fp,
            "true_negative": detector_work_tn,
            "false_negative": detector_work_fn,
        },
        "raw_syntax_detector_vs_node_reduction": {
            "true_positive": raw_detector_node_tp,
            "false_positive": raw_detector_node_fp,
            "true_negative": raw_detector_node_tn,
            "false_negative": raw_detector_node_fn,
        },
        "route_regret": {
            "auto_median_regret_ms_sum": round(median_auto_regret, 6),
            "bdd_median_regret_ms_sum": round(median_bdd_regret, 6),
            "auto_total_regret_ms_sum": round(total_auto_regret, 6),
            "bdd_total_regret_ms_sum": round(total_bdd_regret, 6),
        },
        "interpretation": [
            "guard-aligned syntax signals predict where the restricted KB normalizer has work to do",
            "node reduction is a stricter target than KB applicability because De Morgan rewrites can widen expressions",
            "node reduction is not the same as a promoted Tau speedup",
            "auto route regret must stay separate from BDD-sublane simplification evidence",
        ],
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
