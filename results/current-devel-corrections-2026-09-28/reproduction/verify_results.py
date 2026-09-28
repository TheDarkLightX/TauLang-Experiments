#!/usr/bin/env python3
"""Recalculate the recorded checks from complete process observations."""
import hashlib
import itertools
import json
from pathlib import Path
import re

from check import CASES, TOKEN, evaluate, variables

root = Path(__file__).resolve().parent
for line in (root / 'SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name

info = json.loads((root / 'build-info.json').read_text())
assert info['tau_commit'] == '8b5a61ca98a72f0a2cbece9b1338c7295482bbd3'
assert info['parser_commit'] == '5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a'

for variant, expected_passes in [('original', 4), ('corrected', 9)]:
    report = json.loads((root / (variant + '-roundtrips.json')).read_text())
    assert report['binary_sha256'] == info[variant + '_binary_sha256']
    calls = iter(report['calls'])

    def observed(command, charvar=False):
        call = next(calls)
        assert call['command'] == command and call['charvar'] == charvar
        match = re.fullmatch(r'%1: ([^\n]+)\n*', call.get('stdout', ''))
        if call.get('returncode') != 0 or call.get('stderr') or not match:
            return None
        return match.group(1).strip() or None

    assert len(report['cases']) == len(CASES) == 9
    passes = 0
    assignment_count = 0
    for row, (name, command, expr) in zip(report['cases'], CASES):
        assert (row['name'], row['command'], row['expected_expression']) == (name, command, expr)
        printed, repeated = observed(command), observed(command)
        same = printed is not None and printed == repeated
        names = variables(expr)
        no_new_names = set(TOKEN.findall(printed or '')) - {'sbf', 'T', 'F'} <= names
        assert row['printed'] == printed
        assert row['repeat_matches'] == same and row['no_new_variables'] == no_new_names
        checks = []
        if printed is not None:
            for bits in itertools.product((False, True), repeat=len(names)):
                values = dict(zip(sorted(names), bits))
                expected = 'F' if evaluate(expr, values) else 'T'
                substituted = TOKEN.sub(
                    lambda m: ('{1}:sbf' if values[m[0]] else '{0}:sbf')
                    if m[0] in values else m[0], printed)
                actual = observed('normalize ' + substituted + '.')
                checks.append(dict(values=values, expected=expected, actual=actual,
                                   passed=actual == expected))
        assert checks == row['assignments']
        passed = same and no_new_names and len(checks) == 2 ** len(names) and all(c['passed'] for c in checks)
        assert row['passed'] == passed
        passes += passed
        assignment_count += len(checks)
    assert passes == expected_passes
    assert len(report['controls']) == 4
    for row, (mode, expected) in zip(report['controls'], itertools.product((False, True), ('T', 'F'))):
        command = 'normalize ' + expected + '.'
        actual = observed(command, mode)
        assert row == dict(charvar=mode, command=command, expected=expected,
                           actual=actual, passed=actual == expected)
        assert actual == expected
    assert observed(CASES[0][1], True) == report['default_charvar_output'] == 'xy = 0'
    assert next(calls, None) is None
    assert report['passed'] == (variant == 'corrected')
    assert assignment_count == 48

suite = json.loads((root / 'release-tests.json').read_text())
assert suite['returncode'] == 8
assert len(suite['tests']) == suite['registered_tests']
assert len({t['name'] for t in suite['tests']}) == len(suite['tests'])
assert [t['name'] for t in suite['tests'] if t['status'] != 'passed'] == ['test_repl-run_cmd-values_stay_within_constant_size_budget']
comparison = json.loads((root / 'constant-budget-comparison.json').read_text())
assert len(comparison) == 2
outputs = []
for row in comparison:
    assert row['returncode'] == 0
    assert not re.search(r'o1\[9\] := ', row['stdout'])
    assert 'passed the constant size budget' in row['stdout'] + row['stderr']
    values = re.findall(r'^o1\[\d+\] := .*$', row['stdout'], re.M)
    assert values == row['output_values'] and len(values) == 9
    outputs.append(values)
assert outputs[0] == outputs[1]
assert 'give-up reports unsatisfiable' in (root / 'original-help.txt').read_text()
assert 'boundary; reaching the cap reports no verdict' in (root / 'corrected-help.txt').read_text()
assert 'give-up reports unsatisfiable' not in (root / 'corrected-help.txt').read_text()
print(f"Verified 4/9 original and 9/9 corrected examples, 48 assignments per build, controls, help, and {suite['registered_tests'] - 1}/{suite['registered_tests']} passing registered tests; the remaining test also fails on the reference build.")
