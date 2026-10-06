#!/usr/bin/env python3
"""Bounded sequential comparison for Tau issue 203.

Keep every attempt, its input and complete output. Report median process CPU
and wall time separately from Tau's stage timings. Any failed attempt fails
the comparison; a later faster or successful attempt cannot hide it.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import subprocess
import sys
import time

import tau_dispatch_blowup as reporter

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
STAGE = re.compile(r"^\s*([A-Za-z_][A-Za-z_ ]*):\s*([0-9.]+(?:e[+-]?[0-9]+)?)\s*(µs|us|ms|s)\s*$", re.M)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_one(command, boot, stdin, expected, folder, cap_s, rss_mib, first_step=0):
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "boot.tau").write_text(boot or "")
    (folder / "stdin.txt").write_text(stdin)
    killed = None
    start = time.monotonic()
    with (folder / "stdin.txt").open("rb") as fi, (folder / "stdout.txt").open("wb") as fo, (folder / "stderr.txt").open("wb") as fe:
        argv = command + (["boot.tau"] if boot is not None else [])
        proc = subprocess.Popen(argv, cwd=folder, stdin=fi,
                                stdout=fo, stderr=fe, start_new_session=True)
        next_sample = start
        try:
            while True:
                pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
                if pid:
                    break
                now = time.monotonic()
                if now >= next_sample:
                    sample = subprocess.run(["ps", "-o", "rss=", "-p", str(proc.pid)],
                                            capture_output=True, text=True, timeout=3)
                    if sample.stdout.strip() and int(sample.stdout.strip()) > rss_mib * 1024:
                        killed = "sampled_memory_limit"
                    next_sample = now + 0.2
                if now - start > cap_s:
                    killed = "wall_time_limit"
                if killed:
                    os.killpg(proc.pid, signal.SIGKILL)
                    _, status, usage = os.wait4(proc.pid, 0)
                    break
                time.sleep(0.01)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
                os.wait4(proc.pid, 0)
            except ProcessLookupError:
                pass
            raise
        proc.returncode = os.waitstatus_to_exitcode(status)
    out = ANSI.sub("", (folder / "stdout.txt").read_text(errors="replace"))
    err = ANSI.sub("", (folder / "stderr.txt").read_text(errors="replace"))
    indexed_o5 = re.findall(r"o5\[(\d+)\]\s*:=\s*(\S+)", out)
    actual = [value for _, value in indexed_o5]
    indices_ok = [int(index) for index, _ in indexed_o5] == list(range(first_step, first_step + len(expected)))
    stages = {}
    for name, value, unit in STAGE.findall(out + "\n" + err):
        stages.setdefault(name.strip(), []).append(float(value) * {"µs": 1e-6, "us": 1e-6, "ms": 1e-3, "s": 1}[unit])
    result = {
        "command": argv, "rc": proc.returncode, "stopped": killed,
        "cpu_s": usage.ru_utime + usage.ru_stime, "wall_s": time.monotonic() - start,
        "peak_rss_mib": usage.ru_maxrss / (1024**2 if sys.platform == "darwin" else 1024),
        "expected_o5": list(map(str, expected)), "actual_o5": actual,
        "o5_first_step": first_step, "o5_indices_ok": indices_ok,
        "stages_s": stages,
        "ok": killed is None and proc.returncode == 0 and indices_ok and actual == list(map(str, expected))
              and re.search(r"\bError\b|\bUNKNOWN\b", out + err) is None,
        "sha256": {f: digest(folder / f) for f in ("boot.tau", "stdin.txt", "stdout.txt", "stderr.txt")},
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def aggregate(attempts):
    return {"ok": bool(attempts) and all(a["ok"] for a in attempts), "attempts": attempts,
            **{f"median_{field}": statistics.median(a[field] for a in attempts)
               for field in ("cpu_s", "wall_s", "peak_rss_mib")}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unmodified", required=True)
    ap.add_argument("--patched", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--cap", type=float, default=60)
    ap.add_argument("--rss-mib", type=float, default=1536)
    ap.add_argument("points", nargs="+", help="kind:size:path[:variant-to-skip...]")
    args = ap.parse_args()
    if args.reps < 1:
        ap.error("--reps must be positive")
    if not math.isfinite(args.cap) or args.cap <= 0 or not math.isfinite(args.rss_mib) or args.rss_mib <= 0:
        ap.error("time and memory limits must be finite and positive")
    for point in args.points:
        fields = point.split(":")
        if len(fields) < 3 or fields[0] not in ("terms", "chain") or fields[2] not in ("spec", "revision"):
            ap.error("invalid point: " + point)
        if not fields[1].isdigit() or not 1 <= int(fields[1]) <= 64:
            ap.error("point size must be between 1 and 64")
        if set(fields[3:]) - {"unmodified", "patched", "split_off"}:
            ap.error("unknown skipped variant: " + point)
    args.out.mkdir(parents=True, exist_ok=False)
    configs = {"unmodified": [str(Path(args.unmodified).resolve())],
               "patched": [str(Path(args.patched).resolve())],
               "split_off": [str(Path(args.unmodified).resolve()), "--bv-case-split", "false"]}
    record = {"schema": "tau203-measure/2", "platform": platform.platform(),
              "python": sys.version, "binary_sha256": {k: digest(v[0]) for k, v in configs.items()},
              "reps": args.reps, "cap_s": args.cap, "rss_limit_mib": args.rss_mib,
              "timing_scope": "Complete process, including load and checked steps; stage timings retained separately.",
              "rows": []}
    for point in args.points:
        kind, size, path, *skip = point.split(":")
        wl = reporter.terms_workload(int(size), 8) if kind == "terms" else reporter.chain_workload(int(size), 8, False)
        if path not in ("spec", "revision"):
            raise ValueError(path)
        boot = wl.spec if path == "spec" else reporter.ROUTER
        stdin = reporter.stdin_spec(wl) if path == "spec" else reporter.stdin_router(wl)
        expected = [c.expect for c in wl.checks]
        attempts = {k: [] for k in configs if k not in skip}
        for rep in range(args.reps):
            order = list(attempts)
            if rep % 2:
                order.reverse()
            for name in order:
                folder = args.out / f"{kind}-{size}-{path}-{name}-{rep + 1}"
                r = run_one(configs[name], boot, stdin, expected, folder, args.cap, args.rss_mib,
                            first_step=0 if path == "spec" else 2)
                attempts[name].append(r)
                print(folder.name, "PASS" if r["ok"] else "FAIL", f"cpu={r['cpu_s']:.3f}s wall={r['wall_s']:.3f}s", flush=True)
                if not r["ok"]:
                    record["failure"] = {"point": point, "variant": name, "attempt": r}
                    (args.out / "results.json").write_text(json.dumps(record, indent=2) + "\n")
                    return 1
        record["rows"].append({"kind": kind, "size": int(size), "path": path,
                               "skipped": skip, "variants": {k: aggregate(v) for k, v in attempts.items()}})
        (args.out / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    record["binary_sha256_after"] = {k: digest(v[0]) for k, v in configs.items()}
    record["ok"] = record["binary_sha256_after"] == record["binary_sha256"]
    (args.out / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
