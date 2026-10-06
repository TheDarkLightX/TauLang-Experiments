#!/usr/bin/env python3
"""Preserve and re-run the exact specification printed after a live update."""
import argparse
import json
from pathlib import Path
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repro", type=Path, required=True)
    ap.add_argument("--growth-only", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.repro.resolve()))
    import measure as m
    import tau_dispatch_blowup as g
    args.out.mkdir(parents=True, exist_ok=False)
    configs = {"growth_only": [str(args.growth_only.resolve())], "structural": [str(args.candidate.resolve())]}
    record = {"schema": "tau203-reparse/1", "binary_sha256": {k:m.digest(v[0]) for k,v in configs.items()}, "rows": []}
    for kind, size in (("terms",10),("chain",8)):
        wl = g.terms_workload(size,8) if kind == "terms" else g.chain_workload(size,8,False)
        expected = [c.expect for c in wl.checks]
        for producer, cmd in configs.items():
            folder = args.out/f"{kind}-{size}-revision-{producer}"
            result = m.run_one(cmd,g.ROUTER,g.stdin_router(wl),expected,folder,30,1536,first_step=2)
            record["rows"].append({"path":"revision","kind":kind,"size":size,"producer":producer,"result":result})
            if result["ok"]:
                text = m.ANSI.sub("",(folder/"stdout.txt").read_text())
                updates = g.UPDATED.findall(text)
                result["updates_found"] = len(updates)
                result["ok"] = len(updates) == 2
            if result["ok"]:
                # Both consumers read the same printed form from each producer.
                for consumer, consume in configs.items():
                    target = args.out/f"{kind}-{size}-reparse-{producer}-on-{consumer}"
                    replay = m.run_one(consume,updates[-1]+".\n",g.stdin_reparse(wl),expected,target,30,1536)
                    out = m.ANSI.sub("",(target/"stdout.txt").read_text())
                    observed = re.findall(r"o1\[(\d+)\]\s*:=\s*(\S+)",out)
                    replay["o1_ok"] = observed == [(str(i),c.values[1]) for i,c in enumerate(wl.checks)]
                    replay["ok"] = replay["ok"] and replay["o1_ok"]
                    (target/"result.json").write_text(json.dumps(replay,indent=2)+"\n")
                    record["rows"].append({"path":"reparse","kind":kind,"size":size,"producer":producer,"consumer":consumer,"result":replay})
                    print(kind,size,producer,consumer,"PASS" if replay["ok"] else "FAIL",flush=True)
                    if not replay["ok"]:
                        break
            record["ok"] = all(x["result"]["ok"] for x in record["rows"])
            (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
            if not record["ok"]:
                return 1
    record["ok"] = record["ok"] and record["binary_sha256"] == {k:m.digest(v[0]) for k,v in configs.items()}
    (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
