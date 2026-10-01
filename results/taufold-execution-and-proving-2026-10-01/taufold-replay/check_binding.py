#!/usr/bin/env python3
"""Check fixed-input preparation on seven programs and boundary states."""
import argparse, ast, hashlib, json, os, re, sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
for field in ['catalog','source','candidate','output']:
    p.add_argument('--'+field,type=Path,required=True)
a=p.parse_args();cat=a.catalog.resolve()
sys.dont_write_bytecode=True
sys.path[:0]=[str(cat),str(cat/'adapters'),str(cat/'vm/tools')]
import replay as common
import native_tau_eval as retained
from native_tau_compact import CompactMemoryTau
from compile_tau import Parser,step,INPUT_PATHS
common.ordinary.TAU_COMMIT=retained.nt.TAU_COMMIT='a739b90259729590dee7b424df05ba65bfdeacf2'
os.environ.update({name:'1' for name in ['TAU_CONCRETE_EVAL','TAU_EVAL_DECIMAL_ONLY',
    'TAU_EVAL_TRANSIENT_NORMALIZE','TAU_EVAL_TRIM','TAU_EVAL_ARENA_OUTPUTS',
    'TAU_EVAL_FLAT_LEAVES','TAU_EVAL_RELEASE_PARSE_SCRATCH']})
os.environ['TAU_MEMORY_TELEMETRY']='0'
# Test the exact class used in measurement, without executing that measurement.
measured=Path(__file__).with_name('native_experiments.py').read_text()
node=next(n for n in ast.parse(measured).body if isinstance(n,ast.ClassDef) and n.name=='BoundTau')
exec(compile(ast.Module(body=[node],type_ignores=[]),'native_experiments.py','exec'))
source=(a.source/'spec/vm.tau').read_text();model=Parser(source).parse()
a.output.mkdir(exist_ok=False,parents=True)
report={'status':'incomplete','rows':[],
    'measured_script_sha256':hashlib.sha256(measured.encode()).hexdigest(),
    'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest()}
def save():(a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
try:
    for app in ['auction','payroll','inference','guard','counterexample','controller','matching']:
        program=json.loads((a.source/'examples'/f'{app}.json').read_text())
        private=json.loads((a.source/'examples'/f'{app}.input.json').read_text())
        initial=common.ordinary.initial_state()
        original=list(common.ordinary.inputs_for(program,private,initial))
        for count in [65,82]:
            row={'app':app,'bound_inputs':count,'transitions':0,'boundary_checks':[],'changed_fixed_values_rejected':0}
            with BoundTau(a.candidate,source,original,count) as client:
                state=initial
                for _ in range(512):
                    v=common.ordinary.inputs_for(program,private,state)
                    got=client.step(v);wanted=step(model,v)
                    assert tuple(got)==tuple(wanted)
                    state=common.ordinary.state_from(got);row['transitions']+=1
                    if state['halted']:break
                else:raise AssertionError('Program did not halt')
                row['final_state']=state
                for field in [82,83,84,99,100,101]:
                    for value in [0,1,16,32,4294967295]:
                        v=original.copy();v[field]=value
                        got=client.step(v);assert tuple(got)==tuple(step(model,v))
                        row['boundary_checks'].append({'field':field,'value':value,'outputs':list(got)})
                for field in [0,64]+([65,81] if count==82 else []):
                    v=original.copy();v[field]^=1
                    try:client.step(v)
                    except ValueError as error:assert 'Fixed values changed' in str(error)
                    else:raise AssertionError('Changed fixed input accepted')
                    row['changed_fixed_values_rejected']+=1
                if count==65:
                    v=original.copy();v[65]^=1
                    assert tuple(client.step(v))==tuple(step(model,v))
                    row['dynamic_private_input_check']=True
            report['rows'].append(row);save()
            print(json.dumps({k:v for k,v in row.items() if k not in ['boundary_checks','final_state']}),flush=True)
    report['status']='passed'
except BaseException as error:report.update(status='failed',error=str(error));raise
finally:save()
