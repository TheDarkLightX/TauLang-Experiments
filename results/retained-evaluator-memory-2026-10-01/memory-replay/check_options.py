#!/usr/bin/env python3
"""Check all 64 memory-option combinations against four arithmetic witnesses."""
import argparse,hashlib,json,os
from pathlib import Path
import platform,re,subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('binary',type=Path);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();binary=a.binary.resolve()
a.output.mkdir(parents=True,exist_ok=False)
keys=['TAU_EVAL_DECIMAL_ONLY','TAU_EVAL_TRANSIENT_NORMALIZE','TAU_EVAL_TRIM',
      'TAU_EVAL_ARENA_OUTPUTS','TAU_EVAL_FLAT_LEAVES','TAU_EVAL_RELEASE_PARSE_SCRATCH']
values=[0,127,128,255]
spec='always (i1[t]:bv[8] < {128}:bv[8] ? (o1[t]:bv[8] = (i1[t]:bv[8] + {1}:bv[8]) && o2[t]:bv[8] = (o1[t]:bv[8] + {7}:bv[8])) : (o1[t]:bv[8] = (i1[t]:bv[8] - {1}:bv[8]) && o2[t]:bv[8] = (o1[t]:bv[8] - {7}:bv[8]))).'
commands='\n'.join([spec,'evalspec %1']+['evalspec %1 '+str(v) for v in values]+['evalspec %1','q',''])
expected=[]
for v in values:
    first=(v+(1 if v<128 else -1))%256
    second=(first+(7 if v<128 else -7))%256
    expected.append({'o1[t]':str(first),'o2[t]':str(second)})
version=subprocess.check_output([str(binary),'--version'],text=True,timeout=15).strip()
data={'status':'incomplete','binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
      'version':version,'options':keys,'inputs':values,'expected':expected,'rows':[]}
try:
    for mask in range(64):
        env=os.environ.copy()
        for key in list(env):
            if key.startswith(('TAU_EVAL_','TAU_CONCRETE_','TAU_MEMORY_','TAU_ACYCLIC_')):
                env.pop(key)
        env.update({k:str((mask>>i)&1) for i,k in enumerate(keys)})
        env.update(TAU_CONCRETE_EVAL='1',TAU_MEMORY_TELEMETRY='1')
        result=subprocess.run([str(binary),'--charvar','false','--color','false','--benchmarks','false','--severity','error'],
                              env=env,input=commands,text=True,capture_output=True,timeout=30)
        frames=re.findall(r'^evalspec-result: (.+)$',result.stdout,re.M)
        parsed=[dict(x.split('=',1) for x in frame.split()) for frame in frames]
        if result.returncode or len(parsed)!=6 or parsed[0].get('status')!='admitted' or parsed[-1]!=parsed[0]:
            raise ValueError('Admission/return-code failure at option mask '+str(mask))
        for actual,want in zip(parsed[1:5],expected):
            if actual.get('status')!='ok' or actual.get('outputs')!='2' or any(actual.get(k)!=v for k,v in want.items()):
                raise ValueError('Arithmetic mismatch at option mask '+str(mask))
        counters=[json.loads(v) for v in re.findall(r'^tau-memory: (.+)$',result.stdout,re.M)]
        final=counters[-1]
        if final['parse_scratch_releases']!=int(env['TAU_EVAL_RELEASE_PARSE_SCRATCH']):
            raise ValueError('Cleanup count at option mask '+str(mask))
        trim=int(env['TAU_EVAL_TRIM']) if platform.libc_ver()[0]=='glibc' else 0
        if final['trim_calls']!=trim:
            raise ValueError('Trim count at option mask '+str(mask))
        data['rows'].append({'mask':mask,'frames':parsed,'counters':counters,'stdout':result.stdout,'stderr':result.stderr})
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=data['binary_sha256']:
        raise ValueError('Executable changed during test')
    data.update(status='passed',checks=256,processes=64)
except Exception as e:
    data.update(status='failed',error=str(e))
    raise
finally:
    (a.output/'results.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ['status','checks','processes','binary_sha256']}))
