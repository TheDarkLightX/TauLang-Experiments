#!/usr/bin/env python3
"""Check printed Boolean expressions in fresh Tau processes."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess

CASES = [
    ("short-names", "normalize (x:sbf & y:sbf) = 0:sbf.",
     ["and", "x", "y"]),
    ("long-names", "normalize (alpha:sbf & beta:sbf) = 0:sbf.",
     ["and", "alpha", "beta"]),
    ("underscore-suffix", "normalize (left_:sbf & right_:sbf) = 0:sbf.",
     ["and", "left_", "right_"]),
    ("complement", "normalize (left:sbf & right:sbf') = 0:sbf.",
     ["and", "left", ["not", "right"]]),
    ("numeric-suffix", "normalize (left1:sbf & right2:sbf) = 0:sbf.",
     ["and", "left1", "right2"]),
    ("nested-left", "normalize ((left:sbf | right:sbf) & third:sbf) = 0:sbf.",
     ["and", ["or", "left", "right"], "third"]),
    ("nested-right", "normalize (left:sbf & (right:sbf | third:sbf)) = 0:sbf.",
     ["and", "left", ["or", "right", "third"]]),
    ("three-operands", "normalize (left:sbf & right:sbf & third:sbf) = 0:sbf.",
     ["and", ["and", "left", "right"], "third"]),
    ("eliminated-variable", "qelim ex x0:sbf (((x0:sbf & y0:sbf) ^ z:sbf) = 0:sbf).",
     ["and", "z", ["not", "y0"]]),
]
TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z_0-9]*\b")


def variables(expr):
    if isinstance(expr, str):
        return {expr}
    return set().union(*(variables(x) for x in expr[1:]))


def evaluate(expr, values):
    if isinstance(expr, str):
        return values[expr]
    args = [evaluate(x, values) for x in expr[1:]]
    if expr[0] == "not":
        return not args[0]
    if expr[0] == "and":
        return all(args)
    if expr[0] == "or":
        return any(args)
    raise ValueError(expr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    binary = args.tau.resolve()
    calls = []

    def call(command, charvar=False):
        flags = ["--charvar=" + str(charvar).lower(), "--color=false",
                 "--highlighting=false", "--benchmarks=false", "--status=false",
                 "-S", "error", "--preprocessing=false", "--block-max-splits=0",
                 "--bv-widening=false", "--bv-quantifier-free-decision=false"]
        record = {"command": command, "charvar": charvar}
        try:
            result = subprocess.run([str(binary), *flags, "-e", command],
                                    capture_output=True, text=True, timeout=12)
            record.update(returncode=result.returncode, stdout=result.stdout,
                          stderr=result.stderr)
            match = re.fullmatch(r"%1: ([^\n]+)\n*", result.stdout)
            answer = match.group(1).strip() if match else None
            if result.returncode or result.stderr or not answer:
                answer = None
        except subprocess.TimeoutExpired:
            record.update(timeout=True)
            answer = None
        calls.append(record)
        return answer

    results = []
    for name, command, expr in CASES:
        row = {"name": name, "command": command, "expected_expression": expr}
        printed = call(command)
        repeated = call(command)
        row.update(printed=printed, repeat_matches=printed == repeated and printed is not None)
        expected_names = variables(expr)
        actual_names = set(TOKEN.findall(printed or "")) - {"sbf", "T", "F"}
        row["no_new_variables"] = actual_names <= expected_names
        checks = []
        if printed is not None:
            for bits in itertools.product((False, True), repeat=len(expected_names)):
                values = dict(zip(sorted(expected_names), bits))
                expected = "F" if evaluate(expr, values) else "T"
                substituted = TOKEN.sub(
                    lambda m: ("{1}:sbf" if values[m[0]] else "{0}:sbf")
                    if m[0] in values else m[0], printed)
                got = call("normalize " + substituted + ".")
                checks.append({"values": values, "expected": expected, "actual": got,
                               "passed": got == expected})
        row["assignments"] = checks
        row["passed"] = (row["repeat_matches"] and row["no_new_variables"]
                         and len(checks) == 2 ** len(expected_names)
                         and all(x["passed"] for x in checks))
        results.append(row)

    controls = []
    for mode in (False, True):
        for command, expected in [("normalize T.", "T"), ("normalize F.", "F")]:
            got = call(command, mode)
            controls.append({"charvar": mode, "command": command, "expected": expected,
                             "actual": got, "passed": got == expected})
    default_text = call(CASES[0][1], True)
    report = {
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "cases": results, "controls": controls,
        "default_charvar_output": default_text, "calls": calls,
        "passed": all(x["passed"] for x in results + controls) and default_text is not None,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "cases": len(results),
                      "cases_passed": sum(x["passed"] for x in results),
                      "assignments": sum(len(x["assignments"]) for x in results),
                      "controls_passed": sum(x["passed"] for x in controls),
                      "default_charvar_output": default_text}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
