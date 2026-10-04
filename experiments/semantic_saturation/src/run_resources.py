"""Frozen support-enumeration and egraph search-cap screens (no native claims)."""
from __future__ import annotations
from dataclasses import asdict,replace
from pathlib import Path
import argparse,hashlib,json,time
import engine as E
import support_oracle as S
from study_core import optimize,metrics
from run_study import tuple_tree,context,write,digest


def support_matrix():
    rows=[]
    for n in range(6):
        free=tuple('abcde'[:n]);a=('var',free[0]) if free else ('one',)
        forms={'constant_false':('F',),'atom_nonzero':('ne0',a),
               'endpoint_boundary':('orF',('eq0',a),('eq0',('not',a))),
               'all_parameters_nonzero':('T',)}
        for x in free:forms['all_parameters_nonzero']=('andF',forms['all_parameters_nonzero'],('ne0',('var',x)))
        for family,ast in forms.items():
            for initial in (255,65535):
                for states in (1000,10000,250000):
                    rows.append({'id':f'free-n{n}-{family}-i{initial}-s{states}','family':family,'free':free,'ast':ast,
                        'limits':asdict(replace(S.Limits(),max_free_variables=5,max_initial_supports=initial,max_states=states))})
    for n in range(4):
        free=tuple('abc'[:n]);a=('var',free[0]) if free else ('one',)
        for depth in range(5):
            for family in ('quantified_false','quantified_true','nested_nonzero_witness'):
                ast=('F',) if family=='quantified_false' else ('T',) if family=='quantified_true' else ('ne0',a)
                for name in 'xyzw'[:depth]:
                    body=ast if family!='nested_nonzero_witness' else ('andF',ast,('ne0',('var',name)))
                    ast=('exists',name,body)
                for states in (1000,10000,250000):
                    rows.append({'id':f'quant-n{n}-d{depth}-{family}-s{states}','family':family,'free':free,'ast':ast,
                        'limits':asdict(replace(S.Limits(),max_states=states))})
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--development-results');p.add_argument('--emit-protocol-only',action='store_true');args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    matrix=support_matrix();write(out/'matrix.json',matrix)
    write(out/'manifest-start.json',{'support_source_sha256':digest(S.__file__),'runner_sha256':digest(__file__),'matrix_sha256':digest(out/'matrix.json'),'cases':len(matrix),'native_processes':0})
    if args.emit_protocol_only:return
    results=[]
    for row in matrix:
        t=time.perf_counter();r=S.evaluate_formula(row['ast'],free_variables=row['free'],limits=S.Limits(**row['limits']))
        results.append({'id':row['id'],'family':row['family'],'n_free':len(row['free']),'elapsed_s':time.perf_counter()-t,
            'status':r.status,'complete':r.complete,'reason':r.reason,'stats':asdict(r.stats),
            'observation_sha256':hashlib.sha256(json.dumps([asdict(x) for x in r.observations],sort_keys=True).encode()).hexdigest(),
            'true_observations':sum(x.value for x in r.observations)})
    write(out/'support-results.json',results)
    graph=[]
    if args.development_results:
        base=Path(args.development_results);corpus=json.loads(Path(__file__).parent.parent.joinpath('corpora/dev.json').read_text())['cases']
        selected=corpus[::3][:24]
        for row in selected:
            receipt=base/row['name']/'result.json';r=json.loads(receipt.read_text());ctx=context(row);root=tuple_tree(row['original'])
            pairs=[E.CheckedPair(tuple_tree(x['left']),tuple_tree(x['right']),x['scope_key']) for x in r['registry']['pairs']]
            for nodes in (250,1000,4000):
                for iterations in (1,3,5):
                    out_ast,detail=optimize(root,ctx,pairs,node_limit=nodes,iterations=iterations)
                    graph.append({'case':row['name'],'source_receipt_sha256':digest(receipt),'nodes_budget':nodes,'iterations_budget':iterations,
                         'output_metrics':metrics(out_ast,ctx),'detail':detail})
        write(out/'search-results.json',graph)
    write(out/'SUMMARY.json',{'status':'COMPLETE','support_cases':len(results),'support_statuses':{s:sum(r['status']==s for r in results) for s in sorted({r['status'] for r in results})},
        'support_wall_s':sum(r['elapsed_s'] for r in results),'search_cases':len(graph),'search_wall_s':sum(r['detail']['elapsed_s'] for r in graph),'native_processes':0,
        'nonclaims':['No native proof or optimizer quality gain is established by this resource screen.','Graph outputs require the separate acceptance gate before deployment.']})
if __name__=='__main__':main()
