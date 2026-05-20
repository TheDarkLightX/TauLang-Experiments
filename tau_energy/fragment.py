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
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FRAGMENT_TRAINING_REPORT_SCHEMA = "tau-energy-fragment-training-report-v1"
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
            "expr_ast": expr_to_obj(expr),
            "formula": formula,
            "formula_sha256": hashlib.sha256(formula.encode("utf-8")).hexdigest(),
            "profile": profile,
            "expected_status": expected_status,
            "oracle_route": oracle_route(profile),
        })
    return cases


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


def dumps_fragment_report(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
