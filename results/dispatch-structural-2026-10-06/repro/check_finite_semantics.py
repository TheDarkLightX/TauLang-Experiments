#!/usr/bin/env python3
"""Compare closed formulas with exhaustive integer evaluation on tiny domains.

This tests complete normalization answers. Direct rewrite coverage is checked
separately by the C++ integration tests.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess


def evaluate(t, env, domain):
    op, *a = t
    if op == "eq":
        return env[a[0]] == (env[a[1]] if isinstance(a[1], str) else a[1])
    if op == "not":
        return not evaluate(a[0], env, domain)
    if op == "and":
        return evaluate(a[0], env, domain) and evaluate(a[1], env, domain)
    if op == "or":
        return evaluate(a[0], env, domain) or evaluate(a[1], env, domain)
    if op == "imply":
        return not evaluate(a[0], env, domain) or evaluate(a[1], env, domain)
    if op == "if":
        return evaluate(a[1] if evaluate(a[0], env, domain) else a[2], env, domain)
    if op in ("ex", "all"):
        values = (evaluate(a[1], dict(env, **{a[0]: v}), domain) for v in domain)
        return (any if op == "ex" else all)(values)
    raise ValueError(op)


def render(t, width):
    op, *a = t
    if op == "eq":
        right = a[1] if isinstance(a[1], str) else f"{{ {a[1]} }}:bv[{width}]"
        return f"({a[0]} = {right})"
    if op == "not":
        return f"!({render(a[0], width)})"
    if op in ("and", "or", "imply"):
        symbol = {"and": "&&", "or": "||", "imply": "->"}[op]
        return f"({render(a[0], width)} {symbol} {render(a[1], width)})"
    if op == "if":
        return f"({render(a[0], width)} ? {render(a[1], width)} : {render(a[2], width)})"
    if op in ("ex", "all"):
        return f"({op} {a[0]}:bv[{width}] {render(a[1], width)})"
    raise ValueError(op)


def make_cases():
    cases = []
    for width in (1, 2):
        domain = range(1 << width)
        for forbidden in itertools.chain.from_iterable(itertools.combinations(domain, k) for k in range(1, len(domain)+1)):
            tests = [("not", ("eq", "x", c)) for c in forbidden]
            for connect in ("and", "or"):
                tests_joined = tests[0]
                for test in tests[1:]:
                    tests_joined = (connect, tests_joined, test)
                y_test = ("eq", "y", 0)
                bodies = [
                    tests_joined,
                    ("and", tests_joined, y_test),
                    ("or", tests_joined, y_test),
                    ("imply", y_test, tests_joined),
                    ("imply", tests_joined, y_test),
                    ("if", y_test, tests_joined, ("not", y_test)),
                    ("not", tests_joined),
                ]
                for q in ("all", "ex"):
                    for body in bodies:
                        ast = ("ex", "x", (q, "y", body))
                        cases.append((width, ast))
        # Quantifier dependencies: exchanging the order changes the answer.
        for qx, qy in itertools.product(("ex", "all"), repeat=2):
            for neg in (False, True):
                body = ("eq", "x", "y")
                if neg:
                    body = ("not", body)
                cases.append((width, (qx, "x", (qy, "y", body))))
        cases.append((width, ("ex", "x", ("and", ("not", ("eq", "x", 0)),
                      ("all", "x", ("not", ("eq", "x", 0)))))))
    unique = {}
    for width, ast in cases:
        text = render(ast, width)
        unique[text] = {"formula": text, "width": width,
                        "expected": "T" if evaluate(ast, {}, range(1 << width)) else "F"}
    return list(unique.values())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cases-json", type=Path, help="Replay a supplied independently evaluated bank")
    ap.add_argument("options", nargs=argparse.REMAINDER)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    cases = json.loads(args.cases_json.read_text()) if args.cases_json else make_cases()
    if not cases or any(c.get("expected") not in ("T", "F", True, False) for c in cases):
        raise ValueError("Every case must carry an explicit expected truth value")
    cases = [dict(c, expected=("T" if c["expected"] else "F") if isinstance(c["expected"], bool) else c["expected"]) for c in cases]
    (args.out / "cases.json").write_text(json.dumps(cases, indent=2)+"\n")
    stdin = "set charvar off\n" + "\n".join("n "+c["formula"] for c in cases) + "\nq\n"
    (args.out / "stdin.txt").write_text(stdin)
    options = args.options[1:] if args.options[:1] == ["--"] else args.options
    command = [str(args.binary.resolve()), "-X", *options]
    before = digest(args.binary)
    with (args.out / "stdout.txt").open("w") as out, (args.out / "stderr.txt").open("w") as err:
        p = subprocess.run(command, input=stdin, text=True, stdout=out, stderr=err, timeout=60)
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", (args.out / "stdout.txt").read_text())
    errors = (args.out / "stderr.txt").read_text()
    actual = re.findall(r"^%\d+: (T|F)\s*$", text, re.M)
    expected = [c["expected"] for c in cases]
    mismatches = [{"index": i, **cases[i], "actual": v} for i, v in enumerate(actual[:len(cases)]) if v != expected[i]]
    result = {"command": command, "binary_sha256": before, "cases": len(cases),
              "answers": len(actual), "expected_true": expected.count("T"), "expected_false": expected.count("F"),
              "exit_code": p.returncode, "mismatches": mismatches,
              "ok": p.returncode == 0 and actual == expected and before == digest(args.binary)
                    and re.search(r"\b(Error|UNKNOWN)\b", text+errors) is None}
    (args.out / "result.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
