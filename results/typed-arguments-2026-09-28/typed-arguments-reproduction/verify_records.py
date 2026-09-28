#!/usr/bin/env python3
"""Recompute saved command outcomes; do not trust the recorded pass flags."""
import json
import re
from pathlib import Path
import check_calls
import check_definitions

root = Path(__file__).resolve().parent
for path in sorted((root / 'recorded').glob('*calls*.json')):
    data = json.loads(path.read_text())
    expected = {c['id']: c for c in check_calls.cases()}
    if 'nobv' in path.name:
        expected = {k: c for k, c in expected.items() if 'bv[' not in c['source']}
    assert len(data['cases']) == len(expected), path
    seen = set()
    passed = 0
    unresolved = []
    for row in data['cases']:
        case = expected[row['id']]
        assert row['id'] not in seen
        seen.add(row['id'])
        for k, value in case.items():
            assert row[k] == value, (path, row['id'], k)
        out = check_calls.ANSI.sub('', row['stdout'])
        err = check_calls.ANSI.sub('', row['stderr'])
        answers = re.findall(r'^%\d+:\s*([TF])\s*$', out, re.M)
        if 'error' in case:
            ok = row.get('returncode') == 0 and not answers and case['error'] in err
        else:
            ok = row.get('returncode') == 0 and not err.strip() and answers == [case['answer']]
        assert row['passed'] == ok, (path, row['id'])
        passed += ok
        if not ok:
            unresolved.append(row['id'])
    assert set(expected) == seen
    assert passed == data['passed'] and len(seen) == data['total']
    print(path.name, f'{passed}/{len(seen)}', 'unresolved:', len(unresolved))
before = json.loads((root / 'recorded/reference-calls.json').read_text())
after = json.loads((root / 'recorded/corrected-default-calls.json').read_text())
before_by_id = {r['id']: r for r in before['cases']}
valid_before = [r for r in before['cases'] if 'error' not in r]
assert sum('disagrees with' in r['stderr'] for r in valid_before) == 96
assert not any('disagrees with' in r['stderr'] for r in after['cases'] if 'error' not in r)
assert all(r['passed'] for r in after['cases'] if before_by_id[r['id']]['passed'])

data = json.loads((root / 'recorded/minmax-integration.json').read_text())
expected = check_definitions.cases()
assert len(data['cases']) == len(expected) == 128
for row, case in zip(data['cases'], expected):
    for key, value in case.items():
        assert row[key] == value
    actual = check_definitions.verdict(case, row)
    assert actual == row['actual'] == case['expected'] and row['passed']
assert data['passed']
print('minmax-integration.json: 128/128 strict passes')

data = json.loads((root / 'recorded/ctest-results.json').read_text())
for name, suite in data.items():
    assert suite['total'] == len(suite['tests'])
    assert suite['passed'] == sum(r['status'] == 'passed' for r in suite['tests'])
    assert suite['failed'] == [r['name'] for r in suite['tests'] if r['status'] == 'failed']
    print(name, str(suite['passed']) + '/' + str(suite['total']))
print('Saved counts and outcomes agree with the complete case lists.')
