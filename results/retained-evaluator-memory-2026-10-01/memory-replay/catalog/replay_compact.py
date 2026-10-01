#!/usr/bin/env python3
"""Compare shared-lookup and compact-memory VM sources on one Tau binary."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'adapters'), str(ROOT / 'vm/tools')]
import replay as common
from native_tau_shared import SharedLookupTau
from native_tau_compact import CompactMemoryTau
from compact_memory import transform

SHAPE = {'status': 'admitted', 'inputs': '102', 'outputs': '21', 'decisions': '22',
         'leaves': '17', 'expressions': '60940', 'retained_terms': '455', 'budget': '1048576'}


def run(binary, output, repeats):
    output.mkdir(exist_ok=False)
    source = (ROOT / 'vm/spec/vm.tau').read_text()
    compact, info = transform(source)
    (output / 'vm-compact-memory.tau').write_text(compact)
    model = common.Parser(source).parse()
    vectors = common.read('conformance-cases.json')['inputs']
    distinct = common.read('distinct-cases.json')['inputs']
    programs = common.read('programs.json')
    version = subprocess.check_output([str(binary), '--version'], text=True, timeout=15)
    if not common.ordinary.matches_pinned_version(version):
        raise ValueError('Build the pinned evaluator revision')
    data = {'status': 'incomplete', 'version': version.strip(), 'platform': platform.platform(),
            'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'original_vm_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'transformation': info, 'repeats': [], 'distinct': {},
            'scope': 'Alternating 55-transition runs; one 256-input run per source. RSS samples are not lifetime peaks.'}

    def opened(arm):
        return {'shared': SharedLookupTau, 'compact': CompactMemoryTau}[arm](binary, source=source)

    def setup(client, elapsed):
        if client.admit_frame != SHAPE:
            raise ValueError('Admitted expression counts changed')
        return {'setup_seconds': elapsed, 'load_seconds': client.load_seconds,
                'admission_seconds': client.admit_seconds, 'admission': client.admit_frame,
                'rss_after_load_kib': client.rss_after_load_kib,
                'rss_after_admission_kib': client.rss_after_admit_kib}

    try:
        for index in range(repeats):
            order = ['shared', 'compact'] if index % 2 == 0 else ['compact', 'shared']
            for arm in order:
                begin = time.perf_counter()
                with opened(arm) as client:
                    row = setup(client, time.perf_counter() - begin)
                    workload = {'smoke': common.trace(client, model, programs['smoke'], [], 3),
                                'payroll': common.trace(client, model, programs['payroll'], [10], 17),
                                'conformance': [common.checked_step(client, model, v) for v in vectors]}
                    row['rss_after_workload_kib'] = common.memory_kib(client.process.pid)
                times = [v['seconds'] for group in workload.values() for v in group]
                row.update(repeat=index + 1, arm=arm, order=order, steps=len(times), workload=workload,
                           step_median_seconds=statistics.median(times), step_sum_seconds=sum(times))
                data['repeats'].append(row)
                (output / 'results.json').write_text(json.dumps(data, indent=2) + '\n')
                print(json.dumps({k: v for k, v in row.items() if k != 'workload'}), flush=True)
        for arm in ['compact', 'shared']:
            begin = time.perf_counter()
            with opened(arm) as client:
                row = setup(client, time.perf_counter() - begin)
                rows = [common.checked_step(client, model, v) for v in distinct]
                row.update(rows=rows, step_sum_seconds=sum(x['seconds'] for x in rows),
                           rss_after_workload_kib=common.memory_kib(client.process.pid))
            data['distinct'][arm] = row
        data['status'] = 'passed'
    except Exception as error:
        data.update(status='failed', error=str(error))
        raise
    finally:
        (output / 'results.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'status': data['status'], 'checks_per_arm': 55 * repeats + len(distinct)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error('Use 1..10 repeats')
    run(args.binary.resolve(), args.output, args.repeats)
