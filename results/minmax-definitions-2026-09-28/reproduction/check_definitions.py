#!/usr/bin/env python3
"""Check small min/max definitions and fixed-point fallback values."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def cases():
    rows = []
    for width in (1, 2, 3):
        size = 1 << width
        constant = size // 2
        typ = f'bv[{width}]'
        for op, fn in [('min', min), ('max', max)]:
            definition = f'g(x:{typ}) := {op}(x:{typ}, {{{constant}}}:{typ}). '
            for value in range(size):
                result = fn(value, constant)
                wrong = (result + 1) % size
                for verb, relation, rhs, expected in [
                    ('normalize', '=', result, 'T'),
                    ('normalize', '=', wrong, 'F'),
                    ('sat', '=', result, 'T'),
                    ('valid', '!=', result, 'F'),
                ]:
                    rows.append(dict(family='definition', op=op, width=width,
                                     value=value, constant=constant, value_result=result,
                                     expected=expected, definitions=1,
                                     input=definition + f'{verb} g({{{value}}}:{typ}) {relation} {{{rhs}}}:{typ}.'))
    # f alternates between 0 and the all-ones word. Its explicit fallback
    # provides the result when that fixed-point iteration repeats.
    for op, fn in [('min', min), ('max', max)]:
        for value in range(4):
            result = fn(value, 2)
            for rhs, expected in [(result, 'T'), ((result + 1) % 4, 'F')]:
                definition = "f[0](x:bv[2]) := {0}:bv[2]. f[n](x:bv[2]) := f[n-1](x)'. "
                call = f'(f({{{value}}}:bv[2]) fallback {op}({{{value}}}:bv[2], {{2}}:bv[2]))'
                rows.append(dict(family='fallback', op=op, width=2, value=value,
                                 constant=2, value_result=result, expected=expected,
                                 definitions=2, input=definition + f'normalize {call} = {{{rhs}}}:bv[2].'))
    return rows


def verdict(row, observation):
    if observation.get('returncode') != 0 or observation.get('stderr'):
        return None
    lines = [line for line in observation.get('stdout', '').splitlines() if line.strip()]
    if len(lines) != row['definitions'] + 1:
        return None
    for index, line in enumerate(lines[:-1], 1):
        if not re.fullmatch(r'\[' + str(index) + r'\] .+', line):
            return None
    m = re.fullmatch(r'%1: (T|F)', lines[-1])
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tau', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('output already exists')
    binary = args.tau.resolve()
    flags = ['--charvar=false', '--color=false', '--highlighting=false',
             '--benchmarks=false', '--status=false', '-S', 'error',
             '--preprocessing=false', '--block-max-splits=0',
             '--bv-widening=false', '--bv-quantifier-free-decision=false']
    rows = []
    for example in cases():
        row = example.copy()
        try:
            r = subprocess.run([str(binary), *flags, '-e', row['input']],
                               capture_output=True, text=True, timeout=12)
            row.update(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
        except subprocess.TimeoutExpired:
            row['timeout'] = True
        row['actual'] = verdict(example, row)
        row['passed'] = row['actual'] == row['expected']
        rows.append(row)
    result = dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  flags=flags, cases=rows, passed=all(r['passed'] for r in rows))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], cases=len(rows),
                          cases_passed=sum(r['passed'] for r in rows))))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
