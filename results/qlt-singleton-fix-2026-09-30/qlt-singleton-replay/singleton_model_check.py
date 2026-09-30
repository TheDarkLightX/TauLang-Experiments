#!/usr/bin/env python3
"""Compare quantified singleton membership with an independent Boolean model."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('binary', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
terms = [('x', lambda x,y: x), ('x & y', lambda x,y: x and y),
         ('x | y', lambda x,y: x or y), ('x ^ y', lambda x,y: x != y)]
cases = []
for (term, evaluate), negate_a, negate_b, conjunction, qx, qy in itertools.product(
        terms, (False, True), (False, True), (False, True), ('ex', 'all'), ('ex', 'all')):
    left = f'(({{3}}:qlt & ({term})) {"=" if negate_a else "!="} 0)'
    right = f'(({{3}}:qlt & y) {"=" if negate_b else "!="} 0)'
    command = f'normalize {qx} x:qlt {qy} y:qlt ({left} {"&&" if conjunction else "||"} {right}).'
    by_x = []
    for x in (False, True):
        by_y = []
        for y in (False, True):
            av, bv = evaluate(x,y) != negate_a, y != negate_b
            by_y.append(av and bv if conjunction else av or bv)
        by_x.append((any if qy == 'ex' else all)(by_y))
    expected = 'T' if (any if qx == 'ex' else all)(by_x) else 'F'
    cases.append({'command': command, 'expected': expected})
source = '\n'.join(c['command'] for c in cases) + '\n'
a.output.mkdir(parents=True, exist_ok=True)
(a.output/'inputs.tau').write_text(source)
r = subprocess.run([str(a.binary.resolve()), '--charvar', 'false', '-c', 'false', '-S', 'error', '-q'],
                   input=source, capture_output=True, text=True, timeout=120)
actual = re.findall(r'^%\d+: (.*)$', r.stdout, re.M)
for i, c in enumerate(cases):
    c['actual'] = actual[i] if i < len(actual) else None
    c['passed'] = c['actual'] == c['expected']
report = {'binary_sha256': hashlib.sha256(a.binary.read_bytes()).hexdigest(),
          'model': 'Each variable independently either contains the one tested point or does not. Both assignments have rational singleton witnesses.',
          'returncode': r.returncode, 'total': len(cases),
          'passed': sum(c['passed'] for c in cases), 'outputs': len(actual), 'cases': cases}
(a.output/'stdout.txt').write_text(r.stdout)
(a.output/'stderr.txt').write_text(r.stderr)
(a.output/'results.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, indent=2))
raise SystemExit(0 if r.returncode == 0 and report['passed'] == len(cases) and len(actual) == len(cases) else 1)
