#!/usr/bin/env python3
"""Scoped var-name cache-key demo.

This script models the cache-key question exposed by Tau type-inference
telemetry. The point is not to simulate Tau's resolver completely. The point is
to test the smallest cache-key distinction:

    name-only cache          unsafe under shadowing
    (scope, name) cache      safe in this model
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Visit:
    scope: str
    name: str


@dataclass(frozen=True)
class Scenario:
    name: str
    types: dict[tuple[str, str], str]
    visits: tuple[Visit, ...]


def resolve(types: dict[tuple[str, str], str], visit: Visit) -> str:
    return types[(visit.scope, visit.name)]


def baseline(types: dict[tuple[str, str], str], visits: tuple[Visit, ...]) -> tuple[list[str], int]:
    return [resolve(types, v) for v in visits], len(visits)


def scoped_cache(types: dict[tuple[str, str], str], visits: tuple[Visit, ...]) -> tuple[list[str], int, int]:
    cache: dict[tuple[str, str], str] = {}
    out: list[str] = []
    resolves = 0
    hits = 0
    for v in visits:
        key = (v.scope, v.name)
        if key in cache:
            hits += 1
        else:
            cache[key] = resolve(types, v)
            resolves += 1
        out.append(cache[key])
    return out, resolves, hits


def name_only_cache(types: dict[tuple[str, str], str], visits: tuple[Visit, ...]) -> tuple[list[str], int, int]:
    cache: dict[str, str] = {}
    out: list[str] = []
    resolves = 0
    hits = 0
    for v in visits:
        if v.name in cache:
            hits += 1
        else:
            cache[v.name] = resolve(types, v)
            resolves += 1
        out.append(cache[v.name])
    return out, resolves, hits


def scenarios() -> list[Scenario]:
    return [
        Scenario(
            name="no_shadowing_repeated_names",
            types={
                ("global", "risk"): "tau",
                ("global", "guard"): "sbf",
                ("global", "state"): "tau",
            },
            visits=tuple(
                Visit("global", name)
                for name in [
                    "risk", "guard", "risk", "state", "risk", "guard",
                    "state", "risk", "guard", "state",
                ]
            ),
        ),
        Scenario(
            name="shadowed_x_across_scopes",
            types={
                ("global", "x"): "tau",
                ("quantifier", "x"): "sbf",
                ("quantifier", "guard"): "sbf",
            },
            visits=(
                Visit("global", "x"),
                Visit("global", "x"),
                Visit("quantifier", "x"),
                Visit("quantifier", "guard"),
                Visit("quantifier", "x"),
                Visit("global", "x"),
            ),
        ),
        Scenario(
            name="nested_table_update_names",
            types={
                ("outer", "state"): "tau",
                ("outer", "guard"): "tau",
                ("inner", "state"): "sbf",
                ("inner", "guard"): "sbf",
                ("inner", "replacement"): "tau",
            },
            visits=(
                Visit("outer", "state"),
                Visit("outer", "guard"),
                Visit("inner", "state"),
                Visit("inner", "guard"),
                Visit("inner", "replacement"),
                Visit("inner", "state"),
                Visit("outer", "state"),
                Visit("inner", "guard"),
                Visit("outer", "guard"),
            ),
        ),
    ]


def pct(before: int, after: int) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def run_scenario(s: Scenario) -> dict[str, object]:
    expected, baseline_resolves = baseline(s.types, s.visits)
    scoped_out, scoped_resolves, scoped_hits = scoped_cache(s.types, s.visits)
    name_out, name_resolves, name_hits = name_only_cache(s.types, s.visits)
    name_mismatches = [
        {
            "index": i,
            "scope": v.scope,
            "name": v.name,
            "expected": expected[i],
            "name_only": name_out[i],
        }
        for i, v in enumerate(s.visits)
        if expected[i] != name_out[i]
    ]
    return {
        "name": s.name,
        "visit_count": len(s.visits),
        "baseline_resolves": baseline_resolves,
        "scoped_cache_resolves": scoped_resolves,
        "scoped_cache_hits": scoped_hits,
        "scoped_cache_reduction_percent": pct(baseline_resolves, scoped_resolves),
        "scoped_cache_matches": scoped_out == expected,
        "name_only_cache_resolves": name_resolves,
        "name_only_cache_hits": name_hits,
        "name_only_cache_reduction_percent": pct(baseline_resolves, name_resolves),
        "name_only_cache_matches": name_out == expected,
        "name_only_mismatches": name_mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/local/var-name-cache-key-demo.json"))
    args = parser.parse_args()

    rows = [run_scenario(s) for s in scenarios()]
    total_baseline = sum(int(r["baseline_resolves"]) for r in rows)
    total_scoped = sum(int(r["scoped_cache_resolves"]) for r in rows)
    total_name = sum(int(r["name_only_cache_resolves"]) for r in rows)
    summary = {
        "scope": "scoped var-name cache-key model for Tau type-inference experiments",
        "ok": all(bool(r["scoped_cache_matches"]) for r in rows)
        and any(not bool(r["name_only_cache_matches"]) for r in rows),
        "case_count": len(rows),
        "baseline_resolves_total": total_baseline,
        "scoped_cache_resolves_total": total_scoped,
        "scoped_cache_reduction_percent": pct(total_baseline, total_scoped),
        "name_only_cache_resolves_total": total_name,
        "name_only_cache_reduction_percent": pct(total_baseline, total_name),
        "name_only_cache_has_counterexample": any(
            not bool(r["name_only_cache_matches"]) for r in rows
        ),
        "rows": rows,
        "boundary": (
            "This is a small resolver-cache model, not Tau's full scoped "
            "union-find implementation."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
