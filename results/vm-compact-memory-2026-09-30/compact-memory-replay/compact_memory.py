#!/usr/bin/env python3
"""Use whole-record equality for unchanged memory in the bundled VM."""
from pathlib import Path
import argparse
import hashlib
import json
from share_lookups import transform as share_lookups


def transform(source):
    shared, _ = share_lookups(source)
    fields = '(' + ' && '.join(f'o1[t].memory.r{i} = i3[t].memory.r{i}' for i in range(16)) + ')'
    aggregate = '(o1[t].memory = i3[t].memory)'
    count = shared.count(fields)
    if count != 22 or aggregate in shared:
        raise ValueError('Unexpected memory equality inventory')
    compact = shared.replace(fields, aggregate)
    if compact.replace(aggregate, fields) != shared:
        raise ValueError('Expanding aggregate equality changed the source')
    return compact, {'aggregate_equalities': count,
                     'original_bytes': len(source.encode()),
                     'shared_bytes': len(shared.encode()),
                     'compact_bytes': len(compact.encode()),
                     'compact_sha256': hashlib.sha256(compact.encode()).hexdigest(),
                     'exact_field_expansion': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    source = (Path(__file__).resolve().parent / 'vm/spec/vm.tau').read_text()
    compact, info = transform(source)
    (args.output / 'vm-compact-memory.tau').write_text(compact)
    (args.output / 'transformation.json').write_text(json.dumps(info, indent=2) + '\n')
    print(json.dumps(info, indent=2))
