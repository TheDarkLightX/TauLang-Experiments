"""Synthetic Tau formula corpus and fragment-route energy training.

The model in this module learns route ordering from Tau-checked synthetic
formulas. It is advisory only: a low-energy route may be checked before another
route, but Tau or a route-specific certificate remains the authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FRAGMENT_TRAINING_REPORT_SCHEMA = "tau-energy-fragment-training-report-v1"
MEASURED_FRAGMENT_TRAINING_REPORT_SCHEMA = "tau-energy-measured-fragment-training-report-v1"
FRAGMENT_ROUTES: tuple[str, ...] = (
    "read_once_structural",
    "small_truth_table_or_certificate",
    "ordered_bdd_route",
    "tseitin_sat_crosscheck",
    "tau_native_default",
    "unchecked_no_tau_negative",
)
FRAGMENT_FEATURE_NAMES: tuple[str, ...] = (
    "size_pressure",
    "depth_pressure",
    "variable_pressure",
    "dimacs_pressure",
    "read_once",
    "has_repeated_vars",
    "small_truth_table_shape",
    "ordered_bdd_shape",
    "tseitin_shape",
    "tau_native_shape",
    "has_quantifier",
    "and_ratio",
    "or_ratio",
    "not_ratio",
    "candidate_read_once_structural",
    "candidate_small_truth_table_or_certificate",
    "candidate_ordered_bdd_route",
    "candidate_tseitin_sat_crosscheck",
    "candidate_tau_native_default",
    "candidate_unchecked_no_tau_negative",
    "applicable_read_once_structural",
    "applicable_small_truth_table_or_certificate",
    "applicable_ordered_bdd_route",
    "applicable_tseitin_sat_crosscheck",
    "applicable_tau_native_default",
    "unsafe_no_tau_check",
)


@dataclass(frozen=True)
class BoolExpr:
    op: str
    args: tuple["BoolExpr", ...] = ()
    name: str = ""
    value: bool = False

    @staticmethod
    def var(name: str) -> "BoolExpr":
        return BoolExpr("var", name=name)

    @staticmethod
    def const(value: bool) -> "BoolExpr":
        return BoolExpr("const", value=value)

    @staticmethod
    def neg(expr: "BoolExpr") -> "BoolExpr":
        return BoolExpr("not", (expr,))

    @staticmethod
    def conj(left: "BoolExpr", right: "BoolExpr") -> "BoolExpr":
        return BoolExpr("and", (left, right))

    @staticmethod
    def disj(left: "BoolExpr", right: "BoolExpr") -> "BoolExpr":
        return BoolExpr("or", (left, right))


@dataclass(frozen=True)
class FragmentEnergyModel:
    weights: dict[str, float]
    bias: float = 2.5
    model_id: str = "tau-fragment-energy-hand-route-prior-v0"
    trained: bool = False
    training_rows: int = 0

    def energy(self, features: dict[str, float]) -> float:
        vector = fragment_feature_vector(features)
        value = self.bias
        if vector["unsafe_no_tau_check"] >= 0.5:
            value += 6.0
        for name in FRAGMENT_FEATURE_NAMES:
            value += self.weights.get(name, 0.0) * vector[name]
        return round(value, 6)

    def rank(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = [
            {
                "case_id": row["case_id"],
                "candidate_route": row["candidate_route"],
                "features": fragment_feature_vector(row["features"]),
                "energy": self.energy(row["features"]),
            }
            for row in rows
        ]
        ranked.sort(key=lambda row: (float(row["energy"]), str(row["candidate_route"])))
        return ranked

    def card(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "trained": self.trained,
            "training_rows": self.training_rows,
            "feature_names": list(FRAGMENT_FEATURE_NAMES),
            "authority": "advisory route ordering only; Tau and route certificates decide",
        }


def fragment_feature_vector(features: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name in FRAGMENT_FEATURE_NAMES:
        value = float(features.get(name, 0.0))
        out[name] = min(1.0, max(0.0, value))
    return out


def expr_size(expr: BoolExpr) -> int:
    return 1 + sum(expr_size(arg) for arg in expr.args)


def expr_depth(expr: BoolExpr) -> int:
    if not expr.args:
        return 1
    return 1 + max(expr_depth(arg) for arg in expr.args)


def op_counts(expr: BoolExpr) -> Counter[str]:
    out: Counter[str] = Counter([expr.op])
    for arg in expr.args:
        out.update(op_counts(arg))
    return out


def var_counts(expr: BoolExpr) -> Counter[str]:
    out: Counter[str] = Counter()
    if expr.op == "var":
        out[expr.name] += 1
    for arg in expr.args:
        out.update(var_counts(arg))
    return out


def is_read_once(expr: BoolExpr) -> bool:
    return all(count <= 1 for count in var_counts(expr).values())


def eval_expr(expr: BoolExpr, env: dict[str, bool]) -> bool:
    if expr.op == "var":
        return env[expr.name]
    if expr.op == "const":
        return expr.value
    if expr.op == "not":
        return not eval_expr(expr.args[0], env)
    if expr.op == "and":
        return eval_expr(expr.args[0], env) and eval_expr(expr.args[1], env)
    if expr.op == "or":
        return eval_expr(expr.args[0], env) or eval_expr(expr.args[1], env)
    raise ValueError(f"unknown op: {expr.op}")


def brute_force_sat(expr: BoolExpr, variables: list[str]) -> bool:
    for mask in range(1 << len(variables)):
        env = {name: bool((mask >> index) & 1) for index, name in enumerate(variables)}
        if eval_expr(expr, env):
            return True
    return False


def can_true_false(expr: BoolExpr) -> tuple[bool, bool]:
    if expr.op == "var":
        return True, True
    if expr.op == "const":
        return expr.value, not expr.value
    if expr.op == "not":
        can_true, can_false = can_true_false(expr.args[0])
        return can_false, can_true
    if expr.op == "and":
        left_true, left_false = can_true_false(expr.args[0])
        right_true, right_false = can_true_false(expr.args[1])
        return left_true and right_true, left_false or right_false
    if expr.op == "or":
        left_true, left_false = can_true_false(expr.args[0])
        right_true, right_false = can_true_false(expr.args[1])
        return left_true or right_true, left_false and right_false
    raise ValueError(f"unknown op: {expr.op}")


class TseitinCounter:
    def __init__(self, variables: list[str]) -> None:
        self.var_ids = {name: index + 1 for index, name in enumerate(variables)}
        self.next_id = len(variables) + 1
        self.clauses = 0

    def fresh(self) -> int:
        out = self.next_id
        self.next_id += 1
        return out

    def encode(self, expr: BoolExpr) -> int:
        if expr.op == "var":
            return self.var_ids[expr.name]
        node = self.fresh()
        if expr.op == "const":
            self.clauses += 1
            return node
        if expr.op == "not":
            self.encode(expr.args[0])
            self.clauses += 2
            return node
        if expr.op in {"and", "or"}:
            self.encode(expr.args[0])
            self.encode(expr.args[1])
            self.clauses += 3
            return node
        raise ValueError(f"unknown op: {expr.op}")

    def clause_count(self, expr: BoolExpr) -> int:
        self.encode(expr)
        return self.clauses + 1


class TseitinCNF:
    def __init__(self, variables: list[str]) -> None:
        self.var_ids = {name: index + 1 for index, name in enumerate(variables)}
        self.next_id = len(variables) + 1
        self.clauses: list[list[int]] = []

    def fresh(self) -> int:
        out = self.next_id
        self.next_id += 1
        return out

    def encode(self, expr: BoolExpr) -> int:
        if expr.op == "var":
            return self.var_ids[expr.name]
        node = self.fresh()
        if expr.op == "const":
            self.clauses.append([node if expr.value else -node])
            return node
        if expr.op == "not":
            child = self.encode(expr.args[0])
            self.clauses.append([-node, -child])
            self.clauses.append([node, child])
            return node
        if expr.op == "and":
            left = self.encode(expr.args[0])
            right = self.encode(expr.args[1])
            self.clauses.append([-node, left])
            self.clauses.append([-node, right])
            self.clauses.append([node, -left, -right])
            return node
        if expr.op == "or":
            left = self.encode(expr.args[0])
            right = self.encode(expr.args[1])
            self.clauses.append([node, -left])
            self.clauses.append([node, -right])
            self.clauses.append([-node, left, right])
            return node
        raise ValueError(f"unknown op: {expr.op}")

    def dimacs(self, root: int) -> str:
        clauses = self.clauses + [[root]]
        lines = [f"p cnf {self.next_id - 1} {len(clauses)}"]
        lines.extend(" ".join(str(lit) for lit in clause) + " 0" for clause in clauses)
        return "\n".join(lines) + "\n"


def simplify_expr(expr: BoolExpr) -> BoolExpr:
    if expr.op in {"var", "const"}:
        return expr
    if expr.op == "not":
        child = simplify_expr(expr.args[0])
        if child.op == "const":
            return BoolExpr.const(not child.value)
        if child.op == "not":
            return simplify_expr(child.args[0])
        return BoolExpr.neg(child)
    if expr.op == "and":
        left = simplify_expr(expr.args[0])
        right = simplify_expr(expr.args[1])
        if left.op == "const":
            return right if left.value else BoolExpr.const(False)
        if right.op == "const":
            return left if right.value else BoolExpr.const(False)
        if left == right:
            return left
        return BoolExpr.conj(left, right)
    if expr.op == "or":
        left = simplify_expr(expr.args[0])
        right = simplify_expr(expr.args[1])
        if left.op == "const":
            return BoolExpr.const(True) if left.value else right
        if right.op == "const":
            return BoolExpr.const(True) if right.value else left
        if left == right:
            return left
        return BoolExpr.disj(left, right)
    raise ValueError(f"unknown op: {expr.op}")


def restrict_expr(expr: BoolExpr, name: str, value: bool) -> BoolExpr:
    if expr.op == "var":
        return BoolExpr.const(value) if expr.name == name else expr
    if expr.op == "const":
        return expr
    if expr.op == "not":
        return simplify_expr(BoolExpr.neg(restrict_expr(expr.args[0], name, value)))
    if expr.op == "and":
        return simplify_expr(BoolExpr.conj(
            restrict_expr(expr.args[0], name, value),
            restrict_expr(expr.args[1], name, value),
        ))
    if expr.op == "or":
        return simplify_expr(BoolExpr.disj(
            restrict_expr(expr.args[0], name, value),
            restrict_expr(expr.args[1], name, value),
        ))
    raise ValueError(f"unknown op: {expr.op}")


class OrderedBDD:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.nodes: list[dict[str, Any]] = [
            {"var": None, "low": None, "high": None, "value": False},
            {"var": None, "low": None, "high": None, "value": True},
        ]
        self.unique: dict[tuple[str, int, int], int] = {}
        self.cache: dict[tuple[BoolExpr, int], int] = {}

    def mk(self, var: str, low: int, high: int) -> int:
        if low == high:
            return low
        key = (var, low, high)
        found = self.unique.get(key)
        if found is not None:
            return found
        node_id = len(self.nodes)
        self.nodes.append({"var": var, "low": low, "high": high, "value": None})
        self.unique[key] = node_id
        return node_id

    def compile(self, expr: BoolExpr, index: int = 0) -> int:
        expr = simplify_expr(expr)
        key = (expr, index)
        found = self.cache.get(key)
        if found is not None:
            return found
        if expr.op == "const":
            out = 1 if expr.value else 0
        elif index >= len(self.order):
            raise ValueError("variable order does not cover expression")
        else:
            var = self.order[index]
            low = self.compile(restrict_expr(expr, var, False), index + 1)
            high = self.compile(restrict_expr(expr, var, True), index + 1)
            out = self.mk(var, low, high)
        self.cache[key] = out
        return out

    def has_true(self, node_id: int, seen: set[int] | None = None) -> bool:
        seen = set() if seen is None else seen
        if node_id in seen:
            return False
        seen.add(node_id)
        node = self.nodes[node_id]
        if node["var"] is None:
            return bool(node["value"])
        return self.has_true(int(node["low"]), seen) or self.has_true(int(node["high"]), seen)

    def no_repeat(self, node_id: int, path: frozenset[str] = frozenset()) -> bool:
        node = self.nodes[node_id]
        if node["var"] is None:
            return True
        var = str(node["var"])
        if var in path:
            return False
        next_path = path | {var}
        return self.no_repeat(int(node["low"]), next_path) and self.no_repeat(int(node["high"]), next_path)


def ordered_bdd_sat(expr: BoolExpr, variables: list[str]) -> dict[str, Any]:
    order = sorted(set(variables))
    if not set(var_counts(expr)).issubset(order):
        raise ValueError("variable order does not cover expression")
    compiler = OrderedBDD(order)
    root = compiler.compile(expr)
    return {
        "status": "sat" if compiler.has_true(root) else "unsat",
        "node_count": len(compiler.nodes),
        "no_repeat": compiler.no_repeat(root),
        "order": order,
    }


def tau_atom(name: str) -> str:
    return f"({name} = 0)"


def tau_expr(expr: BoolExpr, fallback_var: str = "x0") -> str:
    if expr.op == "var":
        return tau_atom(expr.name)
    if expr.op == "const":
        atom = tau_atom(fallback_var)
        return f"({atom} || !{atom})" if expr.value else f"({atom} && !{atom})"
    if expr.op == "not":
        return f"!({tau_expr(expr.args[0], fallback_var)})"
    if expr.op == "and":
        return f"({tau_expr(expr.args[0], fallback_var)} && {tau_expr(expr.args[1], fallback_var)})"
    if expr.op == "or":
        return f"({tau_expr(expr.args[0], fallback_var)} || {tau_expr(expr.args[1], fallback_var)})"
    raise ValueError(f"unknown op: {expr.op}")


def expr_to_obj(expr: BoolExpr) -> dict[str, Any]:
    if expr.op == "var":
        return {"var": expr.name}
    if expr.op == "const":
        return {"const": expr.value}
    if expr.op == "not":
        return {"not": expr_to_obj(expr.args[0])}
    if expr.op == "and":
        return {"and": [expr_to_obj(expr.args[0]), expr_to_obj(expr.args[1])]}
    if expr.op == "or":
        return {"or": [expr_to_obj(expr.args[0]), expr_to_obj(expr.args[1])]}
    raise ValueError(f"unknown op: {expr.op}")


def _random_expr(
    rng: random.Random,
    variables: list[str],
    depth: int,
    *,
    leaf_rate: float = 0.22,
) -> BoolExpr:
    if depth <= 0 or rng.random() < leaf_rate:
        if rng.random() < 0.04:
            return BoolExpr.const(rng.choice([True, False]))
        return BoolExpr.var(rng.choice(variables))
    op = rng.choices(["and", "or", "not"], weights=[0.44, 0.44, 0.12], k=1)[0]
    if op == "not":
        return BoolExpr.neg(_random_expr(rng, variables, depth - 1, leaf_rate=leaf_rate))
    left = _random_expr(rng, variables, depth - 1, leaf_rate=leaf_rate)
    right = _random_expr(rng, variables, depth - 1, leaf_rate=leaf_rate)
    return BoolExpr.conj(left, right) if op == "and" else BoolExpr.disj(left, right)


def _read_once_expr(rng: random.Random, variables: list[str]) -> BoolExpr:
    if len(variables) == 1:
        leaf = BoolExpr.var(variables[0])
        return BoolExpr.neg(leaf) if rng.random() < 0.2 else leaf
    split = rng.randint(1, len(variables) - 1)
    left_vars = variables[:split]
    right_vars = variables[split:]
    left = _read_once_expr(rng, left_vars)
    right = _read_once_expr(rng, right_vars)
    return BoolExpr.conj(left, right) if rng.random() < 0.5 else BoolExpr.disj(left, right)


def _generate_expr_for_family(rng: random.Random, family: str) -> tuple[BoolExpr, list[str], str | None]:
    if family == "read_once":
        variables = [f"x{i}" for i in range(rng.randint(5, 12))]
        rng.shuffle(variables)
        return _read_once_expr(rng, variables), sorted(variables), None
    if family == "small_truth":
        variables = [f"x{i}" for i in range(rng.randint(2, 5))]
        return _random_expr(rng, variables, rng.randint(3, 5)), variables, None
    if family == "ordered_bdd":
        variables = [f"x{i}" for i in range(rng.randint(8, 14))]
        guard = BoolExpr.var(variables[0])
        tail_a = _random_expr(rng, variables[1:6], rng.randint(3, 5))
        tail_b = _random_expr(rng, variables[3:8], rng.randint(3, 5))
        expr = BoolExpr.disj(BoolExpr.conj(guard, tail_a), BoolExpr.conj(BoolExpr.neg(guard), tail_b))
        return expr, variables, None
    if family == "tseitin":
        variables = [f"x{i}" for i in range(rng.randint(17, 24))]
        return _random_expr(rng, variables, rng.randint(4, 6)), variables, None
    if family == "quantified":
        variables = [f"x{i}" for i in range(rng.randint(2, 5))]
        return _random_expr(rng, variables, rng.randint(2, 4)), variables, rng.choice(["ex", "all"])
    raise ValueError(f"unknown synthetic family: {family}")


def formula_profile(expr: BoolExpr, variables: list[str], quantifier: str | None) -> dict[str, Any]:
    size = expr_size(expr)
    depth = expr_depth(expr)
    counts = var_counts(expr)
    ops = op_counts(expr)
    repeated = any(count > 1 for count in counts.values())
    read_once = is_read_once(expr)
    dimacs_clauses = TseitinCounter(variables).clause_count(expr)
    has_quantifier = quantifier is not None
    small_truth = (not has_quantifier) and len(variables) <= 5 and size <= 80
    ordered_bdd = (not has_quantifier) and repeated and 5 < len(variables) <= 16 and size <= 250
    tseitin = (
        (not has_quantifier)
        and not read_once
        and not small_truth
        and not ordered_bdd
    )
    tau_native = has_quantifier
    total_ops = max(1, sum(ops.values()))
    return {
        "schema": "tau-formula-shape-profile-v1",
        "size": size,
        "depth": depth,
        "variables": len(variables),
        "dimacs_clauses": dimacs_clauses,
        "read_once": read_once,
        "has_repeated_vars": repeated,
        "has_quantifier": has_quantifier,
        "quantifier": quantifier,
        "small_truth_table_shape": small_truth,
        "ordered_bdd_shape": ordered_bdd,
        "tseitin_shape": tseitin,
        "tau_native_shape": tau_native,
        "op_counts": dict(sorted(ops.items())),
        "and_ratio": round(ops["and"] / total_ops, 6),
        "or_ratio": round(ops["or"] / total_ops, 6),
        "not_ratio": round(ops["not"] / total_ops, 6),
    }


def tau_formula_text(expr: BoolExpr, variables: list[str], quantifier: str | None) -> str:
    text = tau_expr(expr, variables[0] if variables else "x0")
    if quantifier:
        return f"{quantifier} {variables[0]} ({text})"
    return text


def oracle_route(profile: dict[str, Any]) -> str:
    if profile["has_quantifier"]:
        return "tau_native_default"
    if profile["read_once"]:
        return "read_once_structural"
    if profile["small_truth_table_shape"]:
        return "small_truth_table_or_certificate"
    if profile["ordered_bdd_shape"]:
        return "ordered_bdd_route"
    if profile["tseitin_shape"]:
        return "tseitin_sat_crosscheck"
    return "tau_native_default"


def route_features(profile: dict[str, Any], route: str) -> dict[str, float]:
    size = float(profile["size"])
    depth = float(profile["depth"])
    variables = float(profile["variables"])
    dimacs = float(profile["dimacs_clauses"])
    features = {
        "size_pressure": math.log1p(size) / math.log1p(260.0),
        "depth_pressure": min(1.0, depth / 12.0),
        "variable_pressure": min(1.0, variables / 24.0),
        "dimacs_pressure": min(1.0, dimacs / 768.0),
        "read_once": 1.0 if profile["read_once"] else 0.0,
        "has_repeated_vars": 1.0 if profile["has_repeated_vars"] else 0.0,
        "small_truth_table_shape": 1.0 if profile["small_truth_table_shape"] else 0.0,
        "ordered_bdd_shape": 1.0 if profile["ordered_bdd_shape"] else 0.0,
        "tseitin_shape": 1.0 if profile["tseitin_shape"] else 0.0,
        "tau_native_shape": 1.0 if profile["tau_native_shape"] else 0.0,
        "has_quantifier": 1.0 if profile["has_quantifier"] else 0.0,
        "and_ratio": float(profile["and_ratio"]),
        "or_ratio": float(profile["or_ratio"]),
        "not_ratio": float(profile["not_ratio"]),
        "unsafe_no_tau_check": 1.0 if route == "unchecked_no_tau_negative" else 0.0,
    }
    for candidate in FRAGMENT_ROUTES:
        features[f"candidate_{candidate}"] = 1.0 if route == candidate else 0.0
    features["applicable_read_once_structural"] = (
        1.0 if route == "read_once_structural" and profile["read_once"] else 0.0
    )
    features["applicable_small_truth_table_or_certificate"] = (
        1.0
        if route == "small_truth_table_or_certificate" and profile["small_truth_table_shape"]
        else 0.0
    )
    features["applicable_ordered_bdd_route"] = (
        1.0 if route == "ordered_bdd_route" and profile["ordered_bdd_shape"] else 0.0
    )
    features["applicable_tseitin_sat_crosscheck"] = (
        1.0 if route == "tseitin_sat_crosscheck" and profile["tseitin_shape"] else 0.0
    )
    features["applicable_tau_native_default"] = (
        1.0 if route == "tau_native_default" and profile["tau_native_shape"] else 0.0
    )
    return fragment_feature_vector(features)


def target_for(route: str, target_route: str) -> tuple[str, float, float]:
    if route == "unchecked_no_tau_negative":
        return "reject_unsafe_no_validation", 6.0, 5.0
    if route == target_route:
        return "oracle_route", 0.0, 2.0
    if route == "tau_native_default":
        return "safe_fallback_not_preferred", 2.2, 1.0
    return "wrong_fragment_route", 3.8, 1.5


def parse_tau_status(text: str) -> str:
    if "solution:" in text:
        return "sat"
    if "no solution" in text:
        return "unsat"
    return "unknown"


def check_tau_formula(
    *,
    tau_bin: Path,
    formula: str,
    timeout_s: int,
) -> dict[str, Any]:
    start = time.perf_counter()
    proc = subprocess.run(
        [
            str(tau_bin),
            "--charvar",
            "false",
            "--severity",
            "error",
            "--color",
            "false",
            "--status",
            "true",
            "-e",
            f"solve --tau {formula}",
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_s,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    combined = proc.stdout + proc.stderr
    ok = proc.returncode == 0 and "(Error)" not in combined
    return {
        "ok": ok,
        "returncode": proc.returncode,
        "tau_status": parse_tau_status(combined),
        "elapsed_ms": round(elapsed_ms, 3),
        "stderr_tail": proc.stderr[-500:] if not ok else "",
    }


def check_tau_command(
    *,
    tau_bin: Path,
    command: str,
    timeout_s: int,
) -> dict[str, Any]:
    start = time.perf_counter()
    proc = subprocess.run(
        [
            str(tau_bin),
            "--charvar",
            "false",
            "--severity",
            "error",
            "--color",
            "false",
            "--status",
            "true",
            "-e",
            command,
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_s,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    combined = proc.stdout + proc.stderr
    ok = proc.returncode == 0 and "(Error)" not in combined
    return {
        "ok": ok,
        "returncode": proc.returncode,
        "tau_status": parse_tau_status(combined),
        "elapsed_ms": round(elapsed_ms, 3),
        "stderr_tail": proc.stderr[-500:] if not ok else "",
    }


def grammar_manifest(root: Path) -> dict[str, Any]:
    paths = [
        root / "external/tau-lang/parser/tau.tgf",
        root / "external/tau-lang/parser/sbf.tgf",
        root / "external/tau-lang/parser/bitvector.tgf",
    ]
    files: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            digest.update(path.as_posix().encode("utf-8"))
            digest.update(data)
            files.append({
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            })
    return {
        "schema": "tau-grammar-manifest-v1",
        "grammar_file_count": len(files),
        "combined_sha256": digest.hexdigest(),
        "files": files,
    }


def generate_fragment_cases(
    *,
    example_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    families = ["read_once", "small_truth", "ordered_bdd", "tseitin", "quantified"]
    cases: list[dict[str, Any]] = []
    for index in range(example_count):
        family = families[index % len(families)]
        rng = random.Random(seed + index * 7919)
        expr, variables, quantifier = _generate_expr_for_family(rng, family)
        profile = formula_profile(expr, variables, quantifier)
        formula = tau_formula_text(expr, variables, quantifier)
        expected_status = (
            "sat" if brute_force_sat(expr, variables) else "unsat"
        ) if quantifier is None and len(variables) <= 12 else None
        cases.append({
            "case_id": f"synthetic_{index:05d}_{family}",
            "family": family,
            "variables": variables,
            "_expr": expr,
            "expr_ast": expr_to_obj(expr),
            "formula": formula,
            "formula_sha256": hashlib.sha256(formula.encode("utf-8")).hexdigest(),
            "profile": profile,
            "expected_status": expected_status,
            "oracle_route": oracle_route(profile),
        })
    return cases


def command_shape_profile(command: str) -> dict[str, Any]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", command)
    distinct_names = {
        word
        for word in words
        if word not in {"solve", "tau", "bv", "sat", "sbf", "true", "false"}
    }
    has_quantifier = any(token in command for token in [" G ", " F ", "[]", "<>", " all ", " ex "])
    return {
        "schema": "tau-command-shape-profile-v1",
        "size": max(1, len(command) // 4),
        "depth": command.count("(") + command.count("["),
        "variables": len(distinct_names),
        "dimacs_clauses": max(1, command.count("&&") + command.count("||") + 1),
        "read_once": False,
        "has_repeated_vars": False,
        "has_quantifier": has_quantifier,
        "quantifier": "command_surface" if has_quantifier else None,
        "small_truth_table_shape": False,
        "ordered_bdd_shape": False,
        "tseitin_shape": False,
        "tau_native_shape": True,
        "op_counts": {
            "and": command.count("&&") + command.count("&"),
            "or": command.count("||") + command.count("|"),
            "not": command.count("!"),
        },
        "and_ratio": 0.0,
        "or_ratio": 0.0,
        "not_ratio": 0.0,
        "source": "real_tau_command",
    }


def extract_solver_command(text: str) -> str | None:
    lines = [line.rstrip() for line in text.splitlines()]
    start_index = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("solve --tau ") or stripped.startswith("solve --bv "):
            start_index = index
            break
    if start_index is None:
        return None
    parts: list[str] = []
    for line in lines[start_index:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts.append(stripped)
    command = " ".join(parts).strip()
    return command or None


def load_real_tau_command_cases(root: Path, *, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "examples/tau/solver_benchmarks").glob("*.tau")):
        command = extract_solver_command(path.read_text(encoding="utf-8"))
        if not command:
            continue
        digest = hashlib.sha256(command.encode("utf-8")).hexdigest()
        rows.append({
            "case_id": f"real_{path.stem}",
            "family": "real_tau_command",
            "source_path": path.relative_to(root).as_posix(),
            "variables": [],
            "_expr": None,
            "expr_ast": None,
            "formula": command,
            "command": command,
            "formula_sha256": digest,
            "profile": command_shape_profile(command),
            "expected_status": None,
            "oracle_route": "tau_native_default",
        })
        if len(rows) >= limit:
            break
    return rows


def build_rows_for_case(case: dict[str, Any], split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target_route = str(case["oracle_route"])
    for route in FRAGMENT_ROUTES:
        label, target, weight = target_for(route, target_route)
        rows.append({
            "schema": "tau-fragment-route-training-row-v1",
            "case_id": case["case_id"],
            "split": split,
            "candidate_route": route,
            "oracle_route": target_route,
            "label": label,
            "target_energy": target,
            "training_weight": weight,
            "features": route_features(case["profile"], route),
            "formula_sha256": case["formula_sha256"],
            "tau_check": case["tau_check"],
        })
    return rows


def measured_target_for(route: str, best_route: str | None, result: dict[str, Any], best_cost: float) -> tuple[str, float, float]:
    if route == "unchecked_no_tau_negative":
        return "reject_unsafe_no_validation", 6.0, 5.0
    if not result.get("valid"):
        return "invalid_or_inapplicable_route", 4.8, 2.5
    if route == best_route:
        return "measured_best_verified_route", 0.0, 2.5
    elapsed = float(result.get("elapsed_ms") or best_cost)
    regret = max(0.0, elapsed - best_cost)
    return "verified_slower_route", min(3.8, 0.8 + math.log1p(regret)), 1.2


def run_minisat_route(expr: BoolExpr, variables: list[str], minisat_bin: str, timeout_s: int) -> dict[str, Any]:
    cnf = TseitinCNF(variables)
    root = cnf.encode(expr)
    dimacs = cnf.dimacs(root)
    with tempfile.TemporaryDirectory(prefix="tau_energy_minisat_") as tmp:
        cnf_path = Path(tmp) / "case.cnf"
        out_path = Path(tmp) / "case.out"
        cnf_path.write_text(dimacs, encoding="utf-8")
        start = time.perf_counter()
        proc = subprocess.run(
            [minisat_bin, str(cnf_path), str(out_path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_s,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
    text = proc.stdout + proc.stderr
    if "UNSATISFIABLE" in text:
        status = "unsat"
    elif "SATISFIABLE" in text:
        status = "sat"
    else:
        status = "unknown"
    return {
        "route": "tseitin_sat_crosscheck",
        "ran": True,
        "status": status,
        "elapsed_ms": round(elapsed_ms, 6),
        "certificate": {
            "kind": "tseitin_dimacs_minisat",
            "dimacs_vars": cnf.next_id - 1,
            "dimacs_clauses": len(cnf.clauses) + 1,
            "returncode": proc.returncode,
        },
    }


def measure_candidate_route(
    *,
    route: str,
    case: dict[str, Any],
    tau_check: dict[str, Any],
    minisat_bin: str,
    route_timeout_s: int,
) -> dict[str, Any]:
    expr = case.get("_expr")
    variables = list(case.get("variables") or [])
    profile = case["profile"]
    tau_status = str(tau_check.get("tau_status"))
    if route == "unchecked_no_tau_negative":
        return {
            "route": route,
            "ran": False,
            "valid": False,
            "status_match": False,
            "elapsed_ms": 0.0,
            "reason": "candidate lacks Tau or route-certificate validation",
        }
    if route == "tau_native_default":
        return {
            "route": route,
            "ran": True,
            "valid": tau_check.get("ok") is True,
            "status": tau_status,
            "status_match": tau_check.get("ok") is True,
            "elapsed_ms": float(tau_check.get("elapsed_ms") or 0.0),
            "certificate": {"kind": "tau_native", "tau_status": tau_status},
        }
    if not isinstance(expr, BoolExpr) or profile.get("has_quantifier"):
        return {
            "route": route,
            "ran": False,
            "valid": False,
            "status_match": False,
            "elapsed_ms": None,
            "reason": "route only applies to finite generated Boolean formulas",
        }
    try:
        if route == "read_once_structural":
            if not profile["read_once"]:
                raise ValueError("not read-once")
            start = time.perf_counter()
            can_true, _ = can_true_false(expr)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            result = {
                "route": route,
                "ran": True,
                "status": "sat" if can_true else "unsat",
                "elapsed_ms": round(elapsed_ms, 6),
                "certificate": {"kind": "read_once", "read_once_guard": True},
            }
        elif route == "small_truth_table_or_certificate":
            if len(variables) > 8:
                raise ValueError("too many variables for bounded truth table")
            start = time.perf_counter()
            sat = brute_force_sat(expr, variables)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            result = {
                "route": route,
                "ran": True,
                "status": "sat" if sat else "unsat",
                "elapsed_ms": round(elapsed_ms, 6),
                "certificate": {"kind": "truth_table", "assignments": 1 << len(variables)},
            }
        elif route == "ordered_bdd_route":
            if len(variables) > 16 or int(profile["size"]) > 250:
                raise ValueError("outside ordered-BDD measurement budget")
            start = time.perf_counter()
            bdd = ordered_bdd_sat(expr, variables)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            result = {
                "route": route,
                "ran": True,
                "status": bdd["status"],
                "elapsed_ms": round(elapsed_ms, 6),
                "certificate": {
                    "kind": "ordered_bdd",
                    "node_count": bdd["node_count"],
                    "no_repeat": bdd["no_repeat"],
                },
            }
        elif route == "tseitin_sat_crosscheck":
            if not minisat_bin:
                raise ValueError("minisat not available")
            result = run_minisat_route(expr, variables, minisat_bin, route_timeout_s)
        else:
            raise ValueError(f"unknown route: {route}")
        status_match = result["status"] == tau_status
        result["valid"] = bool(status_match)
        result["status_match"] = bool(status_match)
        return result
    except Exception as exc:
        return {
            "route": route,
            "ran": False,
            "valid": False,
            "status_match": False,
            "elapsed_ms": None,
            "reason": str(exc),
        }


def measured_rows_for_case(
    *,
    case: dict[str, Any],
    tau_bin: Path,
    minisat_bin: str,
    split: str,
    tau_timeout_s: int,
    route_timeout_s: int,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    command = str(case.get("command") or f"solve --tau {case['formula']}")
    tau_check = check_tau_command(tau_bin=tau_bin, command=command, timeout_s=tau_timeout_s)
    expected_status = case.get("expected_status")
    tau_status_match = expected_status is None or tau_check.get("tau_status") == expected_status
    if tau_check.get("ok") is not True or not tau_status_match:
        return [], {
            "case_id": case["case_id"],
            "family": case["family"],
            "tau_check": tau_check,
            "expected_status": expected_status,
        }
    measured = {
        route: measure_candidate_route(
            route=route,
            case=case,
            tau_check=tau_check,
            minisat_bin=minisat_bin,
            route_timeout_s=route_timeout_s,
        )
        for route in FRAGMENT_ROUTES
    }
    valid_routes = [
        row for row in measured.values()
        if row.get("valid") is True and row["route"] != "unchecked_no_tau_negative"
    ]
    if not valid_routes:
        return [], {
            "case_id": case["case_id"],
            "family": case["family"],
            "tau_check": tau_check,
            "reason": "no valid measured route",
        }
    best = min(valid_routes, key=lambda row: (float(row.get("elapsed_ms") or 1e9), str(row["route"])))
    best_route = str(best["route"])
    best_cost = float(best.get("elapsed_ms") or 0.0)
    rows: list[dict[str, Any]] = []
    for route in FRAGMENT_ROUTES:
        label, target, weight = measured_target_for(route, best_route, measured[route], best_cost)
        rows.append({
            "schema": "tau-measured-fragment-route-training-row-v1",
            "case_id": case["case_id"],
            "split": split,
            "candidate_route": route,
            "oracle_route": best_route,
            "measured_best_route": best_route,
            "label": label,
            "target_energy": target,
            "training_weight": weight,
            "features": route_features(case["profile"], route),
            "formula_sha256": case["formula_sha256"],
            "source_family": case["family"],
            "route_result": measured[route],
            "tau_check": tau_check,
        })
    receipt = {
        "case_id": case["case_id"],
        "family": case["family"],
        "source_path": case.get("source_path"),
        "formula_sha256": case["formula_sha256"],
        "formula_preview": str(case["formula"])[:220],
        "profile": case["profile"],
        "tau_check": tau_check,
        "measured_best_route": best_route,
        "measured_best_elapsed_ms": round(best_cost, 6),
        "route_results": measured,
    }
    return rows, receipt


def hand_fragment_energy_model() -> FragmentEnergyModel:
    weights = {name: 0.0 for name in FRAGMENT_FEATURE_NAMES}
    weights.update({
        "candidate_tau_native_default": -0.35,
        "candidate_tseitin_sat_crosscheck": 0.25,
        "candidate_ordered_bdd_route": 0.45,
        "candidate_small_truth_table_or_certificate": 0.55,
        "candidate_read_once_structural": 0.65,
        "candidate_unchecked_no_tau_negative": 4.5,
        "unsafe_no_tau_check": 4.5,
    })
    return FragmentEnergyModel(weights=weights)


def fit_fragment_energy_model(
    rows: list[dict[str, Any]],
    *,
    epochs: int = 18,
    learning_rate: float = 0.035,
    l2: float = 0.0005,
) -> FragmentEnergyModel:
    weights = {name: 0.0 for name in FRAGMENT_FEATURE_NAMES}
    weights["unsafe_no_tau_check"] = 3.0
    bias = 2.5
    ordered = list(rows)
    for epoch in range(max(1, epochs)):
        rng = random.Random(10_000 + epoch)
        rng.shuffle(ordered)
        for row in ordered:
            features = fragment_feature_vector(row["features"])
            target = float(row["target_energy"])
            row_weight = float(row["training_weight"])
            pred = bias + sum(weights[name] * features[name] for name in FRAGMENT_FEATURE_NAMES)
            if features["unsafe_no_tau_check"] >= 0.5:
                pred += 6.0
            err = row_weight * (pred - target)
            bias -= learning_rate * err
            for name in FRAGMENT_FEATURE_NAMES:
                weights[name] -= learning_rate * (err * features[name] + l2 * weights[name])
    return FragmentEnergyModel(
        weights={name: round(weights[name], 6) for name in FRAGMENT_FEATURE_NAMES},
        bias=round(bias, 6),
        model_id="tau-fragment-energy-linear-fit-v0",
        trained=True,
        training_rows=len(rows),
    )


def evaluate_fragment_model(model: FragmentEnergyModel, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(str(row["case_id"]), []).append(row)
    top1 = 0
    invalid_accept = 0
    calls_to_oracle: list[int] = []
    route_confusion: dict[str, Counter[str]] = {}
    case_reports: list[dict[str, Any]] = []
    for case_id, case_rows in sorted(by_case.items()):
        ranked = model.rank(case_rows)
        labels = {row["candidate_route"]: row["label"] for row in case_rows}
        oracle = str(case_rows[0]["oracle_route"])
        predicted = str(ranked[0]["candidate_route"])
        if predicted == oracle:
            top1 += 1
        if predicted == "unchecked_no_tau_negative":
            invalid_accept += 1
        oracle_rank = next(
            rank
            for rank, row in enumerate(ranked, start=1)
            if row["candidate_route"] == oracle
        )
        calls_to_oracle.append(oracle_rank)
        route_confusion.setdefault(oracle, Counter())[predicted] += 1
        case_reports.append({
            "case_id": case_id,
            "oracle_route": oracle,
            "top_route": predicted,
            "oracle_rank": oracle_rank,
            "top_energy": ranked[0]["energy"],
            "top_label": labels[predicted],
        })
    count = len(by_case)
    return {
        "case_count": count,
        "top1_oracle_route_rate": round(top1 / count, 6) if count else 0.0,
        "mean_calls_to_oracle": round(sum(calls_to_oracle) / count, 6) if count else None,
        "max_calls_to_oracle": max(calls_to_oracle) if calls_to_oracle else None,
        "invalid_accept_count": invalid_accept,
        "route_confusion": {
            route: dict(sorted(counter.items()))
            for route, counter in sorted(route_confusion.items())
        },
        "cases": case_reports[:50],
    }


def build_fragment_training_report(
    *,
    tau_bin: Path | str = Path("external/tau-lang/build-Release/tau"),
    example_count: int = 1000,
    seed: int = 20260520,
    train_fraction: float = 0.8,
    timeout_s: int = 10,
    root: Path | str = Path("."),
) -> dict[str, Any]:
    path = Path(tau_bin)
    if not path.exists():
        raise FileNotFoundError(f"Tau binary not found: {path}")
    if example_count <= 0:
        raise ValueError("example_count must be positive")
    root_path = Path(root)
    raw_cases = generate_fragment_cases(example_count=example_count, seed=seed)
    checked_cases: list[dict[str, Any]] = []
    failed_checks: list[dict[str, Any]] = []
    for case in raw_cases:
        check = check_tau_formula(tau_bin=path, formula=str(case["formula"]), timeout_s=timeout_s)
        status_match = (
            case["expected_status"] is None
            or check["tau_status"] == case["expected_status"]
        )
        checked = {**case, "tau_check": check, "tau_status_match": status_match}
        if check["ok"] and status_match:
            checked_cases.append(checked)
        else:
            failed_checks.append({
                "case_id": case["case_id"],
                "family": case["family"],
                "tau_check": check,
                "expected_status": case["expected_status"],
            })
    split_index = max(1, min(len(checked_cases), int(len(checked_cases) * train_fraction)))
    train_cases = checked_cases[:split_index]
    test_cases = checked_cases[split_index:]
    if not test_cases and train_cases:
        test_cases = train_cases[-1:]
        train_cases = train_cases[:-1] or test_cases
    train_rows = [
        row
        for case in train_cases
        for row in build_rows_for_case(case, "train")
    ]
    test_rows = [
        row
        for case in test_cases
        for row in build_rows_for_case(case, "test")
    ]
    hand = hand_fragment_energy_model()
    fitted = fit_fragment_energy_model(train_rows)
    route_counts = Counter(str(case["oracle_route"]) for case in checked_cases)
    family_counts = Counter(str(case["family"]) for case in checked_cases)
    hand_eval_train = evaluate_fragment_model(hand, train_rows)
    fitted_eval_train = evaluate_fragment_model(fitted, train_rows)
    hand_eval_test = evaluate_fragment_model(hand, test_rows)
    fitted_eval_test = evaluate_fragment_model(fitted, test_rows)
    status = "passed" if checked_cases and not failed_checks else "failed"
    return {
        "schema": FRAGMENT_TRAINING_REPORT_SCHEMA,
        "status": status,
        "authority": {
            "trained_ranker_can_accept": False,
            "tau_checked_every_formula": True,
            "route_certificate_required": True,
            "deterministic_fallback_required": True,
        },
        "training_status": "linear_fragment_route_ranker_fit_from_tau_checked_synthetic_formulas",
        "seed": seed,
        "requested_example_count": example_count,
        "valid_tau_checked_example_count": len(checked_cases),
        "failed_check_count": len(failed_checks),
        "candidate_route_count": len(FRAGMENT_ROUTES),
        "training_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "train_case_count": len(train_cases),
        "test_case_count": len(test_cases),
        "grammar_manifest": grammar_manifest(root_path),
        "oracle_route_counts": dict(sorted(route_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "hand_model": hand.card() | {"weights": hand.weights, "bias": hand.bias},
        "fitted_model": fitted.card() | {"weights": fitted.weights, "bias": fitted.bias},
        "hand_eval_train": hand_eval_train,
        "fitted_eval_train": fitted_eval_train,
        "hand_eval_test": hand_eval_test,
        "fitted_eval_test": fitted_eval_test,
        "improvement": {
            "test_top1_delta": round(
                float(fitted_eval_test["top1_oracle_route_rate"])
                - float(hand_eval_test["top1_oracle_route_rate"]),
                6,
            ),
            "test_mean_calls_delta": round(
                float(hand_eval_test["mean_calls_to_oracle"] or 0.0)
                - float(fitted_eval_test["mean_calls_to_oracle"] or 0.0),
                6,
            ),
            "baseline": "hand route-prior baseline, not a claim about Tau production heuristics",
        },
        "sample_cases": [
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "formula_sha256": case["formula_sha256"],
                "formula_preview": str(case["formula"])[:220],
                "profile": case["profile"],
                "oracle_route": case["oracle_route"],
                "tau_check": case["tau_check"],
            }
            for case in checked_cases[:20]
        ],
        "failed_checks": failed_checks[:20],
        "limits": [
            "The oracle is a synthetic fragment-route oracle over generated formulas.",
            "This tests shape learning and route ordering, not production Tau optimizer replacement.",
            "Promotion requires real Tau benchmark receipts and route-specific soundness certificates.",
        ],
    }


def verify_fragment_training_report(data: dict[str, Any]) -> bool:
    if data.get("schema") != FRAGMENT_TRAINING_REPORT_SCHEMA:
        return False
    if data.get("status") != "passed":
        return False
    if data.get("authority", {}).get("trained_ranker_can_accept") is not False:
        return False
    if data.get("authority", {}).get("tau_checked_every_formula") is not True:
        return False
    if int(data.get("failed_check_count") or 0) != 0:
        return False
    if int(data.get("valid_tau_checked_example_count") or 0) != int(data.get("requested_example_count") or -1):
        return False
    if int(data.get("training_row_count") or 0) <= 0 or int(data.get("test_row_count") or 0) <= 0:
        return False
    fitted = data.get("fitted_eval_test", {})
    hand = data.get("hand_eval_test", {})
    return bool(
        int(fitted.get("invalid_accept_count", -1)) == 0
        and float(fitted.get("top1_oracle_route_rate") or 0.0) >= float(hand.get("top1_oracle_route_rate") or 0.0)
        and float(data.get("improvement", {}).get("test_top1_delta") or 0.0) >= 0.0
        and int(data.get("grammar_manifest", {}).get("grammar_file_count") or 0) > 0
        and len(data.get("oracle_route_counts", {})) >= 4
    )


def build_measured_fragment_training_report(
    *,
    tau_bin: Path | str = Path("external/tau-lang/build-Release/tau"),
    example_count: int = 250,
    seed: int = 20260522,
    train_fraction: float = 0.8,
    tau_timeout_s: int = 10,
    route_timeout_s: int = 10,
    real_spec_limit: int = 4,
    minisat_bin: str | None = None,
    root: Path | str = Path("."),
) -> dict[str, Any]:
    path = Path(tau_bin)
    if not path.exists():
        raise FileNotFoundError(f"Tau binary not found: {path}")
    root_path = Path(root)
    selected_minisat = minisat_bin if minisat_bin is not None else (shutil.which("minisat") or "")
    synthetic = generate_fragment_cases(example_count=example_count, seed=seed)
    real_cases = load_real_tau_command_cases(root_path, limit=real_spec_limit)
    cases = [*synthetic, *real_cases]
    rng = random.Random(seed + 404)
    rng.shuffle(cases)
    split_index = max(1, min(len(cases), int(len(cases) * train_fraction)))
    split_cases = [
        (case, "train" if index < split_index else "test")
        for index, case in enumerate(cases)
    ]
    if all(split == "train" for _, split in split_cases) and split_cases:
        case, _ = split_cases[-1]
        split_cases[-1] = (case, "test")

    train_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    failed_checks: list[dict[str, Any]] = []
    for case, split in split_cases:
        rows, receipt_or_failure = measured_rows_for_case(
            case=case,
            tau_bin=path,
            minisat_bin=selected_minisat,
            split=split,
            tau_timeout_s=tau_timeout_s,
            route_timeout_s=route_timeout_s,
        )
        if not rows:
            if receipt_or_failure is not None:
                failed_checks.append(receipt_or_failure)
            continue
        if split == "train":
            train_rows.extend(rows)
        else:
            test_rows.extend(rows)
        if receipt_or_failure is not None:
            receipts.append(receipt_or_failure)

    hand = hand_fragment_energy_model()
    fitted = fit_fragment_energy_model(train_rows)
    hand_eval_train = evaluate_fragment_model(hand, train_rows)
    fitted_eval_train = evaluate_fragment_model(fitted, train_rows)
    hand_eval_test = evaluate_fragment_model(hand, test_rows)
    fitted_eval_test = evaluate_fragment_model(fitted, test_rows)
    route_counts = Counter(str(receipt["measured_best_route"]) for receipt in receipts)
    family_counts = Counter(str(receipt["family"]) for receipt in receipts)
    status = "passed" if receipts and not failed_checks and train_rows and test_rows else "failed"
    return {
        "schema": MEASURED_FRAGMENT_TRAINING_REPORT_SCHEMA,
        "status": status,
        "authority": {
            "trained_ranker_can_accept": False,
            "tau_checked_every_formula": True,
            "route_certificate_required": True,
            "measured_route_labels_required": True,
            "deterministic_fallback_required": True,
        },
        "training_status": "linear_fragment_route_ranker_fit_from_measured_tau_verified_routes",
        "seed": seed,
        "requested_example_count": len(cases),
        "requested_synthetic_count": example_count,
        "requested_real_spec_limit": real_spec_limit,
        "valid_tau_checked_example_count": len(receipts),
        "failed_check_count": len(failed_checks),
        "candidate_route_count": len(FRAGMENT_ROUTES),
        "training_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "train_case_count": len({row["case_id"] for row in train_rows}),
        "test_case_count": len({row["case_id"] for row in test_rows}),
        "minisat_available": bool(selected_minisat),
        "minisat_bin": selected_minisat,
        "grammar_manifest": grammar_manifest(root_path),
        "measured_best_route_counts": dict(sorted(route_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "hand_model": hand.card() | {"weights": hand.weights, "bias": hand.bias},
        "fitted_model": fitted.card() | {"weights": fitted.weights, "bias": fitted.bias},
        "hand_eval_train": hand_eval_train,
        "fitted_eval_train": fitted_eval_train,
        "hand_eval_test": hand_eval_test,
        "fitted_eval_test": fitted_eval_test,
        "improvement": {
            "test_top1_delta": round(
                float(fitted_eval_test["top1_oracle_route_rate"])
                - float(hand_eval_test["top1_oracle_route_rate"]),
                6,
            ),
            "test_mean_calls_delta": round(
                float(hand_eval_test["mean_calls_to_oracle"] or 0.0)
                - float(fitted_eval_test["mean_calls_to_oracle"] or 0.0),
                6,
            ),
            "baseline": "hand route-prior baseline inside this workbench",
            "label_source": "fastest route whose deterministic result matched Tau status",
        },
        "sample_receipts": receipts[:20],
        "failed_checks": failed_checks[:20],
        "limits": [
            "Measured labels optimize route choice for this bounded candidate family.",
            "Tau status remains the acceptance authority for each formula.",
            "Route-specific certificates are used only for route result checks, not semantic promotion.",
        ],
    }


def verify_measured_fragment_training_report(data: dict[str, Any]) -> bool:
    if data.get("schema") != MEASURED_FRAGMENT_TRAINING_REPORT_SCHEMA:
        return False
    if data.get("status") != "passed":
        return False
    authority = data.get("authority", {})
    if authority.get("trained_ranker_can_accept") is not False:
        return False
    if authority.get("tau_checked_every_formula") is not True:
        return False
    if authority.get("measured_route_labels_required") is not True:
        return False
    if int(data.get("failed_check_count") or 0) != 0:
        return False
    if int(data.get("valid_tau_checked_example_count") or 0) != int(data.get("requested_example_count") or -1):
        return False
    if int(data.get("training_row_count") or 0) <= 0 or int(data.get("test_row_count") or 0) <= 0:
        return False
    fitted = data.get("fitted_eval_test", {})
    hand = data.get("hand_eval_test", {})
    return bool(
        int(fitted.get("invalid_accept_count", -1)) == 0
        and float(fitted.get("top1_oracle_route_rate") or 0.0) >= float(hand.get("top1_oracle_route_rate") or 0.0)
        and float(data.get("improvement", {}).get("test_top1_delta") or 0.0) >= 0.0
        and int(data.get("grammar_manifest", {}).get("grammar_file_count") or 0) > 0
        and len(data.get("measured_best_route_counts", {})) >= 3
    )


def fragment_training_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": data.get("status"),
        "training_status": data.get("training_status"),
        "requested_example_count": data.get("requested_example_count"),
        "valid_tau_checked_example_count": data.get("valid_tau_checked_example_count"),
        "failed_check_count": data.get("failed_check_count"),
        "training_row_count": data.get("training_row_count"),
        "test_row_count": data.get("test_row_count"),
        "oracle_route_counts": data.get("oracle_route_counts"),
        "hand_test_top1": data.get("hand_eval_test", {}).get("top1_oracle_route_rate"),
        "fitted_test_top1": data.get("fitted_eval_test", {}).get("top1_oracle_route_rate"),
        "fitted_test_mean_calls_to_oracle": data.get("fitted_eval_test", {}).get("mean_calls_to_oracle"),
        "test_top1_delta": data.get("improvement", {}).get("test_top1_delta"),
        "test_mean_calls_delta": data.get("improvement", {}).get("test_mean_calls_delta"),
        "invalid_accept_count": data.get("fitted_eval_test", {}).get("invalid_accept_count"),
    }


def measured_fragment_training_summary(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": data.get("status"),
        "training_status": data.get("training_status"),
        "requested_example_count": data.get("requested_example_count"),
        "valid_tau_checked_example_count": data.get("valid_tau_checked_example_count"),
        "failed_check_count": data.get("failed_check_count"),
        "training_row_count": data.get("training_row_count"),
        "test_row_count": data.get("test_row_count"),
        "measured_best_route_counts": data.get("measured_best_route_counts"),
        "family_counts": data.get("family_counts"),
        "hand_test_top1": data.get("hand_eval_test", {}).get("top1_oracle_route_rate"),
        "fitted_test_top1": data.get("fitted_eval_test", {}).get("top1_oracle_route_rate"),
        "fitted_test_mean_calls_to_best_route": data.get("fitted_eval_test", {}).get("mean_calls_to_oracle"),
        "test_top1_delta": data.get("improvement", {}).get("test_top1_delta"),
        "test_mean_calls_delta": data.get("improvement", {}).get("test_mean_calls_delta"),
        "invalid_accept_count": data.get("fitted_eval_test", {}).get("invalid_accept_count"),
    }


def dumps_fragment_report(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
