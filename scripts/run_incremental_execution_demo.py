#!/usr/bin/env python3
"""Prototype incremental Tau execution from read sets and partial evaluation.

This is a future-work experiment, not an upstream Tau feature. It models a
small Tau-like Boolean-algebra expression language and checks the contract that
The c118/c119/c123 proof lane suggests:

  if a changed input key is outside an expression's read set, the old cached
  value can be reused; otherwise recompute only the affected ancestors.

The carrier is the four-cell Boolean algebra encoded as a 4-bit mask.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


MASK = 0b1111


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | int | None = None
    args: tuple["Expr", ...] = ()


def const(value: int) -> Expr:
    return Expr("const", value & MASK)


def var(name: str) -> Expr:
    return Expr("var", name)


def common(a: Expr, b: Expr) -> Expr:
    return Expr("common", None, (a, b))


def point_join(a: Expr, b: Expr) -> Expr:
    return Expr("pointJoin", None, (a, b))


def point_compl(a: Expr) -> Expr:
    return Expr("pointCompl", None, (a,))


def choice(g: Expr, then_value: Expr, else_value: Expr) -> Expr:
    return point_join(common(g, then_value), common(point_compl(g), else_value))


def select(g: Expr, x: Expr) -> Expr:
    return common(g, x)


def revise(old: Expr, g: Expr, replacement: Expr) -> Expr:
    return choice(g, replacement, old)


def update(old: Expr, base: Expr, g: Expr, replacement: Expr) -> Expr:
    return point_join(base, revise(old, g, replacement))


def node_count(e: Expr) -> int:
    seen: set[Expr] = set()

    def walk(x: Expr) -> None:
        if x in seen:
            return
        seen.add(x)
        for child in x.args:
            walk(child)

    walk(e)
    return len(seen)


def collect_nodes(e: Expr) -> list[Expr]:
    """Return a deterministic child-before-parent node order.

    This mirrors the stable-node-id table a runtime would need before caching
    values or indexing dependencies.
    """
    seen: set[Expr] = set()
    nodes: list[Expr] = []

    def walk(x: Expr) -> None:
        if x in seen:
            return
        seen.add(x)
        for child in x.args:
            walk(child)
        nodes.append(x)

    walk(e)
    return nodes


def runtime_dependency_plan(e: Expr) -> dict[str, object]:
    """Build a stable-node-id read index for the residual expression."""
    nodes = collect_nodes(e)
    node_ids = {node: i for i, node in enumerate(nodes)}
    read_cache: dict[Expr, set[str]] = {}
    read_sets: dict[int, list[str]] = {}
    dependency_index: dict[str, list[int]] = {}
    for node in nodes:
        node_id = node_ids[node]
        node_reads = sorted(reads(node, read_cache))
        read_sets[node_id] = node_reads
        for key in node_reads:
            dependency_index.setdefault(key, []).append(node_id)
    return {
        "node_count": len(nodes),
        "root_node_id": node_ids[e],
        "read_sets": read_sets,
        "dependency_index": {key: ids for key, ids in sorted(dependency_index.items())},
    }


def build_runtime_cache(nodes: list[Expr], env: dict[str, int]) -> list[int]:
    """Evaluate each node once in child-before-parent order."""
    node_ids = {node: i for i, node in enumerate(nodes)}
    values: list[int] = []
    for node in nodes:
        if node.kind == "const":
            assert isinstance(node.value, int)
            value = node.value & MASK
        elif node.kind == "var":
            assert isinstance(node.value, str)
            value = env[node.value] & MASK
        elif node.kind == "common":
            value = values[node_ids[node.args[0]]] & values[node_ids[node.args[1]]]
        elif node.kind == "pointJoin":
            value = values[node_ids[node.args[0]]] | values[node_ids[node.args[1]]]
        elif node.kind == "pointCompl":
            value = (~values[node_ids[node.args[0]]]) & MASK
        else:
            raise ValueError(f"unknown expression kind: {node.kind}")
        values.append(value)
    return values


def runtime_delta_update(
    nodes: list[Expr],
    old_values: list[int],
    env: dict[str, int],
    dirty_node_ids: set[int],
) -> tuple[int, dict[str, int], list[int]]:
    """Update a runtime cache by recomputing only dirty node IDs.

    The caller supplies dirty IDs from the dependency index. Since nodes are
    child-before-parent, a single forward pass is enough.
    """
    node_ids = {node: i for i, node in enumerate(nodes)}
    values = list(old_values)
    metrics = {"runtime_recomputed_nodes": 0, "runtime_reused_nodes": 0}
    for node_id, node in enumerate(nodes):
        if node_id not in dirty_node_ids:
            metrics["runtime_reused_nodes"] += 1
            continue
        metrics["runtime_recomputed_nodes"] += 1
        if node.kind == "const":
            assert isinstance(node.value, int)
            values[node_id] = node.value & MASK
        elif node.kind == "var":
            assert isinstance(node.value, str)
            values[node_id] = env[node.value] & MASK
        elif node.kind == "common":
            values[node_id] = values[node_ids[node.args[0]]] & values[node_ids[node.args[1]]]
        elif node.kind == "pointJoin":
            values[node_id] = values[node_ids[node.args[0]]] | values[node_ids[node.args[1]]]
        elif node.kind == "pointCompl":
            values[node_id] = (~values[node_ids[node.args[0]]]) & MASK
        else:
            raise ValueError(f"unknown expression kind: {node.kind}")
    return values[-1], metrics, values


def reads(e: Expr, memo: dict[Expr, set[str]] | None = None) -> set[str]:
    if memo is None:
        memo = {}
    if e in memo:
        return memo[e]
    if e.kind == "const":
        result: set[str] = set()
    elif e.kind == "var":
        assert isinstance(e.value, str)
        result = {e.value}
    else:
        result = set()
        for child in e.args:
            result |= reads(child, memo)
    memo[e] = result
    return result


def eval_expr(e: Expr, env: dict[str, int], counter: dict[str, int] | None = None) -> int:
    if counter is not None:
        counter["eval_nodes"] = counter.get("eval_nodes", 0) + 1
    if e.kind == "const":
        assert isinstance(e.value, int)
        return e.value & MASK
    if e.kind == "var":
        assert isinstance(e.value, str)
        return env[e.value] & MASK
    if e.kind == "common":
        return eval_expr(e.args[0], env, counter) & eval_expr(e.args[1], env, counter)
    if e.kind == "pointJoin":
        return eval_expr(e.args[0], env, counter) | eval_expr(e.args[1], env, counter)
    if e.kind == "pointCompl":
        return (~eval_expr(e.args[0], env, counter)) & MASK
    raise ValueError(f"unknown expression kind: {e.kind}")


def build_cache(e: Expr, env: dict[str, int]) -> dict[Expr, int]:
    cache: dict[Expr, int] = {}

    def walk(x: Expr) -> int:
        if x in cache:
            return cache[x]
        if x.kind == "const":
            assert isinstance(x.value, int)
            value = x.value & MASK
        elif x.kind == "var":
            assert isinstance(x.value, str)
            value = env[x.value] & MASK
        elif x.kind == "common":
            value = walk(x.args[0]) & walk(x.args[1])
        elif x.kind == "pointJoin":
            value = walk(x.args[0]) | walk(x.args[1])
        elif x.kind == "pointCompl":
            value = (~walk(x.args[0])) & MASK
        else:
            raise ValueError(f"unknown expression kind: {x.kind}")
        cache[x] = value
        return value

    walk(e)
    return cache


def incremental_eval(
    e: Expr,
    env: dict[str, int],
    old_cache: dict[Expr, int],
    changed_key: str,
    read_cache: dict[Expr, set[str]],
) -> tuple[int, dict[str, int]]:
    metrics = {"recomputed_nodes": 0, "reused_nodes": 0}
    new_cache: dict[Expr, int] = {}

    def walk(x: Expr) -> int:
        if x in new_cache:
            return new_cache[x]
        if changed_key not in reads(x, read_cache):
            metrics["reused_nodes"] += 1
            value = old_cache[x]
            new_cache[x] = value
            return value
        metrics["recomputed_nodes"] += 1
        if x.kind == "const":
            assert isinstance(x.value, int)
            value = x.value & MASK
        elif x.kind == "var":
            assert isinstance(x.value, str)
            value = env[x.value] & MASK
        elif x.kind == "common":
            value = walk(x.args[0]) & walk(x.args[1])
        elif x.kind == "pointJoin":
            value = walk(x.args[0]) | walk(x.args[1])
        elif x.kind == "pointCompl":
            value = (~walk(x.args[0])) & MASK
        else:
            raise ValueError(f"unknown expression kind: {x.kind}")
        new_cache[x] = value
        return value

    return walk(e), metrics


def partial_eval(e: Expr, known: dict[str, int]) -> Expr:
    if e.kind == "const":
        return e
    if e.kind == "var":
        assert isinstance(e.value, str)
        return const(known[e.value]) if e.value in known else e
    children = tuple(partial_eval(child, known) for child in e.args)
    return Expr(e.kind, e.value, children)


def env_base() -> dict[str, int]:
    names = [
        "emergency",
        "exploit",
        "oracle",
        "liquidity",
        "governance",
        "normal",
        "freeze",
        "quarantine",
        "slow",
        "cap",
        "review",
        "allow",
        "deny",
        "state",
        "exploit_witness",
        "oracle_alarm",
        "governance_patch",
        "clear_oracle",
        "exploit_region",
        "oracle_region",
        "patch_region",
        "exploit_seed",
        "oracle_seed",
        "patch_label",
        "risk_a",
        "risk_b",
        "risk_c",
        "risk_d",
        "value_a",
        "value_b",
        "value_c",
        "value_d",
        "base",
        "guard",
        "replacement",
        "unused_config",
        "audit_only",
    ]
    return {name: ((i * 7 + 3) & MASK) for i, name in enumerate(names)}


def protocol_firewall() -> Expr:
    rows = [
        ("emergency", "freeze"),
        ("exploit", "quarantine"),
        ("oracle", "slow"),
        ("liquidity", "cap"),
        ("governance", "review"),
        ("normal", "allow"),
    ]
    expr = var("deny")
    for guard_name, value_name in reversed(rows):
        expr = choice(var(guard_name), var(value_name), expr)
    return expr


def incident_memory() -> Expr:
    expr = var("state")
    rows = [
        ("clear_oracle", select(point_compl(var("oracle_region")), var("state"))),
        ("governance_patch", revise(var("state"), var("patch_region"), var("patch_label"))),
        ("oracle_alarm", update(var("state"), var("oracle_seed"), var("oracle_region"), var("oracle_region"))),
        ("exploit_witness", update(var("state"), var("exploit_seed"), var("exploit_region"), var("exploit_region"))),
    ]
    for guard_name, value_expr in rows:
        expr = choice(var(guard_name), value_expr, expr)
    return expr


def sharded_policy() -> Expr:
    shard_a = choice(var("risk_a"), var("value_a"), const(0))
    shard_b = choice(var("risk_b"), var("value_b"), const(0))
    shard_c = choice(var("risk_c"), var("value_c"), const(0))
    shard_d = choice(var("risk_d"), var("value_d"), const(0))
    return point_join(point_join(shard_a, shard_b), point_join(shard_c, shard_d))


def guarded_update() -> Expr:
    return update(var("state"), var("base"), var("guard"), var("replacement"))


def run_case(
    name: str,
    expr: Expr,
    changed_key: str,
    known: dict[str, int],
    expected_relevance: str,
) -> dict[str, object]:
    before_env = env_base()
    after_env = dict(before_env)
    after_env[changed_key] = (before_env[changed_key] ^ 0b1011) & MASK

    residual = partial_eval(expr, known)
    plan = runtime_dependency_plan(residual)
    runtime_nodes = collect_nodes(residual)
    runtime_old_values = build_runtime_cache(runtime_nodes, before_env)

    old_cache = build_cache(residual, before_env)
    read_cache: dict[Expr, set[str]] = {}
    incremental_value, metrics = incremental_eval(
        residual, after_env, old_cache, changed_key, read_cache
    )

    full_counter: dict[str, int] = {}
    full_value = eval_expr(residual, after_env, full_counter)
    original_before = eval_expr(expr, before_env)
    residual_before = eval_expr(residual, before_env)
    original_after = eval_expr(expr, after_env)

    full_tree_visits = full_counter["eval_nodes"]
    full_unique_nodes = node_count(residual)
    recomputed = metrics["recomputed_nodes"]
    savings = (
        100.0 * (full_unique_nodes - recomputed) / full_unique_nodes
        if full_unique_nodes
        else 0.0
    )
    original_reads = sorted(reads(expr))
    residual_reads = sorted(reads(residual))
    changed_in_reads = changed_key in residual_reads
    dependency_index = plan["dependency_index"]
    assert isinstance(dependency_index, dict)
    changed_dependency_ids = list(dependency_index.get(changed_key, []))
    runtime_delta_value, runtime_delta_metrics, runtime_new_values = runtime_delta_update(
        runtime_nodes,
        runtime_old_values,
        after_env,
        set(changed_dependency_ids),
    )
    relevance_ok = (
        (expected_relevance == "relevant" and changed_in_reads)
        or (expected_relevance == "irrelevant" and not changed_in_reads)
    )
    full_reuse_expected_ok = (
        expected_relevance != "irrelevant"
        or (
            recomputed == 0
            and incremental_value == original_before
            and full_value == original_before
        )
    )
    runtime_recompute_count_matches_incremental = len(changed_dependency_ids) == recomputed
    runtime_delta_matches_full = runtime_delta_value == full_value
    runtime_delta_matches_recursive = runtime_delta_value == incremental_value
    runtime_delta_count_matches_index = (
        runtime_delta_metrics["runtime_recomputed_nodes"] == len(changed_dependency_ids)
    )

    return {
        "name": name,
        "changed_key": changed_key,
        "expected_relevance": expected_relevance,
        "known_keys": sorted(known),
        "original_node_count": node_count(expr),
        "residual_node_count": node_count(residual),
        "original_read_count": len(original_reads),
        "residual_read_count": len(residual_reads),
        "runtime_node_count": plan["node_count"],
        "runtime_root_node_id": plan["root_node_id"],
        "runtime_dependency_key_count": len(dependency_index),
        "changed_key_dependency_node_ids": changed_dependency_ids,
        "changed_key_in_residual_reads": changed_in_reads,
        "relevance_expectation_met": relevance_ok,
        "full_eval_tree_visits": full_tree_visits,
        "full_unique_nodes": full_unique_nodes,
        "incremental_recomputed_nodes": recomputed,
        "incremental_reused_nodes": metrics["reused_nodes"],
        "runtime_recompute_count_matches_incremental": runtime_recompute_count_matches_incremental,
        "runtime_delta_recomputed_nodes": runtime_delta_metrics["runtime_recomputed_nodes"],
        "runtime_delta_reused_nodes": runtime_delta_metrics["runtime_reused_nodes"],
        "runtime_delta_matches_full": runtime_delta_matches_full,
        "runtime_delta_matches_recursive": runtime_delta_matches_recursive,
        "runtime_delta_count_matches_index": runtime_delta_count_matches_index,
        "runtime_cache_value_count": len(runtime_new_values),
        "node_recompute_savings_percent": round(savings, 3),
        "partial_eval_preserved_before": original_before == residual_before,
        "partial_eval_preserved_after": original_after == full_value,
        "incremental_matches_full": incremental_value == full_value,
        "full_reuse_expected_ok": full_reuse_expected_ok,
        "before_value": original_before,
        "after_value": full_value,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/local/incremental-execution-demo.json"),
    )
    args = parser.parse_args()

    base = env_base()
    cases = [
        (
            "protocol_change_oracle_guard",
            protocol_firewall(),
            "oracle",
            {"freeze": base["freeze"], "quarantine": base["quarantine"]},
            "relevant",
        ),
        (
            "incident_change_patch_region",
            incident_memory(),
            "patch_region",
            {"exploit_seed": base["exploit_seed"], "oracle_seed": base["oracle_seed"]},
            "relevant",
        ),
        (
            "sharded_change_risk_c",
            sharded_policy(),
            "risk_c",
            {"value_a": base["value_a"], "value_b": base["value_b"]},
            "relevant",
        ),
        (
            "guarded_update_change_replacement",
            guarded_update(),
            "replacement",
            {"base": base["base"], "guard": base["guard"]},
            "relevant",
        ),
        (
            "protocol_change_unused_config",
            protocol_firewall(),
            "unused_config",
            {"freeze": base["freeze"], "quarantine": base["quarantine"]},
            "irrelevant",
        ),
        (
            "incident_change_audit_only",
            incident_memory(),
            "audit_only",
            {"exploit_seed": base["exploit_seed"], "oracle_seed": base["oracle_seed"]},
            "irrelevant",
        ),
    ]
    rows = [run_case(*case) for case in cases]
    ok = all(
        row["partial_eval_preserved_before"]
        and row["partial_eval_preserved_after"]
        and row["incremental_matches_full"]
        and row["relevance_expectation_met"]
        and row["full_reuse_expected_ok"]
        and row["runtime_recompute_count_matches_incremental"]
        and row["runtime_delta_matches_full"]
        and row["runtime_delta_matches_recursive"]
        and row["runtime_delta_count_matches_index"]
        for row in rows
    )
    full_total = sum(int(row["full_unique_nodes"]) for row in rows)
    incremental_total = sum(int(row["incremental_recomputed_nodes"]) for row in rows)
    runtime_delta_total = sum(int(row["runtime_delta_recomputed_nodes"]) for row in rows)
    summary = {
        "scope": "Tau-like expression prototype over the four-cell Boolean algebra",
        "ok": ok,
        "case_count": len(rows),
        "full_eval_nodes_total": full_total,
        "incremental_recomputed_nodes_total": incremental_total,
        "runtime_delta_recomputed_nodes_total": runtime_delta_total,
        "runtime_dependency_plan_checks": all(
            row["runtime_recompute_count_matches_incremental"] for row in rows
        ),
        "runtime_delta_checks": all(
            row["runtime_delta_matches_full"]
            and row["runtime_delta_matches_recursive"]
            and row["runtime_delta_count_matches_index"]
            for row in rows
        ),
        "aggregate_node_recompute_savings_percent": (
            round(100.0 * (full_total - incremental_total) / full_total, 3)
            if full_total
            else 0.0
        ),
        "aggregate_runtime_delta_savings_percent": (
            round(100.0 * (full_total - runtime_delta_total) / full_total, 3)
            if full_total
            else 0.0
        ),
        "rows": rows,
        "boundary": (
            "This is an executable prototype for upstream future-work design. "
            "It is not a Tau runtime patch and not a whole-language speed theorem."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
