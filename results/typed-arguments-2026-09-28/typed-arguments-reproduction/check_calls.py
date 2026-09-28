#!/usr/bin/env python3
"""Check typed definition calls and their diagnostics in fresh Tau processes."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ANSI = re.compile(r'\x1b\[[0-9;]*m')


def cases():
    for algebra in ('sbf', 'bv[1]', 'bv[2]', 'bv[8]'):
        one = '1:sbf' if algebra == 'sbf' else '{1}:' + algebra
        zero = '0:sbf' if algebra == 'sbf' else '{0}:' + algebra
        definitions = f'g(x:{algebra}) := x:{algebra}. '
        shapes = {
            'constant': (definitions, one),
            'expression': (definitions, f'({one} & {one})'),
            'cast': (definitions, f'({algebra}) ({one})'),
            'nested': (f'h(u:{algebra}) := u:{algebra}. ' + definitions, f'h({one})'),
        }
        for shape, (defs, argument) in shapes.items():
            for truth, rhs in ((True, one), (False, zero)):
                for verb in ('normalize', 'sat', 'valid', 'unsat'):
                    yield {
                        'id': f'{algebra}-{shape}-{truth}-{verb}',
                        'source': f'{defs}{verb} g({argument}) = {rhs}.',
                        'answer': 'T' if truth != (verb == 'unsat') else 'F',
                    }
    for verb in ('normalize', 'sat', 'valid', 'unsat'):
        for tag, source in (
            ('algebra-mismatch', f'g(x) := x:sbf = 0. {verb} g(z:tau).'),
            ('width-mismatch', f'g(x:bv[2]) := x:bv[2] = 0. {verb} g({{1}}:bv[3]).'),
        ):
            yield {'id': f'{tag}-{verb}', 'source': source, 'error': 'disagrees with'}


def run(tau, case):
    flags = ['--charvar=false', '--color=false', '--highlighting=false',
             '--benchmarks=false', '--status=false', '-S', 'error']
    try:
        p = subprocess.run([str(tau), *flags, '-e', case['source']],
                           capture_output=True, text=True, timeout=8)
        out, err = ANSI.sub('', p.stdout), ANSI.sub('', p.stderr)
        answers = re.findall(r'^%\d+:\s*([TF])\s*$', out, re.M)
        if 'error' in case:
            passed = p.returncode == 0 and not answers and case['error'] in err
        else:
            passed = p.returncode == 0 and not err.strip() and answers == [case['answer']]
        return dict(case, returncode=p.returncode, stdout=p.stdout,
                    stderr=p.stderr, answers=answers, passed=passed)
    except subprocess.TimeoutExpired as e:
        return dict(case, timeout=True, passed=False,
                    stdout=(e.stdout or b'').decode(errors='replace'),
                    stderr=(e.stderr or b'').decode(errors='replace'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tau', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--without-bv', action='store_true')
    a = p.parse_args()
    binary = a.tau.resolve()
    selected = [c for c in cases() if not a.without_bv or 'bv[' not in c['source']]
    rows = [run(binary, c) for c in selected]
    result = dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  cases=rows, passed=sum(r['passed'] for r in rows), total=len(rows))
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{result['passed']}/{result['total']} strict checks passed")
    for r in rows:
        if not r['passed']:
            print('FAIL', r['id'], r.get('answers'), ANSI.sub('', r['stderr']).strip()[:200])
    raise SystemExit(0 if result['passed'] == result['total'] else 1)


if __name__ == '__main__':
    main()
