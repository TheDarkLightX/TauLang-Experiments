#!/usr/bin/env python3
"""Compare source-generated Rust variants against frozen original-source outputs."""
import argparse, hashlib, json, random, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',type=Path,required=True)
p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();cat=a.catalog.resolve();sys.path[:0]=[str(cat),str(cat/'adapters'),str(cat/'vm/tools')]
import replay as common
from compile_tau import Parser,step
model=Parser((a.source/'spec/vm.tau').read_text()).parse()
vectors=json.loads((cat/'inputs/conformance-cases.json').read_text())['inputs']
vectors+=json.loads((cat/'inputs/distinct-cases.json').read_text())['inputs']
randomizer=random.Random(1991001)
edge=[0,1,15,16,31,32,127,128,255,256,2**31-1,2**31,2**32-2,2**32-1]
# Target every opcode and boundary state, keeping the initial guard reachable.
for opcode in range(20):
 for index in range(70):
  v=[randomizer.getrandbits(32) for _ in range(102)]
  pc=randomizer.randrange(32);v[64]=32;v[81]=16;v[100]=randomizer.randrange(17);v[83]=pc;v[101]=0
  v[2*pc]=opcode;v[2*pc+1]=edge[index%len(edge)]
  v[82]=edge[(index//len(edge))%len(edge)] if index<56 else randomizer.getrandbits(32)
  vectors.append(v)
for _ in range(100):vectors.append([randomizer.getrandbits(32) for _ in range(102)])
apps=['auction','payroll','inference','guard','counterexample','controller','matching']
for app in apps:
 program=json.loads((a.source/'examples'/f'{app}.json').read_text())
 private=json.loads((a.source/'examples'/f'{app}.input.json').read_text())
 state=common.ordinary.initial_state()
 for _ in range(512):
  values=common.ordinary.inputs_for(program,private,state);vectors.append(list(values))
  state=common.ordinary.state_from(step(model,values))
  if state['halted']:break
 else:raise ValueError('Example failed to halt')
expected=[list(step(model,tuple(v))) for v in vectors]
a.output.mkdir(exist_ok=False,parents=True)
(a.output/'vectors.json').write_text(json.dumps({'inputs':vectors,'outputs':expected})+'\n')
code='#![allow(dead_code,unused_parens)]\n'
for name in ['baseline','width32','shared128','shared32']:
 code+=f'mod {name} {{include!("../checker-candidates/{name}.rs");}}\n'
code+='fn main() {\n'
code+='let cases: &[([u128;102],[u128;21])] = &[\n'
code+='\n'.join('('+repr(v)+','+repr(out)+'),' for v,out in zip(vectors,expected))+'\n];\n'
code+='for (index,(input,expected)) in cases.iter().enumerate() {\n'
for name in ['baseline','width32','shared128','shared32']:
 code+=f'assert_eq!({name}::tau_step(input),*expected,"{name} at {{}}",index);\n'
code+='}\nprintln!("checked {} vectors across four Rust variants",cases.len());\n}\n'
(a.output/'check.rs').write_text(code)
cmd=['rustc','+1.97.1','-O',str(a.output/'check.rs'),'-o',str(a.output/'check')]
r=subprocess.run(cmd,capture_output=True,text=True);(a.output/'build.log').write_text(r.stdout+r.stderr);r.check_returncode()
r=subprocess.run([str(a.output/'check')],capture_output=True,text=True);r.check_returncode()
report={'status':'passed','vectors':len(vectors),'variant_comparisons':4*len(vectors),
 'seed':1991001,'scope':'Host-native correctness checks, not guest cycles or proof timing.',
 'stdout':r.stdout,'sources':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in Path('checker-candidates').glob('*.rs')}}
(a.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
