"""Study-specific emitted-byte extraction and exact typed-expression parsing.

Inherited engine and support modules stay byte-identical to the pilot. This
module changes the extraction objective explicitly; it does not certify unions.
"""
from __future__ import annotations
from dataclasses import asdict
import re,time
import engine as E
from native_oracle import typed_render
import normalized_parser as P


def emitted_cost(ast,context):
    return len(typed_render(ast,context).encode('utf-8'))


def objective(ast,context):
    return emitted_cost(ast,context),E.tree_cost(ast),repr(ast)


def metrics(ast,context):
    seen=set()
    def visit(node):
        seen.add(node)
        return 1+max((visit(c) for c in E.children(node)),default=0)
    depth=visit(ast)
    source=typed_render(ast,context)
    return {'emitted':source,'expression_bytes':len(source.encode()),'file_bytes':len((source+'.\n').encode()),
            'tree_nodes':E.tree_cost(ast),'dag_nodes':len(seen),'tree_depth':depth}


def parse_native(stdout,variables,expected_sort):
    """Read the inherited compact native grammar, additionally allowing term roots."""
    if expected_sort=='formula':return P.parse_native_output(stdout,variables)
    match=re.fullmatch(r'%1:\s*(.*?)\s*',stdout,flags=re.DOTALL)
    if match is None:raise ValueError('expected exactly one native history result')
    names=tuple(variables)
    if len(names)!=len(set(names)) or any(re.fullmatch('[a-z]',n) is None for n in names):
        raise ValueError('unique lowercase single-letter variables required')
    parser=P._Parser(P._tokens(match.group(1),frozenset(names),False),frozenset(names))
    ast=parser.expression()
    if parser.peek() is not None or P._sort(ast)!='term':raise ValueError('native term output not admitted')
    stack=[(ast,0)];count=0
    while stack:
        node,depth=stack.pop();count+=1
        if count>1000 or depth>128:raise ValueError('native term resource cap')
        stack.extend((c,depth+1) for c in E.children(node))
    return ast


class ByteEGraph(E.EGraph):
    def extract(self,root):
        best={};members=self.members()
        for _ in range(len(members)+1):
            changed=False
            for eid in sorted(members):
                for node in members[eid]:
                    cs=[best.get(self.find(c)) for c in node.args]
                    if any(c is None for c in cs):continue
                    ast=(node.op,)+node.payload+tuple(c[3] for c in cs)
                    value=(*objective(ast,self.context),ast)
                    if eid not in best or value[:3]<best[eid][:3]:
                        best[eid]=value;changed=True
            if not changed:break
        if self.find(root) not in best:raise ValueError('no finite extracted representative')
        return best[self.find(root)][3]


def optimize(root,context,pairs=(),*,iterations=3,node_limit=1000,rewrites=True):
    """Same inherited rewrite/union engine with an explicitly byte-first objective."""
    start=time.perf_counter();g=ByteEGraph(context,node_limit);rejected=[];rounds=0;reason='iteration_limit'
    timings={'insert_s':0.,'pairs_s':0.,'rewrite_s':0.,'rebuild_s':0.,'extract_s':0.}
    def timed(key,fn):
        t=time.perf_counter()
        try:return fn()
        finally:timings[key]+=time.perf_counter()-t
    try:rid=timed('insert_s',lambda:g.add_ast(root))
    except E.NodeLimit:
        return root,{'stop_reason':'root_node_limit','nodes':len(g.nodes),'elapsed_s':time.perf_counter()-start,'timings':timings}
    try:
        for pair in sorted(pairs,key=lambda p:repr((p.left,p.right,p.scope_key))):
            t=time.perf_counter()
            try:
                if pair.scope_key!=context.key:raise ValueError('context key mismatch')
                if E.sort_of(pair.left,context)!=E.sort_of(pair.right,context):raise ValueError('sort mismatch')
                g.union(g.add_ast(pair.left),g.add_ast(pair.right),semantic=True)
            except ValueError as e:rejected.append(str(e))
            finally:timings['pairs_s']+=time.perf_counter()-t
        timed('rebuild_s',g.rebuild)
        if not rewrites:reason='no_rewrites'
        else:
            for rounds in range(1,iterations+1):
                before=len(g.nodes),g.rewrite_unions
                timed('rewrite_s',g.rewrite_round);timed('rebuild_s',g.rebuild)
                if before==(len(g.nodes),g.rewrite_unions):reason='saturated';break
    except E.NodeLimit:
        reason='node_limit';timed('rebuild_s',g.rebuild)
    output=timed('extract_s',lambda:g.extract(rid))
    return output,{'stop_reason':reason,'nodes':len(g.nodes),'classes':len(g.members()),'iterations':rounds,
        'rewrite_unions':g.rewrite_unions,'semantic_unions':g.semantic_unions,'rejected_pairs':rejected,
        'elapsed_s':time.perf_counter()-start,'timings':timings,'extraction_objective':'typed UTF-8 bytes, AST nodes, repr'}
