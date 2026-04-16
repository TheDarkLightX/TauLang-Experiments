#!/usr/bin/env python3
"""Compare baseline RR extraction with value-argument inference skipping.

The patched Tau binary exposes:

    TAU_RR_SKIP_VALUE_INFER=1

When enabled, `get_nso_rr_with_defs` skips the second full
`infer_ba_types(build_spec(rr_with_defs), ...)` pass for non-`spec` command
arguments that are already ref-valued after parser-time inference. The fallback
path is the existing full inference behavior.
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


def run_mode(tau_bin: Path, reps: int, skip: bool, audit: bool = False) -> dict[str, object]:
    old_rr = os.environ.get("TAU_RR_STATS")
    old_skip = os.environ.get("TAU_RR_SKIP_VALUE_INFER")
    old_audit = os.environ.get("TAU_RR_SKIP_VALUE_INFER_AUDIT")
    os.environ["TAU_RR_STATS"] = "1"
    if skip:
        os.environ["TAU_RR_SKIP_VALUE_INFER"] = "1"
    else:
        os.environ.pop("TAU_RR_SKIP_VALUE_INFER", None)
    if skip and audit:
        os.environ["TAU_RR_SKIP_VALUE_INFER_AUDIT"] = "1"
    else:
        os.environ.pop("TAU_RR_SKIP_VALUE_INFER_AUDIT", None)

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
                ok = ok and result["rr_get_defs_stat_count"] == 1
                ok = ok and result["rr_with_defs_stat_count"] == 1
                if skip and audit:
                    ok = ok and result.get("rr_skip_audit_stat_count", 0) == 1
                    audit_rows = result.get("rr_skip_audit_rows", [])
                    if audit_rows:
                        ok = ok and audit_rows[0].get("inferred") == "1"
                        ok = ok and audit_rows[0].get("structural_equal") == "1"
            rows.append({"name": case["name"], "runs": runs})
    finally:
        if old_rr is None:
            os.environ.pop("TAU_RR_STATS", None)
        else:
            os.environ["TAU_RR_STATS"] = old_rr
        if old_skip is None:
            os.environ.pop("TAU_RR_SKIP_VALUE_INFER", None)
        else:
            os.environ["TAU_RR_SKIP_VALUE_INFER"] = old_skip
        if old_audit is None:
            os.environ.pop("TAU_RR_SKIP_VALUE_INFER_AUDIT", None)
        else:
            os.environ["TAU_RR_SKIP_VALUE_INFER_AUDIT"] = old_audit

    solve_total_ms = 0.0
    solve_apply_ms = 0.0
    rr_get_ms = 0.0
    rr_infer_ms = 0.0
    rr_total_ms = 0.0
    elapsed_ms = 0.0
    branches: dict[str, int] = {}
    audit_rows = 0
    audit_equal = 0
    for row in rows:
        for run in row["runs"]:
            solve = run["solve_rows"][0] if run["solve_rows"] else {}
            rr_with_defs = run["rr_with_defs_rows"][0] if run["rr_with_defs_rows"] else {}
            rr_get_defs = run["rr_get_defs_rows"][0] if run["rr_get_defs_rows"] else {}
            solve_total_ms += as_float(solve, "total_ms")
            solve_apply_ms += as_float(solve, "apply_ms")
            rr_total_ms += as_float(rr_with_defs, "total_ms")
            rr_get_ms += as_float(rr_with_defs, "get_rr_ms")
            rr_infer_ms += as_float(rr_get_defs, "infer_ms")
            elapsed_ms += float(run["elapsed_ms"])
            branch = rr_get_defs.get("branch", "missing")
            branches[branch] = branches.get(branch, 0) + 1
            for audit_row in run.get("rr_skip_audit_rows", []):
                audit_rows += 1
                if audit_row.get("inferred") == "1" and audit_row.get("structural_equal") == "1":
                    audit_equal += 1

    elapsed_values = [
        float(run["elapsed_ms"])
        for row in rows
        for run in row["runs"]
    ]
    return {
        "mode": "skip" if skip else "baseline",
        "ok": ok,
        "case_count": len(rows),
        "reps": reps,
        "run_count": len(rows) * reps,
        "solve_total_ms": round(solve_total_ms, 6),
        "solve_apply_ms": round(solve_apply_ms, 6),
        "rr_total_ms": round(rr_total_ms, 6),
        "rr_get_ms": round(rr_get_ms, 6),
        "rr_infer_ms": round(rr_infer_ms, 6),
        "elapsed_ms": round(elapsed_ms, 3),
        "median_elapsed_ms": round(statistics.median(elapsed_values), 3),
        "rr_get_defs_branches": branches,
        "audit_rows": audit_rows,
        "audit_structural_equal_rows": audit_equal,
        "rows": rows,
    }


def pct_delta(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round(100.0 * (before - after) / before, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("results/local/rr-skip-value-infer-demo.json"))
    args = parser.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be at least 1")
    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    baseline = run_mode(args.tau_bin, args.reps, skip=False)
    skip = run_mode(args.tau_bin, args.reps, skip=True, audit=args.audit)
    ok = bool(baseline["ok"]) and bool(skip["ok"])
    summary = {
        "scope": "feature-gated RR value-argument infer-skip comparison",
        "ok": ok,
        "baseline": baseline,
        "skip": skip,
        "solve_total_improvement_percent": pct_delta(
            float(baseline["solve_total_ms"]),
            float(skip["solve_total_ms"]),
        ),
        "solve_apply_improvement_percent": pct_delta(
            float(baseline["solve_apply_ms"]),
            float(skip["solve_apply_ms"]),
        ),
        "rr_total_improvement_percent": pct_delta(
            float(baseline["rr_total_ms"]),
            float(skip["rr_total_ms"]),
        ),
        "rr_get_improvement_percent": pct_delta(
            float(baseline["rr_get_ms"]),
            float(skip["rr_get_ms"]),
        ),
        "rr_infer_improvement_percent": pct_delta(
            float(baseline["rr_infer_ms"]),
            float(skip["rr_infer_ms"]),
        ),
        "elapsed_improvement_percent": pct_delta(
            float(baseline["elapsed_ms"]),
            float(skip["elapsed_ms"]),
        ),
        "boundary": (
            "This compares one feature-gated shortcut on the safe-table "
            "solver corpus. It is a candidate Tau RR extraction optimization, "
            "not a default-on general correctness claim. Audit mode computes "
            "the full path too and is not a performance mode."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": ok,
        "baseline_solve_total_ms": baseline["solve_total_ms"],
        "skip_solve_total_ms": skip["solve_total_ms"],
        "solve_total_improvement_percent": summary["solve_total_improvement_percent"],
        "baseline_rr_get_ms": baseline["rr_get_ms"],
        "skip_rr_get_ms": skip["rr_get_ms"],
        "rr_get_improvement_percent": summary["rr_get_improvement_percent"],
        "baseline_elapsed_ms": baseline["elapsed_ms"],
        "skip_elapsed_ms": skip["elapsed_ms"],
        "elapsed_improvement_percent": summary["elapsed_improvement_percent"],
        "audit_rows": skip["audit_rows"],
        "audit_structural_equal_rows": skip["audit_structural_equal_rows"],
        "skip_branches": skip["rr_get_defs_branches"],
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
