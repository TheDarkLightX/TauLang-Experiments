#!/usr/bin/env python3
"""Bounded comparison isolating one-step decisions from structural changes."""
import argparse
import json
from pathlib import Path
import platform
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repro", type=Path, required=True)
    ap.add_argument("--one-step", type=Path, required=True)
    ap.add_argument("--growth-only", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()
    sys.path.insert(0, str(args.repro.resolve()))
    import measure as m
    import tau_dispatch_blowup as g
    args.out.mkdir(parents=True, exist_ok=False)
    configs = {"one_step": [str(args.one_step.resolve())],
               "growth_only": [str(args.growth_only.resolve())],
               "structural": [str(args.candidate.resolve())]}
    record = {"platform": platform.platform(), "timing_scope": "whole process, including load and checked steps",
              "binary_sha256": {k: m.digest(v[0]) for k,v in configs.items()},
              "definitions": {"one_step": "growth guard plus one-step decision; structural elimination and normalizer stay at stock source",
                              "growth_only": "previously qualified case-split growth guard",
                              "structural": "growth guard plus one-step decision and refined structural elimination"},
              "cap_s": 30, "rss_mib": 1536, "rows": []}
    points = [("terms",12,"spec"), ("chain",16,"spec"),
              ("terms",10,"revision"), ("terms",12,"revision"), ("chain",16,"revision"),
              ("terms",12,"repeated_steps"), ("chain",16,"repeated_steps")]
    for kind, size, path in points:
        wl = g.terms_workload(size,8) if kind == "terms" else g.chain_workload(size,8,False)
        if path == "repeated_steps":
            wl.checks = wl.checks * 20
        revision = path == "revision"
        names = ["growth_only", "one_step", "structural"]
        attempts = {k: [] for k in names}
        for rep in range(args.reps):
            order = names if rep % 2 == 0 else list(reversed(names))
            for name in order:
                folder = args.out / f"{kind}-{size}-{path}-{name}-{rep+1}"
                result = m.run_one(configs[name], g.ROUTER if revision else wl.spec,
                                   g.stdin_router(wl) if revision else g.stdin_spec(wl),
                                   [c.expect for c in wl.checks], folder,30,1536,
                                   first_step=2 if revision else 0)
                attempts[name].append(result)
                print(folder.name, "PASS" if result["ok"] else "FAIL", f"cpu={result['cpu_s']:.3f}s", flush=True)
                if not result["ok"]:
                    record["failure"] = {"folder": str(folder), "result": result}
                    record["ok"] = False
                    (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
                    return 1
        record["rows"].append({"kind": kind,"size":size,"path":path,"checked_steps":len(wl.checks),
                               "variants": {k:m.aggregate(v) for k,v in attempts.items()}})
        (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
    record["binary_sha256_after"] = {k:m.digest(v[0]) for k,v in configs.items()}
    record["ok"] = record["binary_sha256"] == record["binary_sha256_after"]
    (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
