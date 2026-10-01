#!/usr/bin/env python3
"""Recompute saved VM outputs and timing summaries without launching Tau."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

sys.dont_write_bytecode = True
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('results', type=Path)
p.add_argument('--catalog', required=True, type=Path)
p.add_argument('--output', type=Path)
p.add_argument('--negative-checks', action='store_true')
a = p.parse_args()
catalog = a.catalog.resolve()
sys.path[:0] = [str(catalog), str(catalog / 'adapters'), str(catalog / 'vm/tools')]
import replay as common
from compile_tau import step

source = (catalog / 'vm/spec/vm.tau').read_text()
model = common.Parser(source).parse()
programs = common.read('programs.json')
conformance = common.read('conformance-cases.json')['inputs']
distinct = common.read('distinct-cases.json')['inputs']
expected = {}
for name, count, private in [('smoke', 3, []), ('payroll', 17, [10])]:
    state = common.ordinary.initial_state()
    expected[name] = []
    for _ in range(count):
        values = common.ordinary.inputs_for(programs[name], private, state)
        outputs = list(step(model, tuple(values)))
        expected[name].append(outputs)
        state = common.ordinary.state_from(outputs)
    assert state['halted']
expected['conformance'] = [list(step(model, tuple(v))) for v in conformance]
expected['distinct'] = [list(step(model, tuple(v))) for v in distinct]


def require(value, message):
    if not value:
        raise ValueError(message)


def close(actual, expected, label):
    require(isinstance(actual, (int, float)) and math.isfinite(actual)
            and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), label)


def verify(data):
    require(data['status'] == 'passed', 'incomplete replay')
    require(data['source_revision'] == 'a739b90259729590dee7b424df05ba65bfdeacf2', 'source revision')
    require(data['arms'] == {'baseline': [], 'parser_trim': [2, 5], 'selected': list(range(6))}, 'option sets')
    recorded = data['catalog_sha256']
    actual = {str(f.relative_to(catalog)): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(catalog.rglob('*')) if f.is_file()}
    require(recorded == actual, 'catalog changed')
    repeats = data['repeats']
    require(1 <= repeats <= 5, 'repeat count')
    require(len(data['rows']) == 3 * repeats, 'missing process')
    require(len({(r['repeat'], r['arm']) for r in data['rows']}) == 3 * repeats, 'duplicate process')
    arms = list(data['arms'])
    index = 0
    for repeat in range(1, repeats + 1):
        order = arms if repeat % 2 else list(reversed(arms))
        for arm in order:
            row = data['rows'][index]
            index += 1
            require((row['repeat'], row['arm'], row['order']) == (repeat, arm, order), 'process order')
            require(row['steps'] == 311, 'workload size')
            require(set(row['workload']) == set(expected), 'workload names')
            times = []
            for name, values in expected.items():
                records = row['workload'][name]
                require([v['outputs'] for v in records] == values, 'output mismatch: ' + name)
                times.extend(v['seconds'] for v in records)
            require(all(math.isfinite(v) and v > 0 for v in times), 'invalid step time')
            close(row['step_sum_seconds'], sum(times), 'step sum')
            close(row['step_median_seconds'], statistics.median(times), 'step median')
            close(row['total_seconds'], row['setup_seconds'] + sum(times), 'total time')
            require(row['setup_seconds'] >= row['load_seconds'] + row['admission_seconds'], 'setup accounting')
            require(all(isinstance(row[k], int) and row[k] > 0 for k in [
                'rss_after_load_kib', 'rss_after_admission_kib', 'rss_after_workload_kib']), 'RSS sample')
            shape = {'status': 'admitted', 'inputs': '102', 'outputs': '21', 'decisions': '22',
                     'leaves': '17', 'expressions': '60940', 'retained_terms': '455', 'budget': '1048576'}
            require(row['admission'] == shape, 'admission changed')
            counters = row['telemetry']
            if data['telemetry']:
                phases = ['before_admission', 'after_admission', 'after_parse_scratch_release',
                          'after_reclaim', 'checkpoint'] + ['after_evaluation'] * 55 + ['checkpoint']
                phases += ['after_evaluation'] * 256 + ['checkpoint']
                require([v['phase'] for v in counters] == phases, 'telemetry sequence')
                require(counters[-1]['parse_scratch_releases'] == (0 if arm == 'baseline' else 1), 'release count')
                expected_trim = 1 if 'glibc' in data['platform'] and arm != 'baseline' else 0
                require(counters[-1]['trim_calls'] == expected_trim, 'allocator trim count')
                if arm == 'selected':
                    for key in ['constant_pool_entries', 'normalizer_cache_entries', 'output_scratch_heap_allocations']:
                        require(counters[-1][key] == counters[1][key], 'storage grew: ' + key)
            else:
                require(not counters, 'telemetry during measurements')
    summary = {}
    for arm in arms:
        rows = [r for r in data['rows'] if r['arm'] == arm]
        summary[arm] = {k: statistics.median(r[k] for r in rows) for k in [
            'setup_seconds', 'step_median_seconds', 'total_seconds', 'rss_after_workload_kib']}
        summary[arm]['rss_after_workload_mib'] = summary[arm]['rss_after_workload_kib'] / 1024
    return {'status': 'passed', 'model_checks': index * 311, 'processes': index, 'medians': summary}


data = json.loads(a.results.read_text())
result = verify(data)
if a.negative_checks:
    result['rejected_mutations'] = []
    for name in ['missing process', 'changed output', 'changed step sum', 'changed RSS type']:
        bad = copy.deepcopy(data)
        if name == 'missing process':
            bad['rows'].pop()
        elif name == 'changed output':
            bad['rows'][0]['workload']['smoke'][0]['outputs'][0] ^= 1
        elif name == 'changed step sum':
            bad['rows'][0]['step_sum_seconds'] += 1
        else:
            bad['rows'][0]['rss_after_workload_kib'] = None
        try:
            verify(bad)
        except (ValueError, TypeError):
            result['rejected_mutations'].append(name)
        else:
            raise ValueError('Verifier accepted ' + name)
if a.output:
    a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
