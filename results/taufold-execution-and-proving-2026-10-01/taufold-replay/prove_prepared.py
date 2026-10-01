#!/usr/bin/env python3
"""Prove the same native traces with the prepared checker and compare claims."""
import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'prepared-proofs';out.mkdir(exist_ok=False)
env=os.environ.copy();env.update(RISC0_DEV_MODE='0',TAUFOLD_R0VM=str(root/'tools/risc0-3.0.6/r0vm'))
report={'status':'incomplete','proofs':[]}
def save():(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
try:
    assert json.loads((root/'prepared-checker/receipt.json').read_text())['status']=='passed'
    for app in ['auction','payroll','inference']:
        folder=out/app;folder.mkdir()
        binary=root/'prepared-checker/taufold-proof'
        program=root/'source/zkvm/examples'/f'{app}.json'
        witness=root/'proof-results'/f'{app}.witness.json'
        receipt=folder/'receipt.bin';claim=folder/'claim.json'
        start=time.perf_counter()
        p=subprocess.run([str(binary),'prove',str(program),str(witness),str(receipt),str(claim)],env=env,capture_output=True,text=True,timeout=1800)
        elapsed=time.perf_counter()-start
        (folder/'prove.stderr').write_text(p.stderr);(folder/'prove.stdout').write_text(p.stdout)
        p.check_returncode();result=json.loads(p.stdout)
        assert result['status']=='proved_and_verified'
        assert claim.read_bytes()==(root/'proof-results'/f'{app}-baseline/claim.json').read_bytes()
        verification_env=env|{'TAUFOLD_R0VM':'/nonexistent/r0vm','TAU_BINARY':'/nonexistent/tau'}
        start=time.perf_counter()
        command=[str(binary),'verify',str(program),str(receipt),str(claim)]
        p=subprocess.run(command,env=verification_env,capture_output=True,text=True,timeout=300)
        verify_elapsed=time.perf_counter()-start
        (folder/'verify.stderr').write_text(p.stderr);(folder/'verify.stdout').write_text(p.stdout)
        p.check_returncode();verified=json.loads(p.stdout);assert verified['status']=='verified'
        command[0]=str(root/'checker-builds/baseline/taufold-proof')
        wrong=subprocess.run(command,env=verification_env,capture_output=True,text=True,timeout=300)
        assert wrong.returncode!=0,'Original image accepted new image receipt'
        (folder/'wrong-image.stderr').write_text(wrong.stderr)
        row={'app':app,'variant':'prepared32','prove_process_seconds':elapsed,'verify_process_seconds':verify_elapsed,
             'result':result,'verification':verified,'wrong_image_rejected':True,
             'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
             'claim_sha256':hashlib.sha256(claim.read_bytes()).hexdigest(),
             'host_sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}
        report['proofs'].append(row);save();print(json.dumps(row),flush=True)
    report['status']='passed'
except BaseException as error:report.update(status='failed',error=str(error));raise
finally:save()
