#!/usr/bin/env python3
"""Generate real succinct receipts for native Tau traces and verify separately."""
import hashlib, json, os, subprocess, time
from pathlib import Path

root=Path(__file__).resolve().parent
out=root/'proof-results';out.mkdir(exist_ok=False)
env=os.environ.copy();env.update(RISC0_DEV_MODE='0',TAUFOLD_R0VM=str(root/'tools/risc0-3.0.6/r0vm'))
report={'status':'incomplete','proofs':[]}
def save(): (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
try:
    builds=json.loads((root/'checker-builds/receipt.json').read_text())
    assert builds['status']=='passed'
    for index,app in enumerate(['auction','payroll','inference']):
        witness=json.loads((root/'native-measured'/f'{app}-retained-1.witness.json').read_text())
        witness['salt']=list(os.urandom(32))
        witness_path=out/f'{app}.witness.json'
        with os.fdopen(os.open(witness_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
            json.dump(witness,f)
        program=root/'source/zkvm/examples'/f'{app}.json'
        claims=[]
        for variant in (['baseline','shared32'] if index%2==0 else ['shared32','baseline']):
            binary=root/'checker-builds'/variant/'taufold-proof'
            folder=out/f'{app}-{variant}';folder.mkdir()
            receipt=folder/'receipt.bin';claim=folder/'claim.json'
            start=time.perf_counter()
            p=subprocess.run([str(binary),'prove',str(program),str(witness_path),str(receipt),str(claim)],
                env=env,capture_output=True,text=True,timeout=1800)
            elapsed=time.perf_counter()-start
            (folder/'prove.stderr').write_text(p.stderr)
            (folder/'prove.stdout').write_text(p.stdout)
            p.check_returncode();result=json.loads(p.stdout)
            assert result['status']=='proved_and_verified' and result['receipt_kind']=='succinct'
            verification_env=env|{'TAUFOLD_R0VM':'/nonexistent/r0vm','TAU_BINARY':'/nonexistent/tau'}
            start=time.perf_counter()
            p=subprocess.run([str(binary),'verify',str(program),str(receipt),str(claim)],
                env=verification_env,capture_output=True,text=True,timeout=300)
            verify_elapsed=time.perf_counter()-start
            (folder/'verify.stderr').write_text(p.stderr)
            (folder/'verify.stdout').write_text(p.stdout)
            p.check_returncode();verified=json.loads(p.stdout)
            assert verified['status']=='verified'
            claims.append(json.loads(claim.read_text()))
            row={'app':app,'variant':variant,'prove_process_seconds':elapsed,
                 'verify_process_seconds':verify_elapsed,'result':result,'verification':verified,
                 'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
                 'claim_sha256':hashlib.sha256(claim.read_bytes()).hexdigest(),
                 'host_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
            report['proofs'].append(row);save();print(json.dumps(row),flush=True)
        assert claims[0]==claims[1], 'Public claim changed between checker versions'
    report['status']='passed'
except BaseException as error:
    report.update(status='failed',error=str(error));raise
finally:save()
