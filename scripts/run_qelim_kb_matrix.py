#!/usr/bin/env python3
"""Generated matrix for the opt-in Tau qelim KB rewrite pass.

The matrix compares six patched BDD qelim modes:

  bdd
  bdd+kb
  bdd+kb_guarded
  bdd+ac
  bdd+ac+kb
  bdd+ac+kb_guarded

It is designed to answer a narrow engineering question: does the c111-inspired
rewrite pre-pass simplify the compiled Boolean expression without changing the
qelim output, and is there enough timing evidence to promote it?

Boundary: this is still a generated experiment on a patched Tau checkout, not a
production Tau benchmark.
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
from typing import Iterable


STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


@dataclass(frozen=True)
class Mode:
    name: str
    kb: str = ""
    ac: bool = False


MODES = [
    Mode("bdd"),
    Mode("bdd_kb", kb="1"),
    Mode("bdd_kb_guarded", kb="guarded"),
    Mode("bdd_ac", ac=True),
    Mode("bdd_ac_kb", kb="1", ac=True),
    Mode("bdd_ac_kb_guarded", kb="guarded", ac=True),
]


def atom(name: str) -> str:
    return f"({name} = 0)"


def absorb_and(x: str, free: str) -> str:
    a = atom(x)
    b = atom(free)
    return f"({a} && ({a} || {b}))"


def absorb_or(x: str, free: str) -> str:
    a = atom(x)
    b = atom(free)
    return f"({a} || ({a} && {b}))"


def demorgan_and(x: str, free: str) -> str:
    return f"!({atom(x)} && {atom(free)})"


def demorgan_or(x: str, free: str) -> str:
    return f"!({atom(x)} || {atom(free)})"


def neg_absorb(x: str, free: str) -> str:
    return f"!{absorb_and(x, free)}"


def double_neg(x: str) -> str:
    return f"!(!(!{atom(x)}))"


def qprefix(vars_: Iterable[str]) -> str:
    return " ".join(f"ex {v}" for v in vars_)


def build_cases(max_cases: int) -> list[dict[str, str]]:
    quant = ["x", "y", "z", "w", "u", "v", "p", "q"]
    free = ["a", "b", "c", "d", "e", "f", "g", "h"]
    cases: list[dict[str, str]] = []

    single_patterns = [
        ("absorb_and", absorb_and),
        ("absorb_or", absorb_or),
        ("demorgan_and", demorgan_and),
        ("demorgan_or", demorgan_or),
        ("neg_absorb", neg_absorb),
    ]
    for name, builder in single_patterns:
        body = builder("x", "a")
        cases.append({"name": name, "command": f"qelim {qprefix(['x'])} {body}"})
    cases.append({"name": "double_neg", "command": f"qelim {qprefix(['x'])} {double_neg('x')}"})

    for width in range(2, 9):
        qs = quant[:width]
        fs = free[:width]
        parts = [absorb_and(q, f) for q, f in zip(qs, fs, strict=True)]
        cases.append(
            {
                "name": f"conjoined_absorb_width_{width}",
                "command": f"qelim {qprefix(qs)} " + " && ".join(parts),
            }
        )
        cases.append(
            {
                "name": f"negated_absorb_or_width_{width}",
                "command": f"qelim {qprefix(qs)} !(" + " || ".join(parts) + ")",
            }
        )
        demorgan_parts = [demorgan_and(q, f) for q, f in zip(qs, fs, strict=True)]
        cases.append(
            {
                "name": f"conjoined_demorgan_width_{width}",
                "command": f"qelim {qprefix(qs)} " + " && ".join(demorgan_parts),
            }
        )
        mixed = []
        for i, (q, f) in enumerate(zip(qs, fs, strict=True)):
            mixed.append(absorb_and(q, f) if i % 2 == 0 else demorgan_or(q, f))
        cases.append(
            {
                "name": f"mixed_width_{width}",
                "command": f"qelim {qprefix(qs)} " + " || ".join(mixed),
            }
        )

    return cases[:max_cases]


def parse_stats(text: str) -> dict[str, str]:
    line = ""
    for candidate in text.splitlines():
        if candidate.startswith("[qelim_bdd]"):
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
    env["TAU_QELIM_BACKEND"] = "bdd"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if mode.kb:
        env["TAU_QELIM_BDD_KB_REWRITE"] = mode.kb
    else:
        env.pop("TAU_QELIM_BDD_KB_REWRITE", None)
    if mode.ac:
        env["TAU_QELIM_BDD_AC_CANON"] = "1"
    else:
        env.pop("TAU_QELIM_BDD_AC_CANON", None)

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
    stats = parse_stats(combined)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "elapsed_ms": round(elapsed_ms, 3),
        "stats": stats,
        "total_internal_ms": round(
            as_float(stats, "compile_ms") + as_float(stats, "project_ms") + as_float(stats, "rebuild_ms"),
            6,
        ),
    }


def summarize_mode(values: list[dict[str, object]]) -> dict[str, object]:
    internal = [float(v["total_internal_ms"]) for v in values]
    elapsed = [float(v["elapsed_ms"]) for v in values]
    kb_steps = [as_int(v["stats"], "kb_steps") for v in values]  # type: ignore[arg-type]
    kb_discarded = [as_int(v["stats"], "kb_discarded") for v in values]  # type: ignore[arg-type]
    kb_guard_absorption = [as_int(v["stats"], "kb_guard_absorption") for v in values]  # type: ignore[arg-type]
    kb_guard_demorgan = [as_int(v["stats"], "kb_guard_demorgan") for v in values]  # type: ignore[arg-type]
    kb_guard_ran = [as_int(v["stats"], "kb_guard_ran") for v in values]  # type: ignore[arg-type]
    before_nodes = [as_int(v["stats"], "kb_before_nodes") for v in values]  # type: ignore[arg-type]
    after_nodes = [as_int(v["stats"], "kb_after_nodes") for v in values]  # type: ignore[arg-type]
    before_sum = sum(before_nodes)
    after_sum = sum(after_nodes)
    return {
        "runs": len(values),
        "internal_ms_sum": round(sum(internal), 6),
        "internal_ms_median": round(statistics.median(internal), 6) if internal else 0,
        "elapsed_ms_sum": round(sum(elapsed), 3),
        "elapsed_ms_median": round(statistics.median(elapsed), 3) if elapsed else 0,
        "kb_steps_sum": sum(kb_steps),
        "kb_discarded_sum": sum(kb_discarded),
        "kb_guard_absorption_sum": sum(kb_guard_absorption),
        "kb_guard_demorgan_sum": sum(kb_guard_demorgan),
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
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-kb-matrix.json"))
    parser.add_argument("--max-cases", type=int, default=18)
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    cases = build_cases(args.max_cases)
    rows = []
    per_mode: dict[str, list[dict[str, object]]] = {m.name: [] for m in MODES}
    ok = True

    for case in cases:
        case_runs = {m.name: [] for m in MODES}
        for _ in range(args.reps):
            # Keep ordering stable and visible. This is not a randomized benchmark.
            for mode in MODES:
                result = run_tau(args.tau_bin, case["command"], mode)
                case_runs[mode.name].append(result)
                per_mode[mode.name].append(result)

        baseline_stdout = case_runs["bdd"][0]["stdout"]
        baseline_returncode = case_runs["bdd"][0]["returncode"]
        parity = {}
        for mode in MODES:
            same = all(
                r["stdout"] == baseline_stdout and r["returncode"] == baseline_returncode
                for r in case_runs[mode.name]
            )
            parity[mode.name] = same
            ok = ok and same and baseline_returncode == 0

        rows.append(
            {
                "name": case["name"],
                "command": case["command"],
                "parity": parity,
                "summary": {mode.name: summarize_mode(case_runs[mode.name]) for mode in MODES},
            }
        )

    summary = {
        "scope": "patched BDD qelim generated matrix, not a production Tau benchmark",
        "ok": ok,
        "case_count": len(cases),
        "reps": args.reps,
        "mode_summary": {mode.name: summarize_mode(per_mode[mode.name]) for mode in MODES},
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
