#!/usr/bin/env python3
"""Check useful case splitting and combinations of controller and keyed rules."""
import argparse
import json
from pathlib import Path
import re
import sys

import measure


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unmodified", required=True)
    ap.add_argument("--patched", required=True)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--timings", action="store_true", help="Caller has stopped competing work for timing measurements")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    binaries = {k: str(Path(v).resolve()) for k, v in
                (("unmodified", args.unmodified), ("patched", args.patched))}
    configs = {"unmodified": [binaries["unmodified"], "-X"],
               **{f"budget_{n}": [binaries["patched"], "-X", "--bv-case-split-max-growth", str(n)]
                  for n in (1, 2, 8, 0)}}
    sources = ("issue107_script.txt", "mixed_controller_plus_rule_k9.txt",
               "mixed_controller_plus_rule_k12.txt", "keyed_rule_tau_output_k10.txt")
    record = {"schema": "tau203-controls/1", "rows": [],
              "binary_sha256": {k: measure.digest(v) for k, v in binaries.items()},
              "timing_note": ("Sequential timing run with competing build work paused." if args.timings else
                              "Correctness checks may run during compilation; these times are not benchmark evidence.")}
    for source in sources:
        script = (args.inputs / source).read_text()
        tau_output = source.startswith("keyed_rule")
        # Stop after the supplied inputs. A trailing q is a REPL command,
        # but at an active bitvector input prompt it is a malformed value.
        script = re.sub(r"(?m)^q\s*$", "", script)
        script = re.sub(r"(?m)^run (?:\d+ steps )?", "run " + ("1" if tau_output else "2") + " steps ", script, count=1)
        reference = None
        for name, command in configs.items():
            folder = args.out / (Path(source).stem + "-" + name)
            r = measure.run_one(command, None, script, ["F"] if tau_output else [], folder, 60, 1536)
            out = measure.ANSI.sub("", (folder / "stdout.txt").read_text())
            outputs = re.findall(r"^(o\d+\[\d+\])\s*:=\s*(.*)$", out, re.M)
            if name == "unmodified":
                reference = outputs
            values = dict(outputs)
            known = {"o5[0]": "F"} if tau_output else {"o3[0]": "0", "o3[1]": "9"}
            if source.startswith("mixed"):
                known.update({"o7[0]": "0", "o7[1]": "1"})
            r.update(outputs=outputs, same_outputs_as_unmodified=outputs == reference,
                     expected_values=known, expected_values_ok=all(values.get(k) == v for k, v in known.items()))
            r["ok"] = r["ok"] and r["same_outputs_as_unmodified"] and r["expected_values_ok"]
            (folder / "result.json").write_text(json.dumps(r, indent=2) + "\n")
            record["rows"].append({"source": source, "variant": name, "result": r})
            record["ok"] = all(row["result"]["ok"] for row in record["rows"])
            (args.out / "results.json").write_text(json.dumps(record, indent=2) + "\n")
            print(source, name, "PASS" if r["ok"] else "FAIL", flush=True)
            if not r["ok"]:
                return 1
    record["binary_sha256_after"] = {k: measure.digest(v) for k, v in binaries.items()}
    record["ok"] = record["ok"] and record["binary_sha256"] == record["binary_sha256_after"]
    (args.out / "results.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
