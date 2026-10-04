"""Fresh native checks of development-only lexical/quantifier boundaries."""
from pathlib import Path
import argparse,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import engine as E,checked_registry as R,native_oracle as N
oracle=R.CheckedOracle(a.binary,a.out/'native',timeout=10)
v=lambda n:('var',n);eq=lambda x:('eq0',x);ne=lambda x:('ne0',x);nt=lambda x:('not',x);nf=lambda f:('notF',f);ex=lambda n,f:('exists',n,f);all_=lambda n,f:nf(ex(n,nf(f)));conj=lambda f,g:('andF',f,g)
x,y=v('x'),v('y');av=v('a')
cases=[
 ('closed_proper_split',(),ex('x',conj(ne(x),ne(nt(x)))),('T',)),
 ('free_shadow',('a',),conj(eq(av),ex('a',ne(av))),eq(av)),
 ('nested_shadow',(),ex('x',conj(eq(x),ex('x',ne(x)))),('T',)),
 ('forall_exists_same',(),all_('x',ex('y',eq(('xor',x,y)))),('T',)),
 ('universal_endpoint_false',(),all_('x',('orF',eq(x),eq(nt(x)))),('F',)),
 ('alpha_rename_binder',('a',),ex('x',conj(ne(x),eq(('and',x,nt(av))))),ex('y',conj(ne(y),eq(('and',y,nt(av)))))),
 ('term_xor_cancellation',('a','b'),('xor',('xor',av,v('b')),v('b')),av),
]
rows=[];fail=[]
for name,names,left,right in cases:
 ctx=E.Context(tuple((x,'tau') for x in names),V=names)
 r=R.check_emission(oracle,left,right,ctx,'audit:'+name);rows.append({'name':name,'left':left,'right':right,'context':names,'receipt':r})
 if r['status']!='ACCEPTED':fail.append(name)
ctx=E.Context((('a','tau'),),V=('a',));oneway=oracle.native.equivalent(eq(av),('T',),ctx,'audit:one-way');rows.append({'name':'one_way_native','receipt':{'status':oneway.status,'forward':oneway.forward,'reverse':oneway.reverse}})
if (oneway.forward['truth'],oneway.reverse['truth'],oneway.status)!=('T','F','DIFFERENT'):fail.append('one_way_native')
malformed=oracle.native.run('normalize all a : tau ((a & a) = )','audit:malformed-math');rows.append({'name':'malformed_native','receipt':malformed})
if N.exact_truth(malformed)!='UNKNOWN':fail.append('malformed_native')
summary=oracle.native.finish()
report={'status':'PASS' if not fail else 'FAIL','failures':fail,'development_cases':len(cases),'native_boundary_controls':2,'native_summary':summary,'rows':rows,'source_sha256':{f:hashlib.sha256((a.source/f).read_bytes()).hexdigest() for f in ('checked_registry.py','native_oracle.py','typed_parser.py','support_oracle.py')},'scope':'Independent development-only native validation; not experiment holdout, speedup evidence or native implementation proof.'};(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2));raise SystemExit(bool(fail))
