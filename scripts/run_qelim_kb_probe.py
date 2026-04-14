#!/usr/bin/env python3
"""Probe the opt-in Tau qelim KB rewrite pass.

This script compares the patched BDD qelim backend with and without
TAU_QELIM_BDD_KB_REWRITE=1 on formulas designed to expose absorption,
double-complement, and De Morgan opportunities.

Boundary: this is a micro-probe for the patched experiment backend, not a
general Tau performance benchmark.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path


PROBES = [
    {
        "name": "demorgan_absorption_left",
        "command": "qelim ex x !((x = 0) && ((x = 0) || (a = 0)))",
    },
    {
        "name": "demorgan_absorption_right",
        "command": "qelim ex x !(((x = 0) || (a = 0)) && (x = 0))",
    },
    {
        "name": "double_complement",
        "command": "qelim ex x !(!(!(x = 0)))",
    },
    {
        "name": "join_absorption",
        "command": "qelim ex x ((x = 0) || ((x = 0) && (a = 0)))",
    },
    {
        "name": "nested_mixed",
        "command": (
            "qelim ex x ex y "
            "!(((x = 0) && ((x = 0) || (a = 0))) || "
            "((y = 0) && ((y = 0) || (b = 0))))"
        ),
    },
]

STAT_RE = re.compile(r"([A-Za-z_]+)=([^\s]+)")


def parse_stats(text: str) -> dict[str, str]:
    line = ""
    for candidate in text.splitlines():
        if candidate.startswith("[qelim_bdd]"):
            line = candidate
    return dict(STAT_RE.findall(line))


def run_tau(tau_bin: Path, command: str, kb: bool) -> dict[str, object]:
    env = os.environ.copy()
    env["TAU_QELIM_BACKEND"] = "bdd"
    env["TAU_QELIM_BDD_STATS"] = "1"
    if kb:
        env["TAU_QELIM_BDD_KB_REWRITE"] = "1"
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
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "elapsed_ms": round(elapsed_ms, 3),
        "stats": parse_stats(combined),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-bin", type=Path, default=Path("external/tau-lang/build-Release/tau"))
    parser.add_argument("--out", type=Path, default=Path("results/local/qelim-kb-probe.json"))
    args = parser.parse_args()

    if not args.tau_bin.exists():
        raise SystemExit(f"Tau binary not found: {args.tau_bin}")

    rows = []
    ok = True
    for probe in PROBES:
        base = run_tau(args.tau_bin, probe["command"], kb=False)
        kb = run_tau(args.tau_bin, probe["command"], kb=True)
        same_stdout = base["stdout"] == kb["stdout"]
        same_returncode = base["returncode"] == kb["returncode"]
        ok = ok and same_stdout and same_returncode and base["returncode"] == 0
        rows.append(
            {
                "name": probe["name"],
                "command": probe["command"],
                "same_stdout": same_stdout,
                "same_returncode": same_returncode,
                "base": base,
                "kb": kb,
            }
        )

    summary = {
        "scope": "patched BDD qelim micro-probe, not a full Tau benchmark",
        "ok": ok,
        "probe_count": len(rows),
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
