#!/usr/bin/env python3
"""Check decision entry points and retained temporal interval behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
p=argparse.ArgumentParser()
p.add_argument('binary',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
cases=[
 ('zero_point_can_be_included','sat ex x:qlt (({0}:qlt & x) != 0).','T'),
 ('zero_point_can_be_excluded','sat ex x:qlt (({0}:qlt & x) = 0).','T'),
 ('zero_point_not_always_included','valid all x:qlt (({0}:qlt & x) != 0).','F'),
 ('zero_point_not_always_excluded','valid all x:qlt (({0}:qlt & x) = 0).','F'),
 ('sat_singleton_split','sat ex x:qlt (({3}:qlt & x) != 0 && ({3}:qlt & x\') != 0).','F'),
 ('valid_singleton_partition','valid all x:qlt (({3}:qlt & x) = 0 || ({3}:qlt & x\') = 0).','T'),
 ('temporal_interval_equality','realizable F (o1[t]:qlt = {(0,1)}:qlt).','T'),
 ('temporal_interval_membership','realizable F ((o1[t]:qlt & {(0,1)}:qlt) != 0).','T'),
 ('temporal_singleton_equality','realizable F (o1[t]:qlt = {0}:qlt).','T'),
 ('temporal_recurring_interval','realizable G (F (o1[t]:qlt = {(0,1)}:qlt)).','T')]
results=[]
for name,command,expected in cases:
 r=subprocess.run([str(a.binary.resolve()),'--charvar','false','-c','false','-S','error','-q'],input=command+'\n',text=True,capture_output=True,timeout=60)
 answers=re.findall(r'^%\d+: (.*)$',r.stdout,re.M)
 results.append({'name':name,'command':command,'expected':expected,'answers':answers,'returncode':r.returncode,'passed':r.returncode==0 and answers==[expected],'stdout':r.stdout,'stderr':r.stderr})
report={'binary_sha256':hashlib.sha256(a.binary.read_bytes()).hexdigest(),'total':len(results),'passed':sum(c['passed'] for c in results),'cases':results}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
raise SystemExit(0 if report['passed']==len(results) else 1)
