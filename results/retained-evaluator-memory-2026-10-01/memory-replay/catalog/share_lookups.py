#!/usr/bin/env python3
"""Share repeated lookups in the pinned VM source using ordinary Tau definitions."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import re

VM_SHA256 = '6bd3f28e938038a363182d01c1371f2f4cfdd487677de2d474e3dc0a4496f4eb'


def transform(source):
    if hashlib.sha256(source.encode()).hexdigest() != VM_SHA256:
        raise ValueError('This transformation is checked only for the bundled VM source')
    prefix, original = source.split('always ', 1)
    body = original
    helpers = []
    for function in ['select32', 'select16']:
        calls = []
        for match in re.finditer(r'\b' + function + r'\(', body):
            start, end, depth = match.start(), match.end(), 1
            while depth:
                depth += (body[end] == '(') - (body[end] == ')')
                end += 1
            calls.append(body[start:end])
        for text, count in Counter(calls).items():
            if count < 2:
                continue
            name = 'vmsharedlookup' + str(len(helpers))
            if name in source:
                raise ValueError('Helper name already exists')
            call = name + '({0}:bv[32])'
            body = body.replace(text, call)
            helpers.append({'name': name, 'call': call, 'body': text, 'uses': count})
    # Reverse expansion checks the exact original text, including whitespace.
    restored = body
    for helper in reversed(helpers):
        restored = restored.replace(helper['call'], helper['body'])
    if restored != original:
        raise ValueError('Helper expansion did not restore the original body')
    if [helper['uses'] for helper in helpers] != [20, 45, 7]:
        raise ValueError('Unexpected lookup inventory')
    definitions = ''.join(h['name'] + '(unusedvalue):bv[32] := ' + h['body'] + '.\n'
                          for h in helpers)
    return prefix + definitions + 'always ' + body, helpers


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    source = (Path(__file__).resolve().parent / 'vm/spec/vm.tau').read_text()
    modified, helpers = transform(source)
    (args.output / 'vm-shared-lookups.tau').write_text(modified)
    (args.output / 'helpers.json').write_text(json.dumps(helpers, indent=2) + '\n')
    print(json.dumps({'original_bytes': len(source.encode()), 'shared_bytes': len(modified.encode()),
                      'original_sha256': VM_SHA256,
                      'shared_sha256': hashlib.sha256(modified.encode()).hexdigest(),
                      'exact_reverse_expansion': True}))
