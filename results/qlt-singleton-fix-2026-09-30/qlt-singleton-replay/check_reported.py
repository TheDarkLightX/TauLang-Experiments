#!/usr/bin/env python3
"""Replay #197, including its ground and interval controls."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('binary', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
source = Path(__file__).with_name('reported-checks.tau').read_text()
run = subprocess.run([str(args.binary.resolve()), '--charvar', 'false', '-c', 'false', '-S', 'error', '-q'],
                     input=source, text=True, capture_output=True, timeout=60)
expected = ['F', 'T', 'F', 'F', 'T', 'T']
actual = re.findall(r'^%\d+: (.*)$', run.stdout, re.M)
report = {'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
          'expected': expected, 'actual': actual, 'returncode': run.returncode,
          'passed': run.returncode == 0 and actual == expected}
args.output.mkdir(parents=True, exist_ok=True)
(args.output/'stdout.txt').write_text(run.stdout)
(args.output/'stderr.txt').write_text(run.stderr)
(args.output/'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
