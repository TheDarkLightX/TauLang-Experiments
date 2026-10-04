"""Regression: simplify children of every equivalent class representative."""
from pathlib import Path
import argparse, hashlib, json, sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.source))
import engine as E,checked_registry as R,study_core as C,support_oracle as S
ctx=E.Context((('a','tau'),('b','tau')),V=('a','b'));x=('var','a');y=('var','b')
root=('and',('not',('not',x)),y);alt=('and',('or',x,('zero',)),y);target=('and',x,y)
pairs=(E.CheckedPair(root,alt,ctx.key),E.CheckedPair(('or',x,('zero',)),x,ctx.key))
equivs=[S.compare_terms(p.left,p.right,free_variables=ctx.V).equivalent for p in pairs]
assert all(equivs)
q,qr=R.recursive_quotient(root,ctx,pairs);g,gr=C.optimize(root,ctx,pairs,rewrites=False)
report={'status':'PASS' if C.objective(q,ctx)<=C.objective(target,ctx) else 'FAIL','issue':'Recursive baseline must not discard a class alternative before recursively simplifying its children.','context':ctx.terms,'root':root,'alternative':alt,'target':target,'all_pairs_support_equivalent':equivs,'pairs':[{'left':p.left,'right':p.right} for p in pairs],'recursive':{'output':q,'cost':C.emitted_cost(q,ctx),'receipt':qr},'egraph_no_rewrites':{'output':g,'cost':C.emitted_cost(g,ctx),'receipt':gr},'source_sha256':{f:hashlib.sha256((a.source/f).read_bytes()).hexdigest() for f in ('checked_registry.py','study_core.py')},'scope':'Comparator adequacy issue; returned outputs remain semantically sound. No native Tau execution used.'}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(report['status']!='PASS')
