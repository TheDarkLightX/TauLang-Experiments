#!/usr/bin/env python3
"""Check the two-bit example and two ordinary invalid input values."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error('Output directory must be new')
args.output.mkdir(parents=True)
commands = '\n'.join([
    'always o1[t]:bv[2] = (i1[t]:bv[2] + i2[t]:bv[2]).',
    'evalspec %1', 'evalspec %1 3 2', 'evalspec %1 0 0',
    'evalspec %1 1 2', 'evalspec %1 4 0', 'evalspec %1 03 0', 'q', '',
])
env = os.environ.copy()
env['TAU_CONCRETE_EVAL'] = '1'
env.pop('TAU_CONCRETE_EVAL_MAX_EXPRESSIONS', None)
run = subprocess.run([str(args.binary.resolve()), '--charvar', 'false', '-c', 'false'],
                     input=commands, text=True, capture_output=True,
                     timeout=30, env=env)
(args.output / 'commands.txt').write_text(commands)
(args.output / 'stdout.txt').write_text(run.stdout)
(args.output / 'stderr.txt').write_text(run.stderr)
frames = re.findall(r'evalspec-result: ([^\r\n]+)\r?\nevalspec-end', run.stdout)
expected = [r'status=admitted inputs=2 outputs=1 .*',
            r'status=ok leaf=0 outputs=1 o1\[t\]=1',
            r'status=ok leaf=0 outputs=1 o1\[t\]=0',
            r'status=ok leaf=0 outputs=1 o1\[t\]=3',
            r'status=error reason=bad_value', r'status=error reason=bad_value']
passed = len(frames) == len(expected) and all(
    re.fullmatch(pattern, frame) for pattern, frame in zip(expected, frames))
receipt = {'status': 'passed' if passed else 'failed', 'process_exit_code': run.returncode,
           'frames': frames, 'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest()}
(args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
raise SystemExit(0 if passed else 1)
