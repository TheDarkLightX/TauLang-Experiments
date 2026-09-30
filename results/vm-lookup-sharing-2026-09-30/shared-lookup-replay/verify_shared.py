#!/usr/bin/env python3
"""Recompute saved VM answers and the shared-lookup comparison."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import runpy
import statistics
import sys
sys.dont_write_bytecode = True
from share_lookups import transform

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--results', type=Path, default=ROOT / 'recorded/shared-lookup-results.json')
args = parser.parse_args()
baseline = runpy.run_path(str(ROOT / 'verify_saved.py'))
expected = baseline['expected']
original = (ROOT / 'vm/spec/vm.tau').read_text()
modified, helpers = transform(original)
assert modified == (ROOT / 'vm/spec/vm-shared-lookups.tau').read_text()
assert helpers == json.loads((ROOT / 'recorded/shared-lookup-helpers.json').read_text())
data = json.loads(args.results.read_text())
assert data['status'] == 'passed'
assert data['binary_sha256'] == baseline['build']['binary_sha256']
assert data['original_vm_sha256'] == hashlib.sha256(original.encode()).hexdigest()
assert data['shared_vm_sha256'] == hashlib.sha256(modified.encode()).hexdigest()
assert data['source_bytes'] == {'original': len(original.encode()), 'shared': len(modified.encode())}
assert data['exact_reverse_expansion'] is True
shape = {'status': 'admitted', 'inputs': '102', 'outputs': '21', 'decisions': '22',
         'leaves': '17', 'expressions': '60940', 'retained_terms': '455', 'budget': '1048576'}
seen = set()
for row in data['repeats']:
    key = (row['repeat'], row['arm'])
    assert key not in seen
    seen.add(key)
    assert row['order'] == (['original', 'shared'] if row['repeat'] % 2 else ['shared', 'original'])
    assert row['admission'] == shape
    assert set(row['workload']) == {'smoke', 'payroll', 'conformance'}
    times = []
    for name, values in row['workload'].items():
        assert [x['outputs'] for x in values] == expected[name], (key, name)
        times.extend(x['seconds'] for x in values)
    assert len(times) == row['steps'] == 55
    assert all(math.isfinite(x) and x > 0 for x in times)
    assert math.isclose(sum(times), row['step_sum_seconds'])
    assert math.isclose(statistics.median(times), row['step_median_seconds'])
    assert row['setup_seconds'] >= row['load_seconds'] + row['admission_seconds'] > 0
    assert row['rss_after_workload_kib'] > 0
assert seen == {(i, arm) for i in range(1, 6) for arm in ['original', 'shared']}
assert set(data['distinct']) == {'original', 'shared', 'ordinary'}
totals = {}
for arm, row in data['distinct'].items():
    assert [x['outputs'] for x in row['rows']] == expected['distinct'], arm
    times = [x['seconds'] for x in row['rows']]
    assert len(times) == 256 and all(math.isfinite(x) and x > 0 for x in times)
    assert math.isclose(sum(times), row['step_sum_seconds'])
    assert row['setup_seconds'] > 0
    totals[arm] = row['setup_seconds'] + sum(times)
medians = {}
for arm in ['original', 'shared']:
    rows = [x for x in data['repeats'] if x['arm'] == arm]
    medians[arm] = {name: statistics.median(x[name] for x in rows)
                    for name in ['setup_seconds', 'load_seconds', 'admission_seconds',
                                 'step_median_seconds', 'rss_after_workload_kib']}
summary = {'status': 'passed', 'checked_per_retained_variant': 531, 'ordinary_checks': 256,
           'medians': medians, 'setup_inclusive_distinct_seconds': totals,
           'setup_reduction_percent': 100 * (1 - medians['shared']['setup_seconds'] / medians['original']['setup_seconds']),
           'rss_reduction_percent': 100 * (1 - medians['shared']['rss_after_workload_kib'] / medians['original']['rss_after_workload_kib']),
           'setup_inclusive_speedup_over_original': totals['original'] / totals['shared'],
           'setup_inclusive_speedup_over_ordinary': totals['ordinary'] / totals['shared']}
print(json.dumps(summary, indent=2))
