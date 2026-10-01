#!/usr/bin/env python3
"""Experimental, source-derived sharing and exact-width code generation."""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

def load(path):
    spec=importlib.util.spec_from_file_location('checker_reference_compiler',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    spec.loader.exec_module(module);return module

def generate(source, reference, narrow=True, share=True):
    root=reference.Parser(source).parse()
    nodes=set()
    def visit(node):
        if node in nodes:return
        nodes.add(node)
        if node.width not in (0,32):raise ValueError('This experiment requires only Boolean and 32-bit nodes')
        for child in node.args:visit(child)
    visit(root)
    word='u32' if narrow else 'u128'
    serial=0
    def expression(node,env,lines,indent):
        nonlocal serial
        if node.op=='const':return str(node.value)+word
        if node.op=='var':
            if not str(node.value).startswith('i'):raise ValueError('Unsupported output dependency')
            value=f'input[{int(str(node.value)[1:])-1}]'
            return f'({value} as u32)' if narrow else value
        if share and node in env:return env[node]
        args=[expression(child,env,lines,indent) for child in node.args]
        mask='4294967295'+word
        if node.op=='cast':result=args[0] if narrow else f'({args[0]} & {mask})'
        elif node.op=='complement':result=f'(!{args[0]})' if narrow else f'(!{args[0]} & {mask})'
        elif node.op=='not':result=f'(!{args[0]})'
        elif node.op in ('min','max'):result=f'core::cmp::{node.op}({args[0]}, {args[1]})'
        elif node.op in ('+','-','*'):
            method={'+':'wrapping_add','-':'wrapping_sub','*':'wrapping_mul'}[node.op]
            result=f'({args[0]}).{method}({args[1]})'
            if not narrow:result=f'({result} & {mask})'
        elif node.op in ('<<','>>'):
            method='shift_left' if node.op=='<<' else 'shift_right'
            result=f'{method}({args[0]}, {args[1]})'
        elif node.op in ('&','|','^','=','!=','<','<=','>','>=','&&','||'):
            result=f'({args[0]} {"==" if node.op=="=" else node.op} {args[1]})'
        else:raise ValueError('Unsupported expression: '+node.op)
        if not share:return result
        name='value'+str(serial);serial+=1
        lines.append(indent+f'let {name}: '+('bool' if node.width==0 else word)+f' = {result};')
        env[node]=name;return name
    def tree(node,env,indent):
        lines=[]
        if node.op=='if':
            guard=expression(node.args[0],env,lines,indent)
            lines.append(indent+f'if {guard} {{')
            lines+=tree(node.args[1],dict(env),indent+'    ')
            lines.append(indent+'} else {')
            lines+=tree(node.args[2],dict(env),indent+'    ')
            lines.append(indent+'}')
        else:
            assignments=reference.assignments(node)
            outputs=[expression(assignments[f'o{i+1}'],env,lines,indent) for i in range(21)]
            if narrow:outputs=[f'({value}) as u128' for value in outputs]
            lines.append(indent+'['+', '.join(outputs)+']')
        return lines
    text='// Generated from the checked Tau expression tree; experimental optimizer.\n'
    text+='pub const SPEC_HASH: [u8; 32] = '+repr(list(hashlib.sha256(source.encode()).digest()))+';\n'
    text+=f'fn shift_left(a:{word},b:{word})->{word} {{ if b >= 32 {{0}} else {{ (a << (b as u32)) & 4294967295{word} }} }}\n'
    text+=f'fn shift_right(a:{word},b:{word})->{word} {{ if b >= 32 {{0}} else {{ a >> (b as u32) }} }}\n'
    text+='#[allow(unused_parens)]\npub fn tau_step(input:&[u128;102])->[u128;21] {\n'
    text+='\n'.join(tree(root,{},'    '))+'\n}\n'
    return text, {'narrow':narrow,'share':share,'unique_ast_nodes':len(nodes),'named_intermediates':serial,'source_bytes':len(text.encode())}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
    reference=load(a.root/'tools/compile_tau.py');source=(a.root/'spec/vm.tau').read_text()
    report={}
    (a.output/'baseline.rs').write_text(reference.generate(source))
    for name,narrow,share in [('width32',True,False),('shared128',False,True),('shared32',True,True)]:
        code,meta=generate(source,reference,narrow,share)
        (a.output/(name+'.rs')).write_text(code);report[name]=meta
    (a.output/'generation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
