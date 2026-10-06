#!/usr/bin/env python3
"""Bounded search over the conditions of an output-elimination identity.

The proposals are human/model supplied. This pilot trains no neural model and
proves no unbounded theorem. It retains counterexamples and groups candidates
that have identical behavior on the search bank.
"""
import hashlib
import itertools
import json
from pathlib import Path
import sys


def value(t, env, width):
    op, *a = t
    if op == "const": return a[0]
    if op == "eq": return env[a[0]] == (env[a[1]] if isinstance(a[1], str) else a[1])
    if op == "not": return not value(a[0],env,width)
    if op == "and": return value(a[0],env,width) and value(a[1],env,width)
    if op == "or": return value(a[0],env,width) or value(a[1],env,width)
    if op == "imply": return not value(a[0],env,width) or value(a[1],env,width)
    if op == "if": return value(a[1] if value(a[0],env,width) else a[2],env,width)
    if op in ("all","ex"):
        answers = (value(a[1],dict(env,**{a[0]:x}),width) for x in range(1 << width))
        return (all if op == "all" else any)(answers)
    raise ValueError(op)


def show(t,width):
    op,*a=t
    if op == "const": return "T" if a[0] else "F"
    if op == "eq":
        c = a[1] if isinstance(a[1],str) else f"{{ {a[1]} }}:bv[{width}]"
        return f"({a[0]} = {c})"
    if op == "not": return f"!({show(a[0],width)})"
    if op in ("and","or","imply"):
        return f"({show(a[0],width)} {dict(and_='&&',or_='||',imply_='->')[op+'_']} {show(a[1],width)})"
    if op == "if": return f"({show(a[0],width)} ? {show(a[1],width)} : {show(a[2],width)})"
    if op in ("ex","all"): return f"({op} {a[0]}:bv[{width}] {show(a[1],width)})"
    raise ValueError(op)


def contains(t,var):
    if t[0] == "eq": return t[1] == var or t[2] == var
    if t[0] in ("ex","all") and t[1] == var: return True
    return any(contains(a,var) for a in t[1:] if isinstance(a,tuple))


def candidate(t,width,g):
    if t[0] != "ex": return t
    var,scope=t[1:]
    forbidden=set(); tests=set()
    def walk(n):
        if not contains(n,var): return True
        op,*a=n
        if op == "not" and a[0][0] == "eq":
            left,right=a[0][1:]
            if (left == var) == (right == var): return False
            other=right if left == var else left
            if isinstance(other,str) and not g['allow_open_term']: return False
            forbidden.add(other);tests.add(n);return True
        if op in ("and","or"): return walk(a[0]) and walk(a[1])
        if op == "not": return g['allow_negative_context'] and walk(a[0])
        if op == "imply":
            if contains(a[0],var) and not g['allow_antecedent']: return False
            return walk(a[0]) and walk(a[1])
        if op == "if":
            if contains(a[0],var) and not g['allow_condition']: return False
            return all(walk(x) for x in a)
        if op in ("all","ex"):
            if a[0] == var and not g['allow_shadowing']: return False
            if a[0] != var and not g['through_other_binders']: return False
            return walk(a[1])
        return False
    if not walk(scope) or not tests: return t
    if len(forbidden) >= 1 << width and not g['allow_full_domain']: return t
    def replace(n):
        if n in tests: return ('const',True)
        return tuple(replace(a) if isinstance(a,tuple) else a for a in n)
    return replace(scope)


def cases():
    bank=[];T=('const',True);F=('const',False)
    for width in (1,2):
        dom=range(1 << width)
        subsets=itertools.chain.from_iterable(itertools.combinations(dom,k) for k in range(1,len(dom)+1))
        for forbidden in subsets:
            for connective in ('and','or'):
                p=('not',('eq','x',forbidden[0]))
                for c in forbidden[1:]:p=(connective,p,('not',('eq','x',c)))
                plain=[p,('not',p),('imply',p,F),('imply',T,p),('if',p,F,T),('if',T,p,F)]
                bank += [(width,('ex','x',body)) for body in plain]
                for q in ('all','ex'):
                    for c in dom:
                        y=('eq','y',c)
                        for body in [p,('and',p,y),('or',p,y),('imply',y,p),('imply',p,y),('if',y,p,('not',y))]:
                            bank.append((width,('ex','x',(q,'y',body))))
        bank.append((width,('ex','x',('all','y',('not',('eq','x','y'))))))
        bank.append((width,('ex','x',('and',('not',('eq','x',0)),('all','x',('not',('eq','x',0)))))))
    bank=list(dict.fromkeys(bank))
    bank.sort(key=lambda x:(len(show(x[1],x[0])),x[0],show(x[1],x[0])))
    return bank


def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    bank=cases();truth=[value(t,{},w) for w,t in bank]
    names=['allow_open_term','allow_negative_context','allow_antecedent','allow_condition',
           'allow_shadowing','allow_full_domain','through_other_binders']
    rows=[];groups={}
    for bits in itertools.product((False,True),repeat=len(names)):
        g=dict(zip(names,bits));counter=None;coverage=0;behavior=[]
        for i,(w,t) in enumerate(bank):
            r=candidate(t,w,g);v=value(r,{},w)
            coverage+=r!=t
            behavior.append(show(r,w))
            if v != truth[i] and counter is None:
                counter={'index':i,'width':w,'original':show(t,w),'rewritten':show(r,w),
                         'expected':truth[i],'actual':v}
        h=hashlib.sha256(json.dumps(behavior).encode()).hexdigest()
        row={'guards':g,'rewrites':coverage,'counterexample':counter,'behavior_sha256':h,
             'evidence_level':'refuted_on_finite_domain' if counter else 'bounded_tests_only'}
        rows.append(row)
        if counter is None:groups.setdefault(h,[]).append(len(rows)-1)
    survivors=[r for r in rows if r['counterexample'] is None]
    best=max(r['rewrites'] for r in survivors)
    record={'search':'128 variants of the conditions of one proposed identity',
            'oracle':'exhaustive ordinary integer evaluation, widths 1 and 2',
            'cases':len(bank),'candidate_count':len(rows),'refuted':len(rows)-len(survivors),
            'survivors':len(survivors),'distinct_surviving_behaviors':len(groups),
            'best_bounded_coverage':best,
            'best_candidates':[r for r in survivors if r['rewrites']==best],
            'limitations':['No trained model. Proposals supplied by the researcher.',
                           'Bounded counterexamples refute a candidate; absence of one is not proof.',
                           'Coverage ranks opportunity, not runtime or memory.',
                           'Equivalent behavior is only established on this bank.',
                           'No generated candidate is installed in Tau by this script.'],
            'candidates':rows}
    (out/'bank.json').write_text(json.dumps([{'formula':show(t,w),'width':w,'expected':v} for (w,t),v in zip(bank,truth)],indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k != 'candidates'},indent=2))


if __name__ == '__main__':main()
