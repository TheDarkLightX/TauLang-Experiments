"""Fail-closed registry for the declared Tau profile, with complete cost receipts."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json,re,time
import engine as E
import support_oracle as S
from native_oracle import NativeOracle,FLAGS
from study_core import objective

TERM_LIMITS=S.Limits(max_free_variables=8,max_variable_slots=8,max_initial_supports=255,
                     max_states=250000,max_node_evaluations=2000000)
FORM_LIMITS=S.Limits()


def validate_context(ctx):
    if ctx.T!='nontrivialABA' or ctx.temporal!='none' or ctx.K!=('0','1'):
        raise ValueError('unsupported semantic context')
    if any(s!='tau' or re.fullmatch('[a-z]',n) is None for n,s in ctx.terms):
        raise ValueError('only single-letter tau variables admitted')
    if ctx.V is None or len(set(ctx.V))!=len(ctx.V):
        raise ValueError('ordered unique explicit interface required')


def sort_checked(ast,ctx):
    validate_context(ctx)
    stack=[(ast,0)];nodes=0
    while stack:
        a,depth=stack.pop();nodes+=1
        if not isinstance(a,tuple) or not a or not isinstance(a[0],str):raise ValueError('malformed AST')
        if nodes>10000 or depth>100:raise ValueError('AST resource cap')
        if a[0] in ('var','exists') and (len(a)<2 or not isinstance(a[1],str) or re.fullmatch('[a-z]',a[1]) is None):
            raise ValueError('only single-letter variable and binder names admitted')
        stack.extend((c,depth+1) for c in E.children(a))
    sort=E.sort_of(ast,ctx)
    if not E.free_vars(ast)<=ctx.interface:raise ValueError('changed free-variable interface')
    return sort


def comparison(left,right,ctx):
    sort=sort_checked(left,ctx)
    if sort_checked(right,ctx)!=sort:raise ValueError('incompatible sorts')
    fn=S.compare_formulas if sort=='formula' else S.compare_terms
    limits=FORM_LIMITS if sort=='formula' else TERM_LIMITS
    return fn(left,right,free_variables=ctx.V,limits=limits)


def signature(ast,ctx):
    sort=sort_checked(ast,ctx)
    if sort=='formula':
        result=S.evaluate_formula(ast,free_variables=ctx.V,limits=FORM_LIMITS)
        if not result.complete:return None,asdict(result)
        return ('formula',tuple(x.value for x in result.observations)),{'status':result.status,'stats':asdict(result.stats)}
    result=S.compare_terms(ast,ast,free_variables=ctx.V,limits=TERM_LIMITS)
    if not result.complete:return None,asdict(result)
    return (sort,result.left_signature),{'status':result.status,'observations':len(result.observations)}


class CheckedOracle:
    def __init__(self,binary,receipts,timeout=5.):
        self.native=NativeOracle(binary,receipts,timeout)
        self.profile={'theory':'nontrivialABA','descriptor':'tau','constants':['0','1'],
                      'temporal':'none','binary_sha256':self.native.binary_sha256,'flags':FLAGS,
                      'timeout_s':timeout,'term_limits':asdict(TERM_LIMITS),'formula_limits':asdict(FORM_LIMITS),
                      'support_source_sha256':sha256(Path(S.__file__).read_bytes()).hexdigest()}
        self.profile_key=sha256(json.dumps(self.profile,sort_keys=True).encode()).hexdigest()
        self.cache={};self.requests=[]
    def check(self,left,right,ctx,label):
        start=time.perf_counter();before=len(self.native.records)
        key=(self.profile_key,ctx.key,left,right)
        if key in self.cache:
            r=dict(self.cache[key]);r.update(cache_hit=True,label=label,elapsed_s=time.perf_counter()-start,native_processes=0)
            self.requests.append(r);return r
        r={'label':label,'cache_hit':False,'profile_key':self.profile_key,'context_key':ctx.key,'left':left,'right':right}
        try:
            t=time.perf_counter();s=comparison(left,right,ctx);r['support_s']=time.perf_counter()-t;r['support']=asdict(s)
            if not s.equivalent:r['status']='REJECTED_SUPPORT_'+s.status
            else:
                a,b=(left,right) if E.sort_of(left,ctx)=='formula' else (('eq0',('xor',left,right)),('T',))
                n=self.native.equivalent(a,b,ctx,label)
                if n.status=='UNKNOWN':self.native.cache.pop((self.native.binary_sha256,ctx.key,a,b),None)
                r['native']=asdict(n);r['status']='ACCEPTED' if n.status=='EQUIVALENT' else n.status
        except (ValueError,RecursionError) as e:r.update(status='REJECTED_INTERFACE',reason=str(e))
        r['native_processes']=len(self.native.records)-before;r['elapsed_s']=time.perf_counter()-start
        # Every cache lookup includes the full semantic/checker profile and exact ASTs.
        # Inconclusive runs are not negative certificates and are never cached.
        if r['status']=='ACCEPTED' or r['status']=='DIFFERENT':self.cache[key]=dict(r)
        self.requests.append(r);return r
    def pair(self,left,right,ctx,label):
        receipt=self.check(left,right,ctx,label)
        return (E.CheckedPair(left,right,ctx.key) if receipt['status']=='ACCEPTED' else None),receipt


def visible_subtrees(ast):
    """Scoped roots outside binders; a quantified formula is itself an opaque root.

    No subexpression containing a newly bound free name is submitted outside its
    binder. Egraph algebraic rewrites still operate under its explicit scopes.
    """
    seen=set();out=[]
    def visit(x):
        if x in seen:return
        seen.add(x);out.append(x)
        if x[0]!='exists':
            for c in E.children(x):visit(c)
    visit(ast);return out


def candidate_bank(ctx,sort):
    """Fixed small grammar, not a per-case target or a learned test-set registry."""
    vs=[('var',v) for v in ctx.V]
    terms=[('zero',),('one',)]+vs+[('not',v) for v in vs]
    for i,a in enumerate(vs):
        for b in vs[i+1:]:
            terms.extend((op,a,b) for op in ('and','or','xor'))
    if sort=='formula':
        atoms=[(op,t) for t in terms for op in ('eq0','ne0')]
        candidates=[('T',),('F',)]+atoms
    else:candidates=terms
    return sorted(set(candidates),key=lambda a:objective(a,ctx))


def recursive_quotient(root,ctx,pairs):
    """Explicit scoped AST table with full congruence and all-alternative costs.

    Complete ASTs, lexical scopes, and child links are retained in ordinary
    dictionaries. Full-table congruence scans replace egraph hashcons/rebuild.
    This deliberately strong control shares congruence's mathematical structure;
    it supplies no algebraic rewrite rules and no unverified semantic unions.
    """
    start=time.perf_counter();nodes={};valid=[]
    def collect(a,scope=()):
        key=(scope,a)
        if key in nodes:return key
        child_scope=scope
        if a[0]=='exists':child_scope+=((a[1],dict(ctx.terms).get(a[1],ctx.term_sort)),)
        cs=tuple(collect(c,child_scope) for c in E.children(a))
        nodes[key]=(a,scope,cs,E.sort_of(a,ctx,scope));return key
    rid=collect(root)
    for p in pairs:
        if p.scope_key!=ctx.key:continue
        if sort_checked(p.left,ctx)!=sort_checked(p.right,ctx):continue
        valid.append((collect(p.left),collect(p.right)))
    parent={a:a for a in nodes}
    def find(a):
        trail=[]
        while parent[a]!=a:trail.append(a);a=parent[a]
        for x in trail:parent[x]=a
        return a
    def union(a,b):
        a,b=find(a),find(b)
        if a==b:return False
        if (nodes[a][1],nodes[a][3])!=(nodes[b][1],nodes[b][3]):raise ValueError('scope/sort union')
        if repr(a)>repr(b):a,b=b,a
        parent[b]=a;return True
    for a,b in valid:union(a,b)
    scans=0
    while True:
        changed=False;canonical={};scans+=1
        for key in sorted(nodes,key=repr):
            a,scope,children,sort=nodes[key];cs=tuple(find(c) for c in children)
            if a[0] in E.TERM_BINARY+E.FORM_BINARY:cs=tuple(sorted(cs,key=repr))
            payload=(a[1],) if a[0] in ('var','exists') else ()
            shape=(a[0],payload,scope,sort,cs)
            if shape in canonical:changed|=union(key,canonical[shape])
            else:canonical[shape]=key
        if not changed:break
    groups={}
    for a in nodes:groups.setdefault(find(a),[]).append(a)
    best={};passes=0
    for passes in range(1,len(groups)+2):
        changed=False
        for group in sorted(groups,key=repr):
            for key in sorted(groups[group],key=repr):
                a,scope,cs,sort=nodes[key]
                if any(find(c) not in best for c in cs):continue
                payload=(a[1],) if a[0] in ('var','exists') else ()
                candidate=(a[0],)+payload+tuple(best[find(c)] for c in cs)
                if group not in best or objective(candidate,ctx)<objective(best[group],ctx):
                    best[group]=candidate;changed=True
        if not changed:break
    if find(rid) not in best:raise ValueError('recursive class table has no finite representative')
    return best[find(rid)],{'passes':passes,'congruence_scans':scans,'class_members':len(nodes),
        'classes':len(groups),'elapsed_s':time.perf_counter()-start,
        'mechanism':'full scoped AST table; full congruence scans; all-alternative costs; no rewrites'}


def check_emission(oracle,left,right,ctx,label):
    """Final gate parses and checks actual typed serialized text in both directions."""
    from native_oracle import typed_render,exact_truth
    from typed_parser import parse_emitted
    start=time.perf_counter();before=len(oracle.native.records)
    source,target=typed_render(left,ctx),typed_render(right,ctx)
    if parse_emitted(source,ctx.V)!=left or parse_emitted(target,ctx.V)!=right:
        return {'status':'EMITTER_ROUNDTRIP_FAILED','elapsed_s':time.perf_counter()-start}
    sort=sort_checked(left,ctx)
    if sort_checked(right,ctx)!=sort:return {'status':'REJECTED_INTERFACE','elapsed_s':time.perf_counter()-start}
    if not hasattr(oracle,'emission_cache'):oracle.emission_cache={}
    key=(oracle.profile_key,ctx.key,source,target)
    if key in oracle.emission_cache:
        r=dict(oracle.emission_cache[key]);r.update(cache_hit=True,elapsed_s=time.perf_counter()-start,native_processes=0)
        return r
    # Identical immutable ASTs are a structural-identity fallback, not an oracle
    # equivalence finding. This avoids calling an exhausted support run a proof.
    identity=left==right
    s=None if identity else comparison(left,right,ctx)
    if s is not None and not s.equivalent:
        return {'status':'REJECTED_SUPPORT_'+s.status,'support':asdict(s),'elapsed_s':time.perf_counter()-start,'native_processes':0}
    if sort!='formula':source,target=f'(({source}) ^ ({target})) = 0','T'
    binders=', '.join(f'{n} : tau' for n in ctx.V)
    prefix=f'all {binders} ' if binders else ''
    forward=oracle.native.run(f'normalize {prefix}(({source}) -> ({target}))',label+':emitted-forward')
    reverse=oracle.native.run(f'normalize {prefix}(({target}) -> ({source}))',label+':emitted-reverse')
    status='ACCEPTED_IDENTITY' if identity else 'ACCEPTED'
    if forward['truth']!='T' or reverse['truth']!='T':status='DIFFERENT' if 'F' in (forward['truth'],reverse['truth']) else 'UNKNOWN'
    r={'status':status,'structural_identity':identity,'support':None if s is None else asdict(s),
       'native':{'forward':forward,'reverse':reverse},'roundtrip_ast_equal':True,'cache_hit':False,
       'elapsed_s':time.perf_counter()-start,'native_processes':len(oracle.native.records)-before}
    r['cold_elapsed_s']=r['elapsed_s']
    if status.startswith('ACCEPTED'):oracle.emission_cache[key]=dict(r)
    return r
