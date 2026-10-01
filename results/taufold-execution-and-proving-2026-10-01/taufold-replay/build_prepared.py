#!/usr/bin/env python3
"""Build the prepared 32-bit trace checker in an isolated source checkout."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
import checker_codegen,word_checker_codegen
root=Path(__file__).resolve().parent;src=root/'source/zkvm'
out=root/'prepared-checker';out.mkdir(exist_ok=False)
paths=[src/'tools/compile_tau.py',src/'core/src/generated.rs',src/'core/src/lib.rs']
original={p:p.read_bytes() for p in paths}
env=os.environ.copy();env.update(TAUFOLD_R0VM=str(root/'tools/risc0-3.0.6/r0vm'),RISC0_DEV_MODE='0')
report={'status':'incomplete'}
try:
    reference=checker_codegen.load(paths[0]);source=(src/'spec/vm.tau').read_text()
    generated,_=word_checker_codegen.generate(source,reference)
    paths[1].write_text(generated);(out/'generated.rs').write_text(generated)
    for name in ['checker_codegen.py','word_checker_codegen.py']:
        shutil.copy2(root/name,src/'tools'/name)
    compiler=original[paths[0]].decode().replace('def generate(source: str) -> str:','def generate_reference(source: str) -> str:')
    compiler=compiler.replace('\ndef main() -> None:', '''
def generate(source: str) -> str:
    import word_checker_codegen, sys
    return word_checker_codegen.generate(source, sys.modules[__name__])[0]

def main() -> None:''')
    paths[0].write_text(compiler)
    lib=original[paths[2]].decode()
    old='''    for pair in witness.trace.windows(2) {
        let expected = step(program, &witness.private_input, &pair[0])?;
        if expected != pair[1] {
            return Err(Reject::Transition);
        }
    }'''
    new='''    // Program and private words were validated above and stay fixed in this trace.
    let mut fields = [0u32; INPUT_FIELDS];
    for (index, word) in program.instructions.iter().enumerate() {
        fields[index * 2] = word[0];
        fields[index * 2 + 1] = word[1];
    }
    fields[64] = program.instructions.len() as u32;
    fields[65..65 + witness.private_input.len()].copy_from_slice(&witness.private_input);
    fields[81] = witness.private_input.len() as u32;
    for pair in witness.trace.windows(2) {
        let previous = &pair[0];
        if previous.halted != 0 {
            return Err(Reject::AfterHalt);
        }
        if previous.input_cursor as usize > witness.private_input.len() {
            return Err(Reject::State);
        }
        fields[82] = previous.accumulator;
        fields[83] = previous.pc;
        fields[84..100].copy_from_slice(&previous.memory);
        fields[100] = previous.input_cursor;
        fields[101] = previous.halted;
        let outputs = generated::tau_step32(&fields);
        if outputs[20] != 0 {
            return Err(Reject::Fault);
        }
        if outputs[19] > 1 {
            return Err(Reject::State);
        }
        let actual = &pair[1];
        if outputs[0] != actual.accumulator || outputs[1] != actual.pc
            || outputs[2..18] != actual.memory
            || outputs[18] != actual.input_cursor || outputs[19] != actual.halted {
            return Err(Reject::Transition);
        }
    }'''
    assert lib.count(old)==1
    reference_function=lib[lib.index('pub fn check_trace('):lib.index('\n#[cfg(test)]')].replace('pub fn check_trace(','fn check_trace_reference(',1)
    lib=lib.replace(old,new)
    tests='''
#[cfg(test)]
mod prepared_tests {
    use super::*;
REFERENCE
    #[test]
    fn prepared_trace_matches_reference_for_words_and_changed_states() {
        let mut checked = 0;
        for value in [0u32,1,15,16,31,32,255,256,65535,65536,0x7fffffff,0x80000000,u32::MAX] {
            let program = Program { version:VERSION, public_memory:vec![0,15],
                instructions:vec![[9,0],[6,15],[2,1],[10,15],[11,15],[6,0],[0,0]] };
            let mut witness = Witness { private_input:vec![value], salt:[42;32], trace:vec![State::default()] };
            while witness.trace.last().unwrap().halted == 0 {
                witness.trace.push(step(&program,&witness.private_input,witness.trace.last().unwrap()).unwrap());
            }
            assert_eq!(check_trace(&program,&witness),check_trace_reference(&program,&witness));
            checked += 1;
            for index in 0..witness.trace.len() {
                for field in 0..20 {
                    for delta in [1u32,16,u32::MAX] {
                        let mut changed = witness.clone();
                        let state = &mut changed.trace[index];
                        match field {
                            0=>state.accumulator ^= delta,
                            1=>state.pc ^= delta,
                            2..=17=>state.memory[field-2] ^= delta,
                            18=>state.input_cursor ^= delta,
                            _=>state.halted ^= delta,
                        }
                        assert_eq!(check_trace(&program,&changed),check_trace_reference(&program,&changed));
                        checked += 1;
                    }
                }
            }
            for length in 0..witness.trace.len() {
                let mut changed = witness.clone();changed.trace.truncate(length);
                assert_eq!(check_trace(&program,&changed),check_trace_reference(&program,&changed));
                checked += 1;
            }
        }
        println!("prepared/reference trace checks: {}",checked);
    }
}
'''.replace('REFERENCE',reference_function)
    paths[2].write_text(lib+tests)
    import difflib
    patch=''
    for p in paths[:1]+paths[2:]:
        rel=p.relative_to(src.parent)
        patch+=''.join(difflib.unified_diff(original[p].decode().splitlines(True),p.read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
    (out/'prepared-trace.patch').write_text(patch)
    cmd=['cargo','+1.97.1','build','--locked','--release','--manifest-path',str(src/'Cargo.toml'),
         '--target-dir',str(root/'build-baseline'),'-p','taufold-proof','-j','4']
    with (out/'build.log').open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    binary=out/'taufold-proof';shutil.copy2(root/'build-baseline/release/taufold-proof',binary)
    report.update(identity=json.loads(subprocess.check_output([str(binary),'identity'],env=env)),
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),generated_sha256=hashlib.sha256(generated.encode()).hexdigest())
    cmd[2]='test';cmd+=['-p','taufold-core','--','--include-ignored','--nocapture']
    with (out/'tests.log').open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    for app in ['auction','payroll','inference']:
        p=subprocess.run([str(binary),'profile',str(src/'examples'/f'{app}.json'),str(root/'native-measured'/f'{app}-retained-1.witness.json')],env=env,capture_output=True,text=True,timeout=300)
        (out/f'{app}-profile.stderr').write_text(p.stderr);p.check_returncode()
        (out/f'{app}-profile.json').write_text(json.dumps(json.loads(p.stdout),indent=2)+'\n')
    report['status']='passed'
except BaseException as error:report.update(status='failed',error=str(error));raise
finally:
    for p,data in original.items():p.write_bytes(data)
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
