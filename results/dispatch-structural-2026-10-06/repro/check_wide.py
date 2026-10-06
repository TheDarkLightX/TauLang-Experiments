#!/usr/bin/env python3
"""Replay the report's 384-bit identifiers and keys on both loading paths."""
import argparse
import json
from pathlib import Path
import re
import sys

import measure
import tau_dispatch_blowup as reporter


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--unmodified', required=True)
    ap.add_argument('--patched', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    configs = {'unmodified': [str(Path(args.unmodified).resolve())],
               'patched': [str(Path(args.patched).resolve())],
               'split_off': [str(Path(args.unmodified).resolve()), '--bv-case-split', 'false']}
    record = {'schema': 'tau203-wide-checks/1', 'width': 384,
              'scope': 'Correctness and completion checks, one process per point and configuration; not a repeated timing estimate.',
              'binary_sha256': {k: measure.digest(v[0]) for k, v in configs.items()}, 'rows': []}
    for kind, size, route in [('terms', 12, 'spec'), ('chain', 12, 'spec'),
                              ('terms', 10, 'revision'), ('chain', 12, 'revision')]:
        wl = reporter.terms_workload(size, 384) if kind == 'terms' else reporter.chain_workload(size, 384, False)
        boot = wl.spec if route == 'spec' else reporter.ROUTER
        stdin = reporter.stdin_spec(wl) if route == 'spec' else reporter.stdin_router(wl)
        for name, command in configs.items():
            folder = args.out / f'{kind}-{size}-{route}-{name}'
            first_step = 0 if route == 'spec' else 2
            result = measure.run_one(command, boot, stdin, [c.expect for c in wl.checks], folder, 60, 1536, first_step)
            out = measure.ANSI.sub('', (folder / 'stdout.txt').read_text())
            actual_o1 = [(int(i), v) for i, v in re.findall(r'o1\[(\d+)\]\s*:=\s*(\S+)', out)]
            expected_o1 = [(i + first_step, c.values[1]) for i, c in enumerate(wl.checks)]
            # Revision startup can print earlier outputs; compare the checked steps.
            checked_o1 = [(i, v) for i, v in actual_o1 if i >= first_step]
            result['o1_ok'] = checked_o1 == expected_o1
            result['ok'] = result['ok'] and result['o1_ok']
            (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            record['rows'].append({'kind': kind, 'size': size, 'route': route, 'variant': name,
                                   'input_cases': len(wl.checks), 'result': result})
            record['ok'] = all(row['result']['ok'] for row in record['rows'])
            (args.out / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
            print(folder.name, 'PASS' if result['ok'] else 'FAIL', flush=True)
            if not result['ok']:
                return 1
    record['binary_sha256_after'] = {k: measure.digest(v[0]) for k, v in configs.items()}
    record['ok'] = record['ok'] and record['binary_sha256'] == record['binary_sha256_after']
    record['input_evaluations'] = sum(row['input_cases'] for row in record['rows'])
    (args.out / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
    return 0 if record['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
