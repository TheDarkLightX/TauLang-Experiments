"""Independent finite-support/lexical-binding regression audit; math only.
Reference quantifiers enumerate all child subsets and filter by projection,
not the implementation's per-cell ternary enumeration. This is bounded testing,
not a universal proof or proof of Tau parsing semantics.
"""
from pathlib import Path
import argparse, hashlib, importlib, itertools, json, random, sys, time


def universe(n): return tuple(itertools.product((False, True), repeat=n))


def subsets(xs):
    for bits in itertools.product((False, True), repeat=len(xs)):
        yield frozenset(x for x,b in zip(xs,bits) if b)


def ref_extensions(s, n):
    return (r for r in subsets(universe(n+1)) if frozenset(v[:-1] for v in r)==s)


def ref_term(t, names, valuation):
    op=t[0]
    if op=='var': return valuation[len(names)-1-names[::-1].index(t[1])]
    if op=='zero': return False
    if op=='one': return True
    if op=='not': return not ref_term(t[1],names,valuation)
    a,b=(ref_term(x,names,valuation) for x in t[1:])
    return {'and': a and b, 'or': a or b, 'xor': a != b}[op]


def ref_formula(f, names, s):
    op=f[0]
    if op=='T': return True
    if op=='F': return False
    if op in ('eq0','ne0'):
        z=all(not ref_term(f[1],names,v) for v in s)
        return z if op=='eq0' else not z
    if op=='notF': return not ref_formula(f[1],names,s)
    if op=='andF': return ref_formula(f[1],names,s) and ref_formula(f[2],names,s)
    if op=='orF': return ref_formula(f[1],names,s) or ref_formula(f[2],names,s)
    if op=='exists': return any(ref_formula(f[2],names+(f[1],),r) for r in ref_extensions(s,len(names)))
    raise ValueError(op)


def from_mask(mask,n):
    return frozenset(tuple(bool(i>>j&1) for j in range(n)) for i in range(1<<n) if mask>>i&1)


def gen_term(rng,names,d):
    if d==0 or rng.random()<.35: return rng.choice([('zero',),('one',)]+[('var',n) for n in names])
    op=rng.choice(('not','and','or','xor'))
    return (op,gen_term(rng,names,d-1)) if op=='not' else (op,gen_term(rng,names,d-1),gen_term(rng,names,d-1))


def gen_formula(rng,names,d,q):
    if d==0 or rng.random()<.35:
        return rng.choice((('T',),('F',),(rng.choice(('eq0','ne0')),gen_term(rng,names,2))))
    choices=['notF','andF','orF']+(['exists'] if q else [])
    op=rng.choice(choices)
    if op=='exists':
        name=rng.choice(('a','b','c'))
        return (op,name,gen_formula(rng,names+(name,),d-1,q-1))
    if op=='notF': return (op,gen_formula(rng,names,d-1,q))
    return (op,gen_formula(rng,names,d-1,q),gen_formula(rng,names,d-1,q))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    sys.path.insert(0,str(args.source.resolve()))
    S=importlib.import_module('support_oracle'); E=importlib.import_module('engine'); P=importlib.import_module('normalized_parser')
    N=importlib.import_module('native_oracle')
    start=time.monotonic(); rows=[]; checks=0
    def check(name,got,want,detail=None):
        nonlocal checks
        checks+=1
        if got != want: rows.append({'name':name,'got':got,'expected':want,'detail':detail})
    # Exhaustively enumerate one-step refinements independently at n <= 2.
    ref_count=0
    for n in range(3):
        for mask in range(1,1<<(1<<n)):
            actual=[from_mask(x,n+1) for x in S.refinement_supports(mask,n)]
            expected=set(ref_extensions(from_mask(mask,n),n))
            check('refinement_set',set(actual),expected,{'n':n,'mask':mask})
            check('refinement_no_duplicates',len(actual),len(set(actual)),{'n':n,'mask':mask})
            ref_count+=len(actual)
    # Explicit binding/cache and nontrivial/atomless controls.
    a=('var','a'); b=('var','b')
    controls=[
      (('eq0',('one',)),(),[False]),
      (('orF',('eq0',a),('eq0',('not',a))),('a',),[True,True,False]),
      (('exists','a',('andF',('ne0',a),('ne0',('not',a)))),(),[True]),
      (('andF',('eq0',a),('exists','a',('ne0',a))),('a',),[True,False,False]),
      (('exists','a',('andF',('eq0',a),('exists','a',('ne0',a)))),(),[True]),
      (('notF',('exists','a',('notF',('exists','b',('eq0',('xor',a,b)))))),(),[True]),
    ]
    for f,names,want in controls:
        result=S.evaluate_formula(f,free_variables=names)
        check('binding_control_complete',result.complete,True,{'formula':f,'interface':names})
        check('binding_control', [o.value for o in result.observations],want,{'formula':f,'interface':names})
    rng=random.Random(708130042)
    corpus=[(gen_formula(rng,('a',),4,2),('a',)) for _ in range(160)]
    corpus += [(gen_formula(rng,('a','b'),3,1),('a','b')) for _ in range(80)]
    observations=0
    for f,names in corpus:
        result=S.evaluate_formula(f,free_variables=names)
        check('generated_complete',result.complete,True,{'formula':f,'interface':names})
        for o in result.observations:
            check('independent_truth',o.value,ref_formula(f,names,from_mask(o.support_mask,len(names))),{'formula':f,'interface':names,'mask':o.support_mask})
            observations+=1
    # Parser/renderer AST round trips without quantifiers; semantic equality is sufficient.
    parser_cases=0
    for _ in range(200):
        f=gen_formula(rng,('a','b'),3,0)
        parsed=P.parse_normalized_formula(E.render(f),('a','b'))
        check('render_parse',S.compare_formulas(f,parsed,free_variables=('a','b')).equivalent,True,{'formula':f,'parsed':parsed})
        parser_cases+=1
    # Native receipt parser must fail closed for diagnostics, extra history, whitespace junk.
    receipt={'timed_out':False,'returncode':0,'stderr':'','stdout':'%1: T\n'}
    check('native_truth_valid',N.exact_truth(receipt),'T')
    for field,value in [('timed_out',True),('returncode',1),('stderr','error'),('stdout','%1: T\n%2: T'),('stdout','T'),('stdout','%1: TRUE'),('stdout','%1: T other')]:
        r=dict(receipt);r[field]=value;check('native_truth_fail_closed',N.exact_truth(r),'UNKNOWN',r)
    # Two directions are mandatory even if one implication is valid.
    fake=N.NativeOracle.__new__(N.NativeOracle)
    fake.binary_sha256='audit-fake-binary'; fake.cache={}
    fake.run=lambda command,label: dict(receipt,truth='T' if label.endswith(':forward') else 'F')
    fake_ctx=E.Context((('a','tau'),),V=('a',))
    one_way=fake.equivalent(('eq0',('var','a')),('T',),fake_ctx,'audit-one-way')
    check('native_two_directions_required',one_way.status,'DIFFERENT')
    # Egraph soundness sampled independently; formulas include binders/shadowing.
    egraph_cases=0
    for f,names in corpus[:80]:
        ctx=E.Context(tuple((x,'tau') for x in names),V=names)
        g, report=E.optimize(f,ctx,iterations=2,node_limit=300)
        for mask in range(1,1<<(1<<len(names))):
            s=from_mask(mask,len(names))
            check('egraph_preserves_reference',ref_formula(f,names,s),ref_formula(g,names,s),{'formula':f,'output':g,'mask':mask,'stop_reason':report.stop_reason})
        egraph_cases+=1
    report={'status':'PASS' if not rows else 'FAIL','seed':708130042,'checks':checks,'failures':rows,'refinement_states':ref_count,'generated_formula_count':len(corpus),'generated_support_observations':observations,'parser_roundtrips':parser_cases,'egraph_cases':egraph_cases,'elapsed_s':time.monotonic()-start,'source':str(args.source.resolve()),'source_sha256':{x:hashlib.sha256((args.source/x).read_bytes()).hexdigest() for x in ('support_oracle.py','engine.py','normalized_parser.py','native_oracle.py')},'limitations':['No native executable was invoked.','Finite regression evidence does not prove Python refinement.','Egraph tested with no semantic pair injections.','No native parser or C++ semantics proved.']}
    args.out.write_text(json.dumps(report,indent=2,default=repr)+'\n');print(json.dumps(report,indent=2,default=repr));return bool(rows)

if __name__=='__main__':raise SystemExit(main())
