#!/usr/bin/env python3
"""Check package integrity and the arithmetic of the recorded outcome counts."""
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
for line in (root / 'MANIFEST.sha256').read_text().splitlines():
    expected, name = line.split('  ', 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
cases = json.loads((root / 'cases.json').read_text())
saved = json.loads((root / 'observations.json').read_text())
rows = saved['results']
assert len(cases) == len(rows) == 14
assert len({c['name'] for c in cases}) == 14
mismatches = []
for case, row in zip(cases, rows):
    for key in ('name', 'group', 'input', 'expected'):
        assert case[key] == row[key], (case['name'], key)
    verdicts = re.findall(r'^%\d+: ([TF])\s*$', row['stdout'], re.M)
    assert row['returncode'] == 0 and verdicts == row['observed_verdicts'] and len(verdicts) == 1
    if verdicts != [case['expected']]:
        mismatches.append(case['name'])
assert mismatches == ['constant-equality', 'constant-validity', 'constant-assignment',
                      'point-existential', 'point-universal']
assert '(Error)' in rows[0]['stderr'] and '(Error)' in rows[1]['stderr'] and '(Error)' in rows[2]['stderr']
assert all('(Error)' not in row['stderr'] for row in rows[3:])
print('Package hashes and 14 saved results verified: 5 wrong answers, 9 matching controls.')
print('Expected answers are justified in README.md; this check does not rerun Tau.')
