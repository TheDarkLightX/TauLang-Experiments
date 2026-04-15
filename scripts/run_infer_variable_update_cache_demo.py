#!/usr/bin/env python3
"""Compare baseline type inference with a local variable-update cache.

The patched Tau binary exposes:

    TAU_INFER_VARIABLE_UPDATE_CACHE=1

The cache is deliberately local to one `update(...)` call in
`ba_types_inference.tmpl.h`, where `resolver.current_types()` has already been
snapshotted. This avoids cross-scope invalidation while testing whether repeated
typed-variable updates are worth caching.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from pathlib import Path

import run_table_demo_solve_telemetry as solve_telemetry


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or "0")


def as_int(row: dict[str, str], key: str) -> int:
    return int(row.get(key, "0") or "0")


def run_mode(tau_bin: Path, reps: int, cached: bool) -> dict[str, object]:
    old_rr = os.environ.get("TAU_RR_STATS")
    old_cache = os.environ.get("TAU_INFER_VARIABLE_UPDATE_CACHE")
    os.environ["TAU_RR_STATS"] = "1"
    if cached:
        os.environ["TAU_INFER_VARIABLE_UPDATE_CACHE"] = "1"
    else:
        os.environ.pop("TAU_INFER_VARIABLE_UPDATE_CACHE", None)

    try:
        rows: list[dict[str, object]] = []
        ok = True
        for case in solve_telemetry.cases(Path.cwd()):
            runs = []
            for _ in range(reps):
                result = solve_telemetry.run_tau(tau_bin, case["program"])
                runs.append(result)
                ok = ok and result["returncode"] == 0
                ok = ok and result["last_line"] == "no solution"
                ok = ok and result["solve_stat_count"] == 1
                ok = ok and result["infer_update_stat_count"] >= 1
            rows.append({"name": case["name"], "runs": runs})
    finally:
        if old_rr is None:
            os.environ.pop("TAU_RR_STATS", None)
        else:
            os.environ["TAU_RR_STATS"] = old_rr
        if old_cache is None:
            os.environ.pop("TAU_INFER_VARIABLE_UPDATE_CACHE", None)
        else:
            os.environ["TAU_INFER_VARIABLE_UPDATE_CACHE"] = old_cache

    solve_total_ms = 0.0
    solve_apply_ms = 0.0
    elapsed_ms = 0.0
    variable_queries = 0
    cache_hits = 0
    cache_misses = 0
    cache_size_total = 0
    update_rows = 0
    for row in rows:
        for run in row["runs"]:
            solve = run["solve_rows"][0] if run["solve_rows"] else {}
            solve_total_ms += as_float(solve, "total_ms")
            solve_apply_ms += as_float(solve, "apply_ms")
            elapsed_ms += float(run["elapsed_ms"])
            for update in run["infer_update_rows"]:
                update_rows += 1
                variable_queries += as_int(update, "variable_update_queries")
                cache_hits += as_int(update, "variable_update_cache_hits")
                cache_misses += as_int(update, "variable_update_cache_misses")
                cache_size_total += as_int(update, "variable_update_cache_size")

    elapsed_values = [
        float(run["elapsed_ms"])
        for row in rows
        for run in row["runs"]
    ]
    return {
        "mode": "cached" if cached else "baseline",
        "ok": ok,
        "case_count": len(rows),
        "reps": reps,
        "run_count": len(rows) * reps,
        "solve_total_ms": round(solve_total_ms, 6),
        "solve_apply_ms": round(solve_apply_ms, 6),
        "elapsed_ms": round(elapsed_ms, 3),
        "median_elapsed_ms": round(statistics.median(elapsed_values), 3),
        "infer_update_rows": update_rows,
        "variable_update_queries": variable_queries,
        "variable_update_cache_hits": cache_hits,
        "variable_update_cache_misses": cache_misses,
        "variable_update_cache_size_total": cache_size_total,
        "rows": rows,
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("results/local/infer-variable-update-cache-demo.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    baseline = run_mode(args.tau_bin, args.reps, cached=False)
    cached = run_mode(args.tau_bin, args.reps, cached=True)
    ok = bool(baseline["ok"]) and bool(cached["ok"])
    summary = {
        "scope": "feature-gated Tau type-inference variable-update cache comparison",
        "ok": ok,
        "baseline": baseline,
        "cached": cached,
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]),
            float(cached["solve_total_ms"]),
        ),
        "solve_apply_improvement_percent": pct_delta(
            float(baseline["solve_apply_ms"]),
            float(cached["solve_apply_ms"]),
        ),
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_ms"]),
            float(cached["elapsed_ms"]),
        ),
        "boundary": (
            "This compares one local cache inside Tau type inference on the "
            "safe-table solver corpus. It is not a general Tau speedup claim."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "cached_solve_total_ms": cached["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_elapsed_ms": baseline["elapsed_ms"],
        "cached_elapsed_ms": cached["elapsed_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "cached_variable_update_queries": cached["variable_update_queries"],
        "cached_variable_update_cache_hits": cached["variable_update_cache_hits"],
        "cached_variable_update_cache_misses": cached["variable_update_cache_misses"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
