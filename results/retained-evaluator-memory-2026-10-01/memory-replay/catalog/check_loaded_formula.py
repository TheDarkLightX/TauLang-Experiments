#!/usr/bin/env python3
"""Compare Tau's printed loaded formula for both VM source spellings."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'adapters'), str(ROOT / 'vm/tools')]
from native_tau_shared import SharedLookupTau
from native_tau_compact import CompactMemoryTau


class Capture:
    def _read_response(self, deadline=None):
        output, error = super()._read_response(deadline)
        if re.search(r'^%1:', output, re.M):
            self.loaded_response = output
        return output, error


class Shared(Capture, SharedLookupTau):
    pass


class Compact(Capture, CompactMemoryTau):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    source = (ROOT / 'vm/spec/vm.tau').read_text()
    texts = {}
    admissions = {}
    for arm, kind in [('shared', Shared), ('compact', Compact)]:
        with kind(args.binary.resolve(), source=source) as client:
            response = client.loaded_response
            formula = response[response.index('%1:'):]
            end = re.search(r'\n\[ %1 error \] tau> \s*$', formula)
            if not end:
                raise ValueError('Unexpected response framing')
            texts[arm] = formula[:end.start()].strip()
            admissions[arm] = client.admit_frame
            (args.output / (arm + '-loaded-formula.txt')).write_text(texts[arm] + '\n')
    result = {'loaded_formula_byte_equal': texts['shared'] == texts['compact'],
              'admission_equal': admissions['shared'] == admissions['compact'],
              'formula_sha256': {arm: hashlib.sha256(text.encode()).hexdigest() for arm, text in texts.items()},
              'formula_bytes': {arm: len(text.encode()) for arm, text in texts.items()},
              'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
              'scope': 'Exact printed loaded-formula comparison on the pinned executable; not a proof of all language behavior.'}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not all([result['loaded_formula_byte_equal'], result['admission_equal']]):
        raise ValueError('Loaded representations differ')


if __name__ == '__main__':
    main()
