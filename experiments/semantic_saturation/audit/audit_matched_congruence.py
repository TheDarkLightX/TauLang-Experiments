"""Compare byte extraction on identical sound, fixed checked-pair graphs.
No actual native gates: equations are independently validated here to isolate
congruence-composition mechanics. No algebraic rewrite saturation is run.
"""
from pathlib import Path
import argparse,hashlib,json,random,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.source));import engine as E,study_core as C,checked_registry as R,support_oracle as S
sys.path.insert(0,str(Path(__file__).parent));from audit_math_harness import gen_term,ref_term,universe
rng=random.Random(99843072);ctx=E.Context((('a','tau'),('b','tau')),V=('a','b'));groups={};pool=[]
for _ in range(180):
 t=gen_term(rng,ctx.V,3)
 for f in (t,('not',('not',t)),('or',t,('zero',)),('and',t,('one',))):
  if f in pool:continue
  pool.append(f);k=tuple(ref_term(f,ctx.V,v) for v in universe(2));groups.setdefault(k,[]).append(f)
equiv=[g for g in groups.values() if len(g)>1];failures=[];runs=0
for _ in range(120):
 root=rng.choice(pool);pairs=[]
 for j in range(20):
  g=rng.choice(equiv);left,right=rng.sample(g,2);pairs.append(E.CheckedPair(left,right,ctx.key))
 q,qr=R.recursive_quotient(root,ctx,pairs);g,gr=C.optimize(root,ctx,pairs,rewrites=False,node_limit=10000);runs+=1
 if C.emitted_cost(q,ctx)!=C.emitted_cost(g,ctx):
  failures.append({'kind':'byte_gap','root':root,'pairs':[{'left':p.left,'right':p.right} for p in pairs],'recursive':q,'recursive_cost':C.emitted_cost(q,ctx),'egraph':g,'egraph_cost':C.emitted_cost(g,ctx),'recursive_receipt':qr,'egraph_receipt':gr})
 for out in (q,g):
  if any(ref_term(root,ctx.V,v)!=ref_term(out,ctx.V,v) for v in universe(2)):
   failures.append({'kind':'semantic_change','root':root,'output':out})
# Exact binder/commutative-congruence counterexample; pair is globally sound.
x=('var','x');v=('var','a');root=('exists','x',('eq0',('and',v,x)));alt=('exists','x',('eq0',('and',x,v)));pairs=(E.CheckedPair(alt,('T',),ctx.key),)
assert S.compare_formulas(alt,('T',),free_variables=ctx.V).equivalent
q,qr=R.recursive_quotient(root,ctx,pairs);g,gr=C.optimize(root,ctx,pairs,rewrites=False,node_limit=10000);runs+=1
if C.emitted_cost(q,ctx)!=C.emitted_cost(g,ctx):failures.append({'kind':'binder_byte_gap','root':root,'pairs':[{'left':p.left,'right':p.right} for p in pairs],'recursive':q,'recursive_cost':C.emitted_cost(q,ctx),'egraph':g,'egraph_cost':C.emitted_cost(g,ctx)})
report={'status':'PASS' if not failures else 'FAIL','seed':99843072,'term_pool_size':len(pool),'graph_runs':runs,'failure_count':len(failures),'failures':failures,'source_sha256':{f:hashlib.sha256((a.source/f).read_bytes()).hexdigest() for f in ('checked_registry.py','study_core.py','engine.py')},'limitations':['Finite sampled pair graphs and one targeted binder graph; not an equivalence proof of mechanisms.','Exact fixture equations independently interpreted, no native Tau called.']};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='failures'},indent=2));raise SystemExit(bool(failures))
