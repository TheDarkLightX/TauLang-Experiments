#!/usr/bin/env python3
"""Compare Tau default, auto, and auto plus guarded KB qelim modes.

This script answers a narrower question than run_qelim_kb_matrix.py:

  Does the restricted KB prepass help the already-promoted
  TAU_QELIM_BACKEND=auto route?

Boundary: this is a patched Tau experiment on generated formulas, not a
production Tau benchmark. The script gates KB by exact output parity against
the unmodified `auto` route. It records exact default parity separately because
Tau's default and auto routes may print equivalent residual formulas in
different syntactic forms.
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
    backend: str = ""
    kb: str = ""


MODES = [
    Mode("default"),
    Mode("auto", backend="auto"),
    Mode("auto_kb_guarded", backend="auto", kb="guarded"),
    Mode("auto_kb_forced", backend="auto", kb="1"),
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


def as_int(d: dict[str, str], key: str) -> int:
    try:
        return int(float(d.get(key, "0")))
    except ValueError:
        return 0


def run_tau(tau_bin: Path, command: str, mode: Mode) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_QELIM_STATS"] = "1"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if mode.backend:
        env["TAU_QELIM_BACKEND"] = mode.backend
    else:
        env.pop("TAU_QELIM_BACKEND", None)
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
    qelim_stats = parse_prefixed_stats(combined, "[qelim_cmd]")
    bdd_stats = parse_prefixed_stats(combined, "[qelim_bdd]")
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
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
    qelim_total = [float(v["qelim_total_ms"]) for v in values]
    bdd_internal = [float(v["bdd_internal_ms"]) for v in values]
    kb_steps = [as_int(v["bdd_stats"], "kb_steps") for v in values]  # type: ignore[arg-type]
    kb_guard_ran = [as_int(v["bdd_stats"], "kb_guard_ran") for v in values]  # type: ignore[arg-type]
    kb_before = [as_int(v["bdd_stats"], "kb_before_nodes") for v in values]  # type: ignore[arg-type]
    kb_after = [as_int(v["bdd_stats"], "kb_after_nodes") for v in values]  # type: ignore[arg-type]
    before_sum = sum(kb_before)
    after_sum = sum(kb_after)
    return {
        "runs": len(values),
        "elapsed_ms_sum": round(sum(elapsed), 3),
        "elapsed_ms_median": round(statistics.median(elapsed), 3) if elapsed else 0,
        "qelim_total_ms_sum": round(sum(qelim_total), 6),
        "qelim_total_ms_median": round(statistics.median(qelim_total), 6) if qelim_total else 0,
        "bdd_internal_ms_sum": round(sum(bdd_internal), 6),
        "bdd_internal_ms_median": round(statistics.median(bdd_internal), 6) if bdd_internal else 0,
        "kb_steps_sum": sum(kb_steps),
        "kb_guard_ran_sum": sum(kb_guard_ran),
        "kb_before_nodes_sum": before_sum,
        "kb_after_nodes_sum": after_sum,
        "kb_node_reduction_percent": (
            round(100 * (before_sum - after_sum) / before_sum, 2) if before_sum else 0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-auto-kb-matrix.json"))
    parser.add_argument("--max-cases", type=int, default=18)
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    cases = build_cases(args.max_cases)
    per_mode: dict[str, list[dict[str, object]]] = {m.name: [] for m in MODES}
    rows = []
    ok = True
    default_exact_match = True

    for case in cases:
        case_runs = {m.name: [] for m in MODES}
        for _ in range(args.reps):
            for mode in MODES:
                result = run_tau(args.tau_bin, case["command"], mode)
                case_runs[mode.name].append(result)
                per_mode[mode.name].append(result)

        default_stdout = case_runs["default"][0]["stdout"]
        default_returncode = case_runs["default"][0]["returncode"]
        auto_stdout = case_runs["auto"][0]["stdout"]
        auto_returncode = case_runs["auto"][0]["returncode"]
        exact_default_parity = {}
        auto_kb_parity = {}
        for mode in MODES:
            same_default = all(
                r["stdout"] == default_stdout and r["returncode"] == default_returncode
                for r in case_runs[mode.name]
            )
            same_auto = all(
                r["stdout"] == auto_stdout and r["returncode"] == auto_returncode
                for r in case_runs[mode.name]
            )
            exact_default_parity[mode.name] = same_default
            auto_kb_parity[mode.name] = same_auto
            default_exact_match = default_exact_match and same_default

        ok = (
            ok
            and default_returncode == 0
            and auto_returncode == 0
            and auto_kb_parity["auto"]
            and auto_kb_parity["auto_kb_guarded"]
            and auto_kb_parity["auto_kb_forced"]
        )

        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "exact_default_parity": exact_default_parity,
                "auto_kb_parity": auto_kb_parity,
                "summary": {mode.name: summarize(case_runs[mode.name]) for mode in MODES},
            }
        )

    summary = {
        "scope": "patched Tau generated matrix, default versus auto versus auto+KB",
        "ok": ok,
        "default_exact_match": default_exact_match,
        "case_count": len(cases),
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
