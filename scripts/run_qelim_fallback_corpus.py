#!/usr/bin/env python3
"""Benchmark qelim cases that deliberately exercise auto-backend fallback.

The ordinary qelim auto/KB matrix mostly exercises the compiled `pure` route.
This corpus uses relational atoms such as `(x = a)` and `(x = y)`, which the
current experimental BDD compiler rejects. The point is to measure and document
fallback behavior explicitly, not to promote the BDD backend for these cases.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Mode:
    name: str
    backend: str = ""
    auto_guard: str = ""


MODES = [
    Mode("default"),
    Mode("auto", backend="auto"),
    Mode("auto_guard_raw", backend="auto", auto_guard="raw"),
    Mode("auto_guard_dup", backend="auto", auto_guard="dup"),
    Mode("auto_guard_both", backend="auto", auto_guard="both"),
    Mode("auto_guard_rel", backend="auto", auto_guard="rel"),
    Mode("auto_guard_all", backend="auto", auto_guard="all"),
]


def cases() -> list[dict[str, str]]:
    return [
        {"name": "free_equality", "command": "qelim ex x (x = a)"},
        {"name": "free_equality_meet", "command": "qelim ex x ((x = a) && (x = b))"},
        {"name": "free_equality_join", "command": "qelim ex x ((x = a) || (x = b))"},
        {
            "name": "two_quantifier_chain",
            "command": "qelim ex x ex y ((x = y) && (y = a))",
        },
        {
            "name": "two_quantifier_cross",
            "command": "qelim ex x ex y (((x = a) || (y = b)) && ((x = b) || (y = a)))",
        },
        {
            "name": "three_quantifier_cycle",
            "command": (
                "qelim ex x ex y ex z "
                "(((x = y) || (a = b)) && ((y = z) || (b = c)) && ((z = x) || (c = a)))"
            ),
        },
        {
            "name": "three_quantifier_witness",
            "command": (
                "qelim ex x ex y ex z "
                "(((x = a) && (y = b)) || ((x = b) && (z = c)) || ((y = c) && (z = a)))"
            ),
        },
    ]


def parse_prefixed_stats(text: str, prefix: str) -> dict[str, str]:
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


def run_tau(tau_bin: Path, command: str, mode: Mode) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_QELIM_STATS"] = "1"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if mode.backend:
        env["TAU_QELIM_BACKEND"] = mode.backend
    else:
        env.pop("TAU_QELIM_BACKEND", None)
    if mode.auto_guard:
        env["TAU_QELIM_AUTO_GUARD"] = mode.auto_guard
    else:
        env.pop("TAU_QELIM_AUTO_GUARD", None)

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
    qelim_stats = parse_prefixed_stats(combined, "[qelim_cmd]")
    bdd_stats = parse_prefixed_stats(combined, "[qelim_bdd]")
    normalized_stdout = "\n".join(
        line
        for line in proc.stdout.strip().splitlines()
        if not line.startswith("[")
        and "Experimental qelim BDD backend rejected" not in line
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "normalized_stdout": normalized_stdout,
        "stderr": proc.stderr.strip(),
        "elapsed_ms": round(elapsed_ms, 3),
        "qelim_stats": qelim_stats,
        "bdd_stats": bdd_stats,
        "qelim_total_ms": round(as_float(qelim_stats, "total_ms"), 6),
        "bdd_internal_ms": round(
            as_float(bdd_stats, "compile_ms")
            + as_float(bdd_stats, "project_ms")
            + as_float(bdd_stats, "rebuild_ms"),
            6,
        ),
    }


def summarize(values: list[dict[str, object]]) -> dict[str, object]:
    elapsed = [float(v["elapsed_ms"]) for v in values]
    qelim = [float(v["qelim_total_ms"]) for v in values]
    bdd = [float(v["bdd_internal_ms"]) for v in values]
    routes = Counter(
        str(v["bdd_stats"].get("route", "missing"))  # type: ignore[union-attr]
        for v in values
    )
    return {
        "runs": len(values),
        "returncodes": sorted({int(v["returncode"]) for v in values}),
        "elapsed_ms_sum": round(sum(elapsed), 3),
        "elapsed_ms_median": round(statistics.median(elapsed), 3) if elapsed else 0,
        "qelim_total_ms_sum": round(sum(qelim), 6),
        "qelim_total_ms_median": round(statistics.median(qelim), 6) if qelim else 0,
        "bdd_internal_ms_sum": round(sum(bdd), 6),
        "bdd_internal_ms_median": round(statistics.median(bdd), 6) if bdd else 0,
        "route_counts": dict(sorted(routes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-fallback-corpus.json"))
    parser.add_argument("--reps", type=int, default=5)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    per_mode: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
    ok = True
    for case in cases():
        case_runs: dict[str, list[dict[str, object]]] = {mode.name: [] for mode in MODES}
        for _ in range(args.reps):
            for mode in MODES:
                result = run_tau(args.tau_bin, case["command"], mode)
                case_runs[mode.name].append(result)
                per_mode[mode.name].append(result)

        default_stdout = case_runs["default"][0]["normalized_stdout"]
        default_returncode = case_runs["default"][0]["returncode"]
        parity = {
            mode.name: all(
                r["normalized_stdout"] == default_stdout and r["returncode"] == default_returncode
                for r in case_runs[mode.name]
            )
            for mode in MODES
        }
        ok = ok and default_returncode == 0 and all(parity.values())
        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "exact_default_parity": parity,
                "summary": {mode.name: summarize(case_runs[mode.name]) for mode in MODES},
            }
        )

    summary = {
        "scope": "patched Tau qelim auto fallback corpus for relational atoms",
        "ok": ok,
        "case_count": len(cases()),
        "reps": args.reps,
        "mode_summary": {mode.name: summarize(per_mode[mode.name]) for mode in MODES},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
