#!/usr/bin/env python3
"""Replay checked mathematics and bounded implementation correspondence.
The Python-to-Lean AST/index adapter is tested, not itself formally verified.
"""
import hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SRC=ROOT/'experiments/semantic_saturation/src'
OUT=HERE/'receipts'
BUILD=HERE/'.build'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def tup(x):return tuple(tup(y) for y in x) if isinstance(x,list) else x

def term(a,env):
    tag=a[0]
    if tag=='var':
        if a[1] not in env:raise ValueError('unbound '+a[1])
        return f'(.var {env.index(a[1])})'
    if tag=='zero':return '.zero'
    if tag=='one':return '.one'
    if tag=='not':return f'(.neg {term(a[1],env)})'
    x,y=term(a[1],env),term(a[2],env)
    if tag=='and':return f'(.meet {x} {y})'
    if tag=='or':return f'(.join {x} {y})'
    if tag=='xor':return f'(.join (.meet {x} (.neg {y})) (.meet (.neg {x}) {y}))'
    raise ValueError(tag)

def formula(a,env):
    tag=a[0]
    if tag=='T':return '(.eq .zero .zero)'
    if tag=='F':return '(.neg (.eq .zero .zero))'
    if tag=='eq0':return f'(.eq {term(a[1],env)} .zero)'
    if tag=='ne0':return f'(.neg (.eq {term(a[1],env)} .zero))'
    if tag=='notF':return f'(.neg {formula(a[1],env)})'
    if tag in ('andF','orF'):
        return f'(.{"conj" if tag=="andF" else "disj"} {formula(a[1],env)} {formula(a[2],env)})'
    if tag=='exists':return f'(.ex {formula(a[2],[a[1]]+env)})'
    raise ValueError(tag)

HEADER='''import Proofs
open SupportCells
set_option maxRecDepth 10000
set_option maxHeartbeats 0

-- Lean index 0 is the newest slot; Python slot 0 is the oldest slot.
def pythonCell {n : Nat} (v : Val n) : Nat :=
  (List.finRange n).foldl (fun a i => a + (v i).toNat * 2 ^ (n - 1 - i.val)) 0

def fromMask {n : Nat} (mask : Nat) : Val n → Bool :=
  fun v => mask.testBit (pythonCell v)

def asMask {n : Nat} (s : Val n → Bool) : Nat :=
  (allVal n).foldl (fun mask v => if s v then mask + 2 ^ pythonCell v else mask) 0

def resultLine {n : Nat} (id : String) (f : Formula n) : IO Unit :=
  IO.println (id ++ ":" ++ String.join
    ((List.range (2 ^ (2 ^ n) - 1)).map fun k => if f.eval (fromMask (k + 1)) then "1" else "0"))

def refinementLine (n mask : Nat) : IO Unit :=
  IO.println ("r" ++ toString n ++ ":" ++ toString mask ++ ":" ++ String.intercalate ","
    (((allSupport (n + 1)).filter (refinesB (fromMask mask))).map (fun s => toString (asMask s))))

'''

def bridge(fixtures):
    out=[HEADER]
    for f in fixtures:
        ast=formula(tup(f['ast']),list(reversed(f['free_variables'])))
        out.append(f'def {f["id"]} : Formula {len(f["free_variables"])} := {ast}\n')
    chunks=[]
    for start in range(0,len(fixtures),50):
        name=f'runChunk{start//50}';chunks.append(name)
        out.append(f'\ndef {name} : IO Unit := do\n')
        for f in fixtures[start:start+50]:out.append(f'  resultLine "{f["id"]}" {f["id"]}\n')
    out.append('\ndef main : IO Unit := do\n')
    for name in chunks:out.append(f'  {name}\n')
    out.append('  resultLine "m_order_correct" (.eq (.var 1) (.zero : Term 2))\n')
    out.append('  resultLine "m_order_mutant" (.eq (.var 0) (.zero : Term 2))\n')
    out.append('  resultLine "m_shadow_correct" (.ex (.neg (.eq (.var 0) (.zero : Term 2))))\n')
    out.append('  resultLine "m_shadow_mutant" (.ex (.neg (.eq (.var 1) (.zero : Term 2))))\n')
    for n in range(3):
        for mask in range(1,2**(2**n)):out.append(f'  refinementLine {n} {mask}\n')
    return ''.join(out)

def main():
    if sys.flags.optimize != 0:
        raise RuntimeError('Optimized Python disables control assertions; rerun without -O or PYTHONOPTIMIZE')
    OUT.mkdir(exist_ok=True);BUILD.mkdir(exist_ok=True)
    fixture=json.loads((HERE/'fixtures.json').read_text());rows=fixture['fixtures']
    generated=bridge(rows)
    gp=HERE/'Bridge.lean'
    if '--generate' in sys.argv:gp.write_text(generated)
    if not gp.exists() or gp.read_text()!=generated:raise RuntimeError('Bridge.lean does not match deterministic generation')
    lean=shutil.which('lean')
    if not lean:raise RuntimeError('Put the official pinned Lean 4.29.1 bin directory on PATH')
    version=subprocess.check_output([lean,'--version'],text=True).strip()
    if 'version 4.29.1,' not in version:raise RuntimeError('wrong Lean toolchain: '+version)
    t=time.monotonic()
    proof=subprocess.run([lean,'-o',str(BUILD/'Proofs.olean'),'Proofs.lean'],cwd=HERE,text=True,capture_output=True)
    (OUT/'lean-build.txt').write_text(proof.stdout+proof.stderr)
    if proof.returncode:raise RuntimeError('Lean proof build failed')
    source=(HERE/'Proofs.lean').read_text()
    # Comments and #print axioms are not declarations. Kernel dependency output is checked separately.
    stripped=re.sub(r'/\-.*?\-/','',source,flags=re.S)
    if re.search(r'\b(sorry|admit|unsafe|axiom)\b',stripped):raise RuntimeError('forbidden declaration/token')
    audits=re.findall(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",proof.stdout)
    allowed={'propext','Classical.choice','Quot.sound'}
    if len(audits)<15 or any(set(filter(None,(x.strip() for x in a.split(','))))-allowed for _,a in audits):
        raise RuntimeError('missing or unexpected foundational dependency audit')
    env=dict(os.environ,LEAN_PATH=str(BUILD))
    rejected={}
    for name,code in {
        'sort_mismatch':'import Proofs\nopen SupportCells\ndef wrong : Term 1 := Formula.eq (.var 0) .zero\n',
        'out_of_scope_index':'import Proofs\nopen SupportCells\ndef wrong : Term 1 := .var ⟨1, by decide⟩\n'
    }.items():
        path=BUILD/(name+'.lean');path.write_text(code)
        check=subprocess.run([lean,str(path)],cwd=HERE,text=True,capture_output=True,env=env)
        rejected[name]={'exit_code':check.returncode,'source':code,'diagnostic':check.stdout+check.stderr}
        if check.returncode==0:raise RuntimeError('invalid typed control was accepted: '+name)
    run=subprocess.run([lean,'--run','Bridge.lean'],cwd=HERE,text=True,capture_output=True,env=env)
    (OUT/'lean-correspondence.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Lean bridge failed')
    observed={}; refinements={}; mutants={}
    for line in run.stdout.splitlines():
        if line.startswith('f'):
            key,bits=line.split(':')
            if key in observed:raise RuntimeError('duplicate fixture output '+key)
            observed[key]=bits
        elif line.startswith('r'):
            n,mask,values=line[1:].split(':');key=(int(n),int(mask))
            if key in refinements:raise RuntimeError('duplicate refinement output '+str(key))
            refinements[key]=[int(v) for v in values.split(',') if v]
        elif line.startswith('m_'):
            key,bits=line.split(':')
            if key in mutants:raise RuntimeError('duplicate mutant output '+key)
            mutants[key]=bits
        elif line.strip():raise RuntimeError('unexpected Lean output '+line)
    oracle=load('bound_support_oracle',SRC/'support_oracle.py')
    parser=load('bound_normalized_parser',SRC/'normalized_parser.py')
    mismatch=[];observations=0;quantified=0
    for f in rows:
        r=oracle.evaluate_formula(tup(f['ast']),free_variables=f['free_variables'])
        if not r.complete:raise RuntimeError('oracle incomplete '+f['id']+': '+str(r.reason))
        expected=''.join('1' if o.value else '0' for o in r.observations)
        observations+=len(expected);quantified+=('exists' in json.dumps(f['ast']))
        if observed.get(f['id'])!=expected:mismatch.append(f['id'])
    if set(observed)!={f['id'] for f in rows}:raise RuntimeError('extra or missing fixture output')
    expected_refinement_keys={(n,mask) for n in range(3) for mask in range(1,2**(2**n))}
    if set(refinements)!=expected_refinement_keys:raise RuntimeError('extra or missing refinement output')
    expected_mutants={'m_order_correct','m_order_mutant','m_shadow_correct','m_shadow_mutant'}
    if set(mutants)!=expected_mutants:raise RuntimeError('extra or missing mutation-control output')
    assert mutants['m_order_correct']!=mutants['m_order_mutant']
    assert mutants['m_shadow_correct']!=mutants['m_shadow_mutant']
    refine_count=0
    for (n,mask),values in refinements.items():
        expected=list(oracle.refinement_supports(mask,n));refine_count+=len(expected)
        if len(values)!=len(set(values)) or sorted(values)!=sorted(expected):mismatch.append(f'refine:{n}:{mask}')
    for p in fixture['native_parser_receipts']:
        if p['returncode']!=0 or p['stderr']:raise RuntimeError('invalid inherited native receipt')
        actual=parser.parse_native_output(p['stdout'],p['free_variables'])
        if actual!=tup(p['candidate']):mismatch.append('parse:'+p['case'])
    # Additional semantic boundary controls in the canonical Python implementation.
    x=('var','x'); a=('var','a'); b=('var','b')
    end=oracle.evaluate_formula(('orF',('eq0',x),('eq0',('not',x))),free_variables=('x',))
    assert [o.value for o in end.observations]==[True,True,False]
    left=oracle.evaluate_formula(('eq0',a),free_variables=('a','b'))
    perm=oracle.evaluate_formula(('eq0',a),free_variables=('b','a'))
    assert [o.value for o in left.observations]!=[o.value for o in perm.observations]
    shadow=oracle.evaluate_formula(('exists','x',('ne0',x)),free_variables=('x',))
    unbound=oracle.evaluate_formula(('ne0',x),free_variables=('x',))
    assert [o.value for o in shadow.observations]!=[o.value for o in unbound.observations]
    assert mutants['m_order_correct']==''.join('1' if o.value else '0' for o in left.observations)
    assert mutants['m_shadow_correct']==''.join('1' if o.value else '0' for o in shadow.observations)
    # Execute a localized mutant that illegally forbids splitting one cell into both children.
    proper=('exists','x',('andF',('ne0',x),('ne0',('not',x))))
    real=oracle.evaluate_formula(proper,free_variables=())
    original_refinements=oracle.refinement_supports
    def no_both(mask,n):
        for r in original_refinements(mask,n):
            offset=1<<n;low=r&((1<<offset)-1);high=r>>offset
            if not (low&high):yield r
    try:
        oracle.refinement_supports=no_both
        mutated=oracle.evaluate_formula(proper,free_variables=())
    finally:
        oracle.refinement_supports=original_refinements
    assert real.complete and mutated.complete
    assert [o.value for o in real.observations]==[True]
    assert [o.value for o in mutated.observations]==[False]
    exact={'schema':'tau-support-proof-receipt/v1','status':'PASS' if not mismatch else 'FAIL',
           'lean_version':version,'replay_exit_code':0,'lake_build_executed_by_this_script':False,'separate_lake_build_receipt':'receipts/lake-build.txt','proof_replay':['lean','-o','.build/Proofs.olean','Proofs.lean'],
           'bridge_replay':['lean','--run','Bridge.lean'],'cwd':'proofs/lean/support_cells_v001',
           'fixture_count':len(rows),'quantified_fixture_count':quantified,'formula_support_observations':observations,
           'refinement_cases':len(refinements),'refinement_children_checked':refine_count,
           'inherited_native_parser_receipts':len(fixture['native_parser_receipts']),
           'mismatches':mismatch,'audited_declarations':{name:[x.strip() for x in axioms.split(',') if x.strip()] for name,axioms in audits},
           'semantic_negative_controls':['finite-two-element-vs-two-cell-support','ordered-free-interface','lexical-shadowing'],
           'executed_lean_translation_mutants':mutants,'rejected_typed_controls':rejected,
           'executed_python_refinement_mutant':{'mutation':'forbid both occupied children','correct':[o.value for o in real.observations],'mutated':[o.value for o in mutated.observations]},
           'duration_seconds':round(time.monotonic()-t,3),
           'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'Proofs.lean',HERE/'Bridge.lean',HERE/'fixtures.json',HERE/'replay.py',SRC/'support_oracle.py',SRC/'normalized_parser.py']},
           'nonclaims':['No machine proof of the Python-to-Lean adapter or Python implementation.',
                        'No general abstract Boolean-algebra representation theorem.',
                        'No current native Tau checker equivalence claim; parser receipts are inherited Mac execution.',
                        'No performance result; the executable Lean algorithm deliberately enumerates all child supports.']}
    (OUT/'correspondence.json').write_text(json.dumps(exact,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:exact[k] for k in ['status','fixture_count','formula_support_observations','refinement_cases','refinement_children_checked','mismatches','duration_seconds']},indent=2))
    if mismatch:raise SystemExit(1)
if __name__=='__main__':main()
