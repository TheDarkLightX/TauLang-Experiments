#!/usr/bin/env python3
"""Run the fixed, small arithmetic cases and retain every response."""
import argparse,hashlib,json,re,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FLAGS=['--charvar=false','--color=false','--highlighting=false','--benchmarks=false',
       '--status=false','-S','error','--preprocessing=false','--block-max-splits=0',
       '--bv-widening=false','--bv-quantifier-free-decision=false']
p=argparse.ArgumentParser();p.add_argument('--tau',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():raise SystemExit('Output exists')
binary=a.tau.resolve(strict=True)
cases=json.loads((ROOT/'exact-cases.json').read_text())
rows=[]
start=time.time()
with tempfile.TemporaryDirectory(prefix='tau-exact-') as wd:
 for case in cases:
  try:
   run=subprocess.run([str(binary),*FLAGS,'-e',case['command']],cwd=wd,input='',capture_output=True,text=True,timeout=12)
   r=dict(id=case['id'],returncode=run.returncode,stdout=run.stdout,stderr=run.stderr,timeout=False)
   r['passed']=run.returncode==0 and run.stderr=='' and re.fullmatch(r'%\d+:\s*'+case['expected']+r'\s*',run.stdout) is not None
  except subprocess.TimeoutExpired as e:
   r=dict(id=case['id'],returncode=None,stdout=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout or '',stderr=(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else e.stderr or '',timeout=True,passed=False)
  rows.append(r)
result=dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cases_sha256=hashlib.sha256((ROOT/'exact-cases.json').read_bytes()).hexdigest(),flags=FLAGS,checks=len(rows),passed=sum(x['passed'] for x in rows),failed=sum(not x['passed'] for x in rows),diagnostic_wall_seconds=time.time()-start,rows=rows)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
raise SystemExit(1 if result['failed'] else 0)
