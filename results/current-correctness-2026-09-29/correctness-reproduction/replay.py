#!/usr/bin/env python3
"""Run the packaged small correctness checks against an explicit Tau binary."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import os

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('--output', type=Path, default=Path('replay-results.json'))
    args = p.parse_args()
    binary = args.binary.resolve(strict=True)
    cases = json.loads((Path(__file__).parent / 'cases.json').read_text())
    env = {k: v for k, v in os.environ.items() if not k.startswith('TAU_')}
    ansi = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
    records = []
    with args.output.open('x') as output:
        for case in cases:
            try:
                r = subprocess.run([str(binary), '--charvar', 'false', '-c', 'false', '-S', 'error'],
                                   input=case['input'], text=True, capture_output=True,
                                   env=env, timeout=15)
                stdout, stderr = ansi.sub('', r.stdout), ansi.sub('', r.stderr)
                verdicts = re.findall(r'^%\d+: ([TF])\s*$', stdout, re.M)
                ok = r.returncode == 0 and verdicts == [case['expected']] and '(Error)' not in stderr
                record = dict(case, returncode=r.returncode, stdout=stdout, stderr=stderr,
                              observed_verdicts=verdicts, matches_expected=ok)
            except subprocess.TimeoutExpired:
                record = dict(case, timed_out=True, matches_expected=False)
            records.append(record)
            print(f"{case['name']}: {'PASS' if record['matches_expected'] else 'FAIL'}")
        json.dump({'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                   'results': records}, output, indent=2)
        output.write('\n')
    return 0 if all(r['matches_expected'] for r in records) else 1

if __name__ == '__main__':
    sys.exit(main())
