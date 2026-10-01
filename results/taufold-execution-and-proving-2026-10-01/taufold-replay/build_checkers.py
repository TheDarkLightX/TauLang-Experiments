#!/usr/bin/env python3
"""Build and test original and experimental proof guests sequentially."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
src=root/'source/zkvm'; compiler=src/'tools/compile_tau.py'; generated=src/'core/src/generated.rs'
original_compiler=compiler.read_bytes();original_generated=generated.read_bytes()
out=root/'checker-builds';out.mkdir(exist_ok=False)
environment=os.environ.copy();environment.update(TAUFOLD_R0VM=str(root/'tools/risc0-3.0.6/r0vm'),RISC0_DEV_MODE='0')
report={'status':'incomplete','variants':[]}
def save(): (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
try:
    for name in ['baseline','width32','shared128','shared32']:
        folder=out/name;folder.mkdir()
        if name=='baseline':
            compiler.write_bytes(original_compiler);generated.write_bytes(original_generated)
        else:
            shutil.copy2(root/'checker_codegen.py',src/'tools/checker_codegen.py')
            text=original_compiler.decode().replace('def generate(source: str) -> str:', 'def generate_reference(source: str) -> str:')
            addition='''\ndef generate(source: str) -> str:
    import checker_codegen
    import sys
    result, _ = checker_codegen.generate(source, sys.modules[__name__], narrow=NARROW, share=SHARE)
    return result
\n'''.replace('NARROW',str(name!='shared128')).replace('SHARE',str(name!='width32'))
            text=text.replace('\ndef main() -> None:',addition+'\ndef main() -> None:')
            compiler.write_text(text)
            generated.write_bytes((root/'checker-candidates'/f'{name}.rs').read_bytes())
        command=['cargo','+1.97.1','build','--locked','--release','--manifest-path',str(src/'Cargo.toml'),
                 '--target-dir',str(root/'build-baseline'),'-p','taufold-proof','-j','4']
        with (folder/'build.log').open('w') as log:
            r=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT);r.check_returncode()
        binary=folder/'taufold-proof';shutil.copy2(root/'build-baseline/release/taufold-proof',binary)
        identity=json.loads(subprocess.check_output([str(binary),'identity'],env=environment))
        row={'name':name,'identity':identity,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
             'generated_sha256':hashlib.sha256(generated.read_bytes()).hexdigest()}
        command[2]='test';command+=['-p','taufold-core','--','--include-ignored']
        with (folder/'tests.log').open('w') as log:
            r=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT)
            row['test_exit_code']=r.returncode
            report['variants'].append(row);save();r.check_returncode()
        for app in ['auction','payroll','inference']:
            command=[str(binary),'profile',str(src/'examples'/f'{app}.json'),
                     str(root/'native-measured'/f'{app}-retained-1.witness.json')]
            r=subprocess.run(command,env=environment,capture_output=True,text=True,timeout=300)
            (folder/(app+'-profile.stderr')).write_text(r.stderr);r.check_returncode()
            profile=json.loads(r.stdout);(folder/(app+'-profile.json')).write_text(json.dumps(profile,indent=2)+'\n')
        print(json.dumps(row),flush=True)
    report['status']='passed'
except BaseException as err:
    report.update(status='failed',error=str(err));raise
finally:
    compiler.write_bytes(original_compiler);generated.write_bytes(original_generated);save()
