#!/usr/bin/env python3
"""Check and compare retained VM memory options on one pinned executable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--catalog', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--repeats', type=int, default=5, choices=range(1, 6))
parser.add_argument('--telemetry', action='store_true')
args = parser.parse_args()
catalog = args.catalog.resolve()
sys.path[:0] = [str(catalog), str(catalog / 'adapters'), str(catalog / 'vm/tools')]
import replay as common
import native_tau_eval as retained
from native_tau_compact import CompactMemoryTau

PIN = 'a739b90259729590dee7b424df05ba65bfdeacf2'
common.ordinary.TAU_COMMIT = PIN
retained.nt.TAU_COMMIT = PIN
SWITCHES = ['TAU_EVAL_DECIMAL_ONLY', 'TAU_EVAL_TRANSIENT_NORMALIZE', 'TAU_EVAL_TRIM',
            'TAU_EVAL_ARENA_OUTPUTS', 'TAU_EVAL_FLAT_LEAVES', 'TAU_EVAL_RELEASE_PARSE_SCRATCH']
ARMS = {'baseline': [], 'parser_trim': [2, 5], 'selected': list(range(6))}
SHAPE = {'status': 'admitted', 'inputs': '102', 'outputs': '21', 'decisions': '22',
         'leaves': '17', 'expressions': '60940', 'retained_terms': '455', 'budget': '1048576'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return {str(p.relative_to(catalog)): sha(p) for p in sorted(catalog.rglob('*')) if p.is_file()}


class Client(CompactMemoryTau):
    def __init__(self, *values, **keywords):
        self.telemetry = []
        super().__init__(*values, **keywords)

    def _read_response(self, deadline=None):
        output, error = super()._read_response(deadline)
        for line in output.splitlines():
            if line.startswith('tau-memory: '):
                self.telemetry.append(json.loads(line[len('tau-memory: '):]))
        return output, error


binary = args.binary.resolve()
version = subprocess.check_output([str(binary), '--version'], text=True, timeout=15)
if not common.ordinary.matches_pinned_version(version):
    raise ValueError('Unexpected Tau version')
before = inventory()
vm = (catalog / 'vm/spec/vm.tau').read_text()
model = common.Parser(vm).parse()
programs = common.read('programs.json')
conformance = common.read('conformance-cases.json')['inputs']
distinct = common.read('distinct-cases.json')['inputs']
args.output.mkdir(parents=True, exist_ok=False)
data = {'status': 'incomplete', 'source_revision': PIN, 'binary_sha256': sha(binary),
        'version': version.strip(), 'platform': platform.platform(), 'catalog_sha256': before,
        'repeats': args.repeats, 'telemetry': args.telemetry, 'arms': ARMS, 'rows': [],
        'scope': '311 model-checked evaluations per process; sampled RSS is not lifetime peak memory.'}


def save():
    temporary = args.output / 'results.tmp'
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(args.output / 'results.json')


try:
    for repeat in range(1, args.repeats + 1):
        order = list(ARMS) if repeat % 2 else list(reversed(ARMS))
        for arm in order:
            os.environ.update({name: '1' if i in ARMS[arm] else '0' for i, name in enumerate(SWITCHES)})
            os.environ['TAU_MEMORY_TELEMETRY'] = '1' if args.telemetry else '0'
            begin = time.perf_counter()
            with Client(binary, source=vm) as client:
                setup = time.perf_counter() - begin
                if client.admit_frame != SHAPE:
                    raise ValueError('Admitted interface changed')
                work = {'smoke': common.trace(client, model, programs['smoke'], [], 3),
                        'payroll': common.trace(client, model, programs['payroll'], [10], 17),
                        'conformance': [common.checked_step(client, model, v) for v in conformance]}
                if args.telemetry and retained.parse_frame(client.command('evalspec %1')) != SHAPE:
                    raise ValueError('Cached admission changed')
                work['distinct'] = [common.checked_step(client, model, v) for v in distinct]
                if args.telemetry and retained.parse_frame(client.command('evalspec %1')) != SHAPE:
                    raise ValueError('Final cached admission changed')
                rss = common.memory_kib(client.process.pid)
                counters = client.telemetry
                if args.telemetry:
                    expected = ['before_admission', 'after_admission', 'after_parse_scratch_release',
                                'after_reclaim', 'checkpoint']
                    expected += ['after_evaluation'] * 55 + ['checkpoint']
                    expected += ['after_evaluation'] * 256 + ['checkpoint']
                    if [x['phase'] for x in counters] != expected:
                        raise ValueError('Incomplete telemetry sequence')
                    if arm == 'selected':
                        for key in ['constant_pool_entries', 'normalizer_cache_entries', 'output_scratch_heap_allocations']:
                            if counters[-1][key] != counters[1][key]:
                                raise ValueError('Selected storage grew: ' + key)
                    if arm != 'baseline' and counters[-1]['parse_scratch_releases'] != 1:
                        raise ValueError('Expected one parser scratch release')
                elif counters:
                    raise ValueError('Telemetry enabled during timing confirmation')
                times = [v['seconds'] for group in work.values() for v in group]
                if len(times) != 311:
                    raise ValueError('Incomplete VM workload')
                row = {'repeat': repeat, 'arm': arm, 'order': order, 'setup_seconds': setup,
                       'load_seconds': client.load_seconds, 'admission_seconds': client.admit_seconds,
                       'rss_after_load_kib': client.rss_after_load_kib,
                       'rss_after_admission_kib': client.rss_after_admit_kib,
                       'rss_after_workload_kib': rss, 'steps': len(times), 'admission': client.admit_frame,
                       'step_median_seconds': statistics.median(times), 'step_sum_seconds': sum(times),
                       'total_seconds': setup + sum(times), 'workload': work, 'telemetry': counters}
            data['rows'].append(row)
            save()
            print(json.dumps({k: row[k] for k in ['repeat', 'arm', 'steps', 'setup_seconds', 'rss_after_workload_kib']}), flush=True)
    if inventory() != before or sha(binary) != data['binary_sha256']:
        raise ValueError('Executable or catalog changed during replay')
    data['status'] = 'passed'
except BaseException as error:
    data.update(status='failed', error=str(error))
    raise
finally:
    save()
print(json.dumps({'status': data['status'], 'model_checks': sum(r['steps'] for r in data['rows'])}))
