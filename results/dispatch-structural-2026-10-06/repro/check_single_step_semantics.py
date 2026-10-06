#!/usr/bin/env python3
"""Independent finite-relation checks for memoryless Tau constants.

The expected satisfiability answer is forall inputs, exists outputs.
Validity is forall inputs and outputs. Every assignment is enumerated.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess

INPUTS=('i1','i2')
OUTPUTS=('o1','o2')

def term(t,env,w):
    op,*a=t;mask=(1<<w)-1
    if op=='v':return env[a[0]]
    if op=='c':return a[0]&mask
    x=term(a[0],env,w)
    if op=='not':return x^mask
    y=term(a[1],env,w)
    return {'add':lambda:(x+y)&mask,'xor':lambda:x^y,'and':lambda:x&y}[op]()

def truth(f,env,w):
    op,*a=f
    if op=='eq':return term(a[0],env,w)==term(a[1],env,w)
    if op=='lt':return term(a[0],env,w)<term(a[1],env,w)
    if op=='not':return not truth(a[0],env,w)
    if op=='and':return truth(a[0],env,w) and truth(a[1],env,w)
    if op=='or':return truth(a[0],env,w) or truth(a[1],env,w)
    if op=='imply':return not truth(a[0],env,w) or truth(a[1],env,w)
    if op=='if':return truth(a[1] if truth(a[0],env,w) else a[2],env,w)
    raise ValueError(op)

def vars_in(x):
    if x[0]=='v':return {x[1]}
    return set().union(*(vars_in(a) for a in x[1:] if isinstance(a,tuple)))

def show_term(t,w):
    op,*a=t
    if op=='v':return a[0]+f'[t]:bv[{w}]'
    if op=='c':return '{ '+str(a[0]&((1<<w)-1))+f' }}:bv[{w}]'
    if op=='not':return '('+show_term(a[0],w)+")'"
    return '('+show_term(a[0],w)+' '+{'add':'+','xor':'^','and':'&'}[op]+' '+show_term(a[1],w)+')'

def show(f,w):
    op,*a=f
    if op in ('eq','lt'):return '('+show_term(a[0],w)+(' = ' if op=='eq' else ' < ')+show_term(a[1],w)+')'
    if op=='not':return '!('+show(a[0],w)+')'
    if op=='if':return '('+show(a[0],w)+' ? '+show(a[1],w)+' : '+show(a[2],w)+')'
    return '('+show(a[0],w)+' '+{'and':'&&','or':'||','imply':'->'}[op]+' '+show(a[1],w)+')'

def make_bank():
    bank=[]
    i,j,o,p=[('v',v) for v in (*INPUTS,*OUTPUTS)]
    for w in (1,2,3):
        z=('c',0);one=('c',1);top=('c',(1<<w)-1)
        terms=[i,j,z,one,top,('not',i),('add',i,one),('xor',i,j),('and',i,j)]
        guards=[('eq',i,z),('lt',i,j),('eq',j,top)]
        forms=[]
        for t in terms:
            eq=('eq',o,t)
            forms += [eq,('not',eq),('and',eq,('not',eq)),('or',eq,('not',eq))]
            for guard in guards:
                forms += [('and',guard,eq),('imply',guard,eq),('if',guard,eq,('eq',o,top))]
            forms += [('and',eq,('eq',p,('add',o,one))),
                      ('and',eq,('and',('eq',p,o),('not',('eq',p,t))))]
        forms += [*guards,('eq',o,z),('lt',o,z),('lt',i,o),('lt',o,i),
                  ('and',('lt',i,o),('lt',o,j)),('and',('eq',o,j),('eq',p,i))]
        seen=set()
        for f in forms:
            text=show(f,w)
            if text in seen:continue
            seen.add(text)
            names=vars_in(f);ins=[v for v in INPUTS if v in names];outs=[v for v in OUTPUTS if v in names]
            d=range(1<<w);sat=True;valid=True;assignments=0
            for iv in itertools.product(d,repeat=len(ins)):
                row=[]
                for ov in itertools.product(d,repeat=len(outs)):
                    env=dict(zip(ins,iv));env.update(zip(outs,ov))
                    row.append(truth(f,env,w));assignments+=1
                sat &= any(row);valid &= all(row)
            bank.append({'width':w,'body':text,'satisfiable':sat,'valid':valid,
                         'assignments':assignments,'inputs':ins,'outputs':outs})
    return bank

def clean(s):
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',s)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--binary',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--route',choices=('constant','api'),default='constant')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    bank=make_bank()
    (args.out/'cases.json').write_text(json.dumps(bank,indent=2)+'\n')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before=sha(args.binary); results=[]
    for w in sorted({c['width'] for c in bank}):
        rows=[c for c in bank if c['width']==w];commands=[];expected=[]
        for c in rows:
            if args.route=='constant':
                pairs=[('n { always '+c['body']+' }:tau = 0',not c['satisfiable']),
                       ('n { always '+c['body']+' }:tau = 1',c['valid'])]
            else:
                pairs=[('sat always '+c['body'],c['satisfiable']),
                       ('valid always '+c['body'],c['valid'])]
            for cmd,value in pairs:
                commands.append(cmd);expected.append('T' if value else 'F')
        stdin='set charvar off\n'+'\n'.join(commands)+'\nq\n'
        folder=args.out/('width-'+str(w));folder.mkdir()
        (folder/'stdin.txt').write_text(stdin)
        with (folder/'stdout.txt').open('w') as out,(folder/'stderr.txt').open('w') as err:
            proc=subprocess.run([str(args.binary.resolve()),'-X'],input=stdin,text=True,stdout=out,stderr=err,timeout=120)
        out=clean((folder/'stdout.txt').read_text());err=clean((folder/'stderr.txt').read_text())
        chunks=out.split('tau> ');observed=[]
        for chunk in chunks:
            cmd,sep,body=chunk.partition('\n')
            if cmd in commands:
                answers=re.findall(r'^%\d+: (T|F)\s*$',body,re.M)
                observed.append((cmd,answers))
        aligned=[v[0] for v in observed]==commands
        checks=[]
        if aligned:
            for cmd,e,(_,ans) in zip(commands,expected,observed):
                checks.append({'query':cmd,'expected':e,'answers':ans,'ok':ans==[e]})
        result={'width':w,'formulas':len(rows),'queries':len(expected),'observed_queries':len(observed),
                'answers':sum(len(a) for _,a in observed),'aligned':aligned,
                'exit_code':proc.returncode,'checks':checks,
                'ok':aligned and all(c['ok'] for c in checks) and proc.returncode==0
                     and re.search(r'\b(error|unknown)\b',out+err,re.I) is None,
                'files':{n:sha(folder/n) for n in ('stdin.txt','stdout.txt','stderr.txt')}}
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
    result={'binary_sha256':before,'binary_unchanged':before==sha(args.binary),'route':args.route,
            'formulas':len(bank),'queries':sum(r['queries'] for r in results),
            'answers':sum(r['answers'] for r in results),'assignments':sum(c['assignments'] for c in bank),
            'failed_checks':sum(not c['ok'] for r in results for c in r['checks']),
            'incomplete_checks':sum(len(c['answers'])!=1 for r in results for c in r['checks']),
            'ok':all(r['ok'] for r in results) and before==sha(args.binary),
            'scope':'Independent finite relations; fresh session per bit width; every query matched to its echoed command. The constant route tests a proposed semantic contract; it is not evidence of direct helper use.'}
    (args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
