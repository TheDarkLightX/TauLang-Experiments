#!/usr/bin/env python3
"""Generate exact ground min/max checks independent of Tau's evaluator."""
from pathlib import Path
from itertools import product
import json

cases=[]
for width in (1,2,3):
    size=1<<width
    for name,operation in [('min',min),('max',max)]:
        for a,b in product(range(size),repeat=2):
            term=f'{name}({{{a}}}:bv[{width}], {{{b}}}:bv[{width}])'
            value=operation(a,b)
            d=(a+b+1)%size
            other=f'{name}({{{b}}}:bv[{width}], {{{d}}}:bv[{width}])'
            other_value=operation(b,d)
            narrower=max(1,width-1)
            expressions=[
                ('widen',f'(bv[{width+1}]) {term}',value,width+1),
                ('narrow',f'(bv[{narrower}]) {term}',value&((1<<narrower)-1),narrower),
                ('complement',term+"'",value^(size-1),width),
                ('left-adjacent',term+f'{{{d}}}:bv[{width}]',value&d,width),
                ('both-adjacent',term+other,value&other_value,width),
                ('spaced',term+' '+other,value&other_value,width),
                ('nested-complement',f'{name}({term}, {{{d}}}:bv[{width}])' + "'",operation(value,d)^(size-1),width),
            ]
            for position,expr,expected,out_width in expressions:
                # Both truth values prevent an always-true result from passing.
                for equal in (True,False):
                    target=expected if equal else expected^1
                    cases.append(dict(id=f'{name}-w{width}-{a}-{b}-{position}-{int(equal)}',
                                      width=width,position=position,operation=name,
                                      command=f'normalize ({expr}) = {{{target}}}:bv[{out_width}].',
                                      expected='T' if equal else 'F'))
path=Path(__file__).with_name('exact-cases.json')
if path.exists():raise SystemExit('Refusing to overwrite generated cases')
path.write_text(json.dumps(cases,indent=2)+'\n')
print(len(cases),'exact ground checks')
