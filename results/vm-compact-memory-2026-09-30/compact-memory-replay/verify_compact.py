#!/usr/bin/env python3
"""Check saved answers, source transformation and compact-memory measurements."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import runpy
import statistics
import sys
sys.dont_write_bytecode = True
from compact_memory import transform

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--results', type=Path, default=ROOT / 'recorded/compact-memory-results.json')
parser.add_argument('--expected-binary-sha256', help='Explicit executable hash for a separately built replay')
args = parser.parse_args()
baseline = runpy.run_path(str(ROOT / 'verify_saved.py'))
expected = baseline['expected']
original = (ROOT / 'vm/spec/vm.tau').read_text()
compact, info = transform(original)
assert compact == (ROOT / 'vm/spec/vm-compact-memory.tau').read_text()
data = json.loads(args.results.read_text())
assert data['status'] == 'passed'
assert data['binary_sha256'] == (args.expected_binary_sha256 or baseline['build']['binary_sha256'])
assert data['original_vm_sha256'] == hashlib.sha256(original.encode()).hexdigest()
assert data['transformation'] == info
shape = {'status': 'admitted', 'inputs': '102', 'outputs': '21', 'decisions': '22',
         'leaves': '17', 'expressions': '60940', 'retained_terms': '455', 'budget': '1048576'}


def check_setup(row):
    assert row['admission'] == shape
    assert row['setup_seconds'] >= row['load_seconds'] + row['admission_seconds'] > 0
    for key in ['rss_after_load_kib', 'rss_after_admission_kib', 'rss_after_workload_kib']:
        assert row[key] > 0


seen = set()
for row in data['repeats']:
    key = (row['repeat'], row['arm'])
    assert key not in seen
    seen.add(key)
    assert row['order'] == (['shared', 'compact'] if row['repeat'] % 2 else ['compact', 'shared'])
    check_setup(row)
    assert set(row['workload']) == {'smoke', 'payroll', 'conformance'}
    times = []
    for name, values in row['workload'].items():
        assert [x['outputs'] for x in values] == expected[name], (key, name)
        times.extend(x['seconds'] for x in values)
    assert len(times) == row['steps'] == 55
    assert all(math.isfinite(t) and t > 0 for t in times)
    assert math.isclose(sum(times), row['step_sum_seconds'])
    assert math.isclose(statistics.median(times), row['step_median_seconds'])
assert seen == {(i, arm) for i in range(1, 6) for arm in ['shared', 'compact']}
assert set(data['distinct']) == {'shared', 'compact'}
totals = {}
for arm, row in data['distinct'].items():
    check_setup(row)
    assert [x['outputs'] for x in row['rows']] == expected['distinct'], arm
    times = [x['seconds'] for x in row['rows']]
    assert len(times) == 256 and all(math.isfinite(t) and t > 0 for t in times)
    assert math.isclose(sum(times), row['step_sum_seconds'])
    totals[arm] = row['setup_seconds'] + sum(times)
medians = {}
for arm in ['shared', 'compact']:
    rows = [row for row in data['repeats'] if row['arm'] == arm]
    medians[arm] = {name: statistics.median(row[name] for row in rows)
                    for name in ['setup_seconds', 'load_seconds', 'admission_seconds',
                                 'step_median_seconds', 'rss_after_workload_kib']}
summary = {'status': 'passed', 'checked_per_variant': 531, 'medians': medians,
           'setup_inclusive_distinct_seconds': totals,
           'setup_reduction_percent': 100 * (1 - medians['compact']['setup_seconds'] / medians['shared']['setup_seconds']),
           'rss_reduction_percent': 100 * (1 - medians['compact']['rss_after_workload_kib'] / medians['shared']['rss_after_workload_kib']),
           'setup_inclusive_speedup': totals['shared'] / totals['compact']}
print(json.dumps(summary, indent=2))
