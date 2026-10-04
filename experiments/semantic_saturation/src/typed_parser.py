"""Independent parser for the fully parenthesized typed emitted study grammar.

This grammar is smaller than Tau. It does not use engine.children or render,
and rejects every non-admitted token and descriptor rather than repairing text.
"""
from __future__ import annotations
import re

TOKEN=re.compile(r"\s*(?:(?P<name>[a-z]+)|(?P<num>[01])|(?P<form>[TF])|(?P<op>&&|\|\||!=|[()':!&|^=]))")

class TypedParseError(ValueError):pass


def parse_emitted(source,free,*,descriptor='tau'):
    if not isinstance(source,str) or len(source)>200000:raise TypedParseError('emitted length cap')
    if descriptor!='tau':raise TypedParseError('unsupported descriptor')
    if len(free)!=len(set(free)) or any(re.fullmatch('[a-z]',x) is None for x in free):raise TypedParseError('invalid free interface')
    tokens=[];position=0
    while position<len(source):
        m=TOKEN.match(source,position)
        if not m:raise TypedParseError('unknown token at '+str(position))
        tokens.append(m.group(m.lastgroup));position=m.end()
    i=0
    def peek():return tokens[i] if i<len(tokens) else None
    def take(expected=None):
        nonlocal i
        if i>=len(tokens):raise TypedParseError('unexpected end')
        t=tokens[i];i+=1
        if expected is not None and t!=expected:raise TypedParseError('expected '+expected)
        return t
    def expr(env,depth=0):
        if depth>150:raise TypedParseError('depth cap')
        t=take()
        if t in ('0','1','T','F'):
            ast=({'0':'zero','1':'one','T':'T','F':'F'}[t],);sort='formula' if t in ('T','F') else 'term'
        elif t=='ex':
            name=take()
            if re.fullmatch('[a-z]',name) is None:raise TypedParseError('binder name')
            take(':');take(descriptor);take('(')
            body,s=expr(env+(name,),depth+1);take(')')
            if s!='formula':raise TypedParseError('binder body sort')
            ast=('exists',name,body);sort='formula'
        elif t=='!':
            take('(');body,s=expr(env,depth+1);take(')')
            if s!='formula':raise TypedParseError('negation sort')
            ast=('notF',body);sort='formula'
        elif t=='(':
            if peek() in env and i+1<len(tokens) and tokens[i+1]==':':
                name=take();take(':');take(descriptor);take(')');ast=('var',name);sort='term'
            else:
                left,ls=expr(env,depth+1)
                if peek()==')':take(')');ast=left;sort=ls
                else:
                    op=take()
                    if op in ('=','!='):
                        take('0');take(')')
                        if ls!='term':raise TypedParseError('comparison sort')
                        ast=('eq0' if op=='=' else 'ne0',left);sort='formula'
                    else:
                        right,rs=expr(env,depth+1);take(')')
                        tags={'&':'and','|':'or','^':'xor','&&':'andF','||':'orF'}
                        if op not in tags:raise TypedParseError('unknown binary operator')
                        required='formula' if op in ('&&','||') else 'term'
                        if ls!=required or rs!=required:raise TypedParseError('binary sort')
                        ast=(tags[op],left,right);sort=required
        else:raise TypedParseError('untyped or undeclared variable')
        while peek()=="'":
            take()
            if sort!='term':raise TypedParseError('complement sort')
            ast=('not',ast)
        return ast,sort
    ast,sort=expr(tuple(free))
    if i!=len(tokens):raise TypedParseError('trailing tokens')
    return ast
