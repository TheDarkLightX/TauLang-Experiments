#!/usr/bin/env python3
"""Check issue 203 outputs against integer arithmetic at branch boundaries."""
import argparse
import dataclasses
import json
from pathlib import Path
import re
import sys

import measure
import tau_dispatch_blowup as reporter


def make_checks(kind, size):
    rows = []
    if kind == "terms":
        amounts = sorted({0, 2**24 - 1, *[1000*j+d for j in range(1,size+1) for d in (-1,0,1)]})
        for amount in amounts:
            for ident, mode in [(1,"all"),(1,"none"),(1,"last_missing"),(1,"alternating"),(0,"none")]:
                keys = [j+2 if mode == "all" or mode == "last_missing" and j < size-1
                        or mode == "alternating" and j % 2 == 0 else 0 for j in range(size)]
                expected = int(ident != 1 or all(amount <= 1000*(j+1) or keys[j] == j+2 for j in range(size)))
                vals = {1:str(amount),12:str(ident),**{18+j:str(k) for j,k in enumerate(keys)}}
                rows.append((f"amount={amount},id={ident},keys={mode}", expected, vals))
    else:
        for branch in range(1,size+1):
            ident = 4*branch-3
            expected_keys = [ident+1,ident+2,ident+3]
            amounts = [999,1000,1001,9999,10000,10001,99999,100000,100001]
            for amount in amounts:
                for mode in ("all","none","one_missing"):
                    keys = expected_keys[:] if mode != "none" else [0,0,0]
                    if mode == "one_missing":
                        keys[(branch-1)%3] = 0
                    thresholds = [1000,10000,100000]
                    expected = int(all(amount <= t or key == wanted for t,key,wanted in zip(thresholds,keys,expected_keys)))
                    vals = {1:str(amount),12:str(ident),**{18+j:str(k) for j,k in enumerate(keys)}}
                    rows.append((f"branch={branch},amount={amount},keys={mode}",expected,vals))
        for ident in (0,2,254):
            rows.append((f"fallback-id={ident}",1,{1:str(2**24-1),12:str(ident),18:"0",19:"0",20:"0"}))
    return [reporter.Check(label, expected, vals) for label,expected,vals in rows]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unmodified",required=True)
    ap.add_argument("--patched",required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    configs={"unmodified":[str(Path(args.unmodified).resolve())],
             "patched":[str(Path(args.patched).resolve())],
             "split_off":[str(Path(args.unmodified).resolve()),"--bv-case-split","false"]}
    record={"schema":"tau203-outputs/1","oracle":"Unsigned integer threshold and key comparisons, derived directly from the rule.",
            "binary_sha256":{k:measure.digest(v[0]) for k,v in configs.items()},"rows":[]}
    for kind,size in (("terms",12),("chain",12)):
        wl=reporter.terms_workload(size,8) if kind=="terms" else reporter.chain_workload(size,8,False)
        wl.checks=make_checks(kind,size)
        (args.out/f"{kind}-checks.json").write_text(json.dumps([dataclasses.asdict(c) for c in wl.checks],indent=2)+"\n")
        for name,cmd in configs.items():
            folder=args.out/f"{kind}-{name}"
            result=measure.run_one(cmd,wl.spec,reporter.stdin_spec(wl),[c.expect for c in wl.checks],folder,120,1536)
            out=measure.ANSI.sub("",(folder/"stdout.txt").read_text())
            indexed_o1=re.findall(r"o1\[(\d+)\]\s*:=\s*(\S+)",out)
            o1=[value for _,value in indexed_o1]
            expected_o1=[c.values[1] for c in wl.checks]
            result["o1_ok"] = o1 == expected_o1 and [int(index) for index,_ in indexed_o1] == list(range(len(wl.checks)))
            result["ok"] = result["ok"] and result["o1_ok"]
            (folder/"result.json").write_text(json.dumps(result,indent=2)+"\n")
            record["rows"].append({"kind":kind,"variant":name,"cases":len(wl.checks),"result":result})
            record["ok"]=all(r["result"]["ok"] for r in record["rows"])
            (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
            print(kind,name,len(wl.checks),"PASS" if result["ok"] else "FAIL",flush=True)
            if not result["ok"]:
                return 1
    record["binary_sha256_after"]={k:measure.digest(v[0]) for k,v in configs.items()}
    record["ok"] = record["ok"] and record["binary_sha256"] == record["binary_sha256_after"]
    (args.out/"results.json").write_text(json.dumps(record,indent=2)+"\n")
    return 0 if record["ok"] else 1


if __name__=="__main__":
    sys.exit(main())
