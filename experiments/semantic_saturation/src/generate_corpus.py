"""Original deterministic synthetic workloads; distinct family and seed holdouts.

This generator never invokes an optimizer, native Tau, or a correctness oracle.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
import argparse,hashlib,json,random
from pathlib import Path
import engine as E

@dataclass(frozen=True)
class Case:
    name:str
    split:str
    family:str
    free:tuple
    original:tuple
    size_parameter:int
    seed:int


def seed_for(namespace):return int.from_bytes(hashlib.sha256(namespace.encode()).digest()[:8],'big')
def v(x):return ('var',x)
def neg(x):return ('not',x)
def nz(x):return ('ne0',x)
def eq(x):return ('eq0',x)
def meet(x,y):return ('and',x,y)
def join(x,y):return ('or',x,y)
def conj(x,y):return ('andF',x,y)
def disj(x,y):return ('orF',x,y)
def nf(x):return ('notF',x)
def ex(x,f):return ('exists',x,f)
def all_(x,f):return nf(ex(x,nf(f)))


def tree(rng,names,budget):
    if budget<=1:return rng.choice([v(x) for x in names]+[('zero',),('one',)])
    if budget==2 or rng.random()<.18:return neg(tree(rng,names,budget-1))
    left=rng.randrange(1,budget-1)
    return (rng.choice(('and','or','xor')),tree(rng,names,left),tree(rng,names,budget-1-left))


def formula(rng,names,budget):
    if budget<=3:return rng.choice((eq,nz))(tree(rng,names,max(1,budget-1)))
    if rng.random()<.2:return nf(formula(rng,names,budget-1))
    left=rng.randrange(2,max(3,budget-1))
    return rng.choice((conj,disj))(formula(rng,names,left),formula(rng,names,max(2,budget-1-left)))


def fold(op,xs):
    xs=list(xs);out=xs[0]
    for x in xs[1:]:out=(op,out,x)
    return out


def family_ast(family,rng,names,size):
    if family=='random_term':return tree(rng,names,size)
    if family=='random_formula':return formula(rng,names,size)
    if family=='quantified_random':
        body=formula(rng,names+('x',),size)
        return rng.choice((ex,all_))('x',body)
    if family=='factoring_composition':
        a=tree(rng,names,max(1,size//6));b=tree(rng,names,max(1,size//6));c=tree(rng,names,max(1,size//6))
        return join(meet(a,b),meet(a,c))
    if family=='multiplexer_holdout':
        # Structurally held out: Shannon switch trees with independently drawn leaves.
        def mux(depth):
            if depth==0:return tree(rng,names,3)
            sel=v(rng.choice(names));return join(meet(sel,mux(depth-1)),meet(neg(sel),mux(depth-1)))
        return mux(1 if size<=16 else 2 if size<=32 else 3)
    if family=='parity_holdout':
        # XOR was seen in training; only this structural chain template is held out.
        # Chain parity remains a primitive-XOR workload, not inverse factoring rules.
        return fold('xor',[tree(rng,names,3) for _ in range(max(2,size//4))])
    if family=='proper_split_composition_holdout':
        # Proper-split law was in the pilot: only its composed structure is held out.
        t=tree(rng,names,max(1,size//4));x=v('x')
        split=ex('x',conj(eq(meet(x,neg(t))),conj(nz(x),nz(meet(t,neg(x))))))
        guard=formula(rng,names,max(2,size//4))
        return rng.choice((conj,disj))(split,guard)
    if family=='mixed_quantifier_pair_holdout':
        # Some formulas are valid and others false/nontrivial; no target supplied.
        a=tree(rng,names,max(1,size//5));x,y=v('x'),v('y')
        base=rng.choice((conj,disj))(eq(meet(x,neg(y))),nz(meet(a,y)))
        return rng.choice((all_,ex))('x',rng.choice((all_,ex))('y',base))
    raise ValueError(family)


def make(split):
    cases=[]
    # Freeze split sizes independently of any optimizer outcomes.
    if split=='train':families=['random_term','random_formula','quantified_random','factoring_composition'];reps=2
    elif split=='dev':families=['random_term','random_formula','quantified_random','factoring_composition'];reps=2
    elif split=='test':families=['random_term','random_formula','quantified_random','factoring_composition','multiplexer_holdout','parity_holdout','proper_split_composition_holdout','mixed_quantifier_pair_holdout'];reps=4
    else:raise ValueError(split)
    for family in families:
        term_family=family in ('random_term','factoring_composition','multiplexer_holdout','parity_holdout')
        counts=(2,4,6,8) if term_family else (1,2,3)
        if family=='mixed_quantifier_pair_holdout':counts=(0,1,2)
        for n in counts:
            names=tuple('abcdefgh'[:n])
            for size in (16,32,64):
                for rep in range(reps):
                    label=f'tau-study-v2/{split}/{family}/n{n}/s{size}/r{rep}'
                    seed=seed_for(label);rng=random.Random(seed)
                    ast=family_ast(family,rng,names,size)
                    ctx=E.Context(tuple((x,'tau') for x in names),V=names)
                    E.sort_of(ast,ctx)
                    name=f'{split}-{family}-n{n}-s{size}-r{rep}'
                    cases.append(Case(name,split,family,names,ast,size,seed))
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['train','dev','test'],required=True);p.add_argument('--out',required=True)
    args=p.parse_args();rows=[asdict(c) for c in make(args.split)]
    target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'schema':'tau-study-corpus/v2','split':args.split,'cases':rows},sort_keys=True,indent=2)+'\n')
    print(json.dumps({'cases':len(rows),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
