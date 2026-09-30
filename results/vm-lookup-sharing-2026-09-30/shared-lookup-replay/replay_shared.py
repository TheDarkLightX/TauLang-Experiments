#!/usr/bin/env python3
"""Compare original and shared-lookup loading with the same evaluator binary."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'adapters'), str(ROOT / 'vm/tools')]
import replay as common
import native_tau_shared as shared
from share_lookups import transform


def run(binary, output, repeats):
    output.mkdir(exist_ok=False)
    source = (ROOT / 'vm/spec/vm.tau').read_text()
    modified, helpers = transform(source)
    (output / 'vm-shared-lookups.tau').write_text(modified)
    (output / 'helpers.json').write_text(json.dumps(helpers, indent=2) + '\n')
    model = common.Parser(source).parse()
    vectors = common.read('conformance-cases.json')['inputs']
    cases = common.read('distinct-cases.json')['inputs']
    programs = common.read('programs.json')
    version = subprocess.check_output([str(binary), '--version'], text=True, timeout=15)
    if not common.ordinary.matches_pinned_version(version):
        raise ValueError('Use the pinned evaluator build')
    result = {'status': 'incomplete', 'version': version.strip(),
              'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'original_vm_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'shared_vm_sha256': hashlib.sha256(modified.encode()).hexdigest(),
              'source_bytes': {'original': len(source.encode()), 'shared': len(modified.encode())},
              'exact_reverse_expansion': True, 'platform': platform.platform(),
              'repeats': [], 'distinct': {},
              'scope': 'Five alternating 55-transition runs per retained variant; one additional 256-input run for each retained variant and the ordinary adapter. Process RSS samples are not peaks.'}

    def opened(arm):
        os.environ['TAU_CONCRETE_EVAL'] = '0' if arm == 'ordinary' else '1'
        kind = {'ordinary': common.ordinary.NativeTau,
                'original': common.retained.EvalspecTau,
                'shared': shared.SharedLookupTau}[arm]
        return kind(binary, source=source)

    def setup(client, elapsed):
        return {'setup_seconds': elapsed, 'load_seconds': client.load_seconds,
                'admission_seconds': client.admit_seconds,
                'rss_after_load_kib': client.rss_after_load_kib,
                'rss_after_admission_kib': client.rss_after_admit_kib,
                'admission': client.admit_frame}

    expected_shape = {'status': 'admitted', 'inputs': '102', 'outputs': '21',
                      'decisions': '22', 'leaves': '17', 'expressions': '60940',
                      'retained_terms': '455', 'budget': '1048576'}
    try:
        for index in range(repeats):
            order = ['original', 'shared'] if index % 2 == 0 else ['shared', 'original']
            for arm in order:
                start = time.perf_counter()
                with opened(arm) as client:
                    row = setup(client, time.perf_counter() - start)
                    if row['admission'] != expected_shape:
                        raise ValueError('Admitted representation changed')
                    workload = {'smoke': common.trace(client, model, programs['smoke'], [], 3),
                                'payroll': common.trace(client, model, programs['payroll'], [10], 17),
                                'conformance': [common.checked_step(client, model, values) for values in vectors]}
                    row['rss_after_workload_kib'] = common.memory_kib(client.process.pid)
                times = [x['seconds'] for group in workload.values() for x in group]
                row.update(repeat=index + 1, arm=arm, order=order, steps=len(times),
                           step_median_seconds=statistics.median(times), step_sum_seconds=sum(times),
                           workload=workload)
                result['repeats'].append(row)
                (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps({k: v for k, v in row.items() if k != 'workload'}), flush=True)
        for arm in ['shared', 'original', 'ordinary']:
            start = time.perf_counter()
            with opened(arm) as client:
                row = {'setup_seconds': time.perf_counter() - start}
                rows = [common.checked_step(client, model, values) for values in cases]
                row.update(rows=rows, step_sum_seconds=sum(x['seconds'] for x in rows),
                           rss_after_workload_kib=common.memory_kib(client.process.pid))
            result['distinct'][arm] = row
            print(json.dumps({'distinct_arm': arm, 'setup_seconds': row['setup_seconds'],
                              'step_sum_seconds': row['step_sum_seconds']}), flush=True)
        result['status'] = 'passed'
    except Exception as error:
        result['error'] = str(error)
        result['status'] = 'failed'
        raise
    finally:
        (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error('Use 1..10 repeats')
    run(args.binary.resolve(), args.output, args.repeats)
