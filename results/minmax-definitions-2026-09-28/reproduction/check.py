#!/usr/bin/env python3
"""Run small correctness examples against an explicitly supplied Tau binary."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
FLAGS = ['--charvar=false', '--color=false', '--highlighting=false',
         '--benchmarks=false', '--status=false', '-S', 'error',
         '--preprocessing=false', '--block-max-splits=0',
         '--bv-widening=false', '--bv-quantifier-free-decision=false']

def invoke(binary, command):
    with tempfile.TemporaryDirectory(prefix='tau-check-') as cwd:
        try:
            p = subprocess.run([str(binary), *FLAGS, '-e', command], cwd=cwd,
                               input='', capture_output=True, text=True, timeout=12)
            return dict(command=command, returncode=p.returncode,
                        stdout=p.stdout, stderr=p.stderr, timeout=False)
        except subprocess.TimeoutExpired as e:
            def text(x):
                return x.decode(errors='replace') if isinstance(x, bytes) else x or ''
            return dict(command=command, returncode=None, stdout=text(e.stdout),
                        stderr=text(e.stderr), timeout=True)

def clean(row):
    return row['returncode'] == 0 and not row['timeout'] and row['stderr'] == ''

def verdict(row, expected):
    return clean(row) and re.fullmatch(r'%\d+:\s*'+expected+r'\s*', row['stdout']) is not None

def model(row, kind):
    if not clean(row):
        return False
    match = re.fullmatch(r'\s*solution:\s*\{(.*?)\}\s*', row['stdout'], re.S)
    if not match:
        return False
    assignments = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'\s*([xy])\s*:=\s*\{\s*(-?\d+(?:\s*/\s*\d+)?)\s*\}:(qlt|bv\[3\])\s*', line)
        wanted_type = 'bv[3]' if kind == 'model-cast' else 'qlt'
        if not m or m[1] in assignments or m[3] != wanted_type:
            return False
        try:
            assignments[m[1]] = Fraction(re.sub(r'\s+', '', m[2]))
        except (ValueError, ZeroDivisionError):
            return False
    if kind == 'model-cast':
        return assignments == {'y': Fraction(2)}
    if kind == 'model-independent':
        return set(assignments) == {'x', 'y'} and assignments['y'] != 2 and assignments['x'] < 3
    if kind == 'model-distinct':
        return set(assignments) == {'x', 'y'} and assignments['x'] != assignments['y'] and assignments['x'] < 3
    if kind == 'model-control':
        return set(assignments) == {'x'} and assignments['x'] < 3
    raise ValueError(kind)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tau', type=Path, required=True)
    parser.add_argument('--group', help='Optional exact group name from cases.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite existing results')
    binary = args.tau.resolve(strict=True)
    cases = json.loads((ROOT/'cases.json').read_text())
    if args.group:
        cases = [c for c in cases if c['group'] == args.group]
    if not cases:
        raise SystemExit('No cases selected')
    results = []
    for case in cases:
        row = invoke(binary, case['command'])
        expected = case['expected']
        if expected == 'roundtrip':
            formula = re.fullmatch(r'%\d+:\s*([^\n]+)\s*', row['stdout'])
            if clean(row) and formula:
                followup = invoke(binary, 'sat '+formula[1].rstrip('.')+'.')
                passed = verdict(followup, 'T')
                row['reparsed'] = followup
            else:
                passed = False
        elif expected in ('T', 'F'):
            passed = verdict(row, expected)
        else:
            passed = model(row, expected)
        results.append(dict(case=case, observation=row, passed=passed))
    result = dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                  flags=FLAGS, checks=len(results), passed=sum(r['passed'] for r in results),
                  failed=sum(not r['passed'] for r in results), results=results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k:result[k] for k in ['checks', 'passed', 'failed']}))
    raise SystemExit(1 if result['failed'] else 0)

if __name__ == '__main__':
    main()
