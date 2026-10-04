"""Independent candidate-domination/property checks for ByteEGraph."""
from pathlib import Path
import argparse,hashlib,json,random,sys,time
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.source));import engine as E, study_core as C,support_oracle as S
sys.path.insert(0,str(Path(__file__).parent));from audit_math_harness import gen_formula, ref_formula, from_mask
rng=random.Random(62570081);ctx=E.Context((('a','tau'),),V=('a',));groups={};failures=[];count=0
for _ in range(400):
 f=gen_formula(rng,('a',),4,1);key=tuple(ref_formula(f,('a',),from_mask(m,1)) for m in (1,2,3));groups.setdefault(key,[]).append(f)
for group in groups.values():
 for i in range(0,len(group),8):
  roots=group[i:i+8]
  if len(roots)<2:continue
  original=roots[0];pairs=tuple(E.CheckedPair(original,r,ctx.key) for r in roots[1:]);low=min(C.objective(r,ctx) for r in roots)
  for rewrites in (False,True):
   output,report=C.optimize(original,ctx,pairs,iterations=2,node_limit=2000,rewrites=rewrites);count+=1
   if C.objective(output,ctx)>low:failures.append({'kind':'candidate_domination','roots':roots,'output':output,'report':report,'expected_max_objective':low,'actual_objective':C.objective(output,ctx)})
   for m in (1,2,3):
    if ref_formula(original,('a',),from_mask(m,1))!=ref_formula(output,('a',),from_mask(m,1)):failures.append({'kind':'semantic_change','original':original,'output':output,'mask':m})
report={'status':'PASS' if not failures else 'FAIL','seed':62570081,'formula_count':400,'semantic_groups':len(groups),'extraction_runs':count,'failures':failures,'source_sha256':{x:hashlib.sha256((a.source/x).read_bytes()).hexdigest() for x in ('study_core.py','engine.py','native_oracle.py')},'limitations':['Finite one-free-variable tests, not extraction optimality proof.','Semantic pair evidence is independent reference evaluation for this local test, not native Tau.','No claim that egraph strictly improves upon recursive quotienting.']};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
