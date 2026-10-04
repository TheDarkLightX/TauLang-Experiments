"""Run immutable corpus rows, shared-transcript controls, and serialized final gates."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import argparse,collections,hashlib,json,random,re,time
import engine as E
from study_core import emitted_cost,objective,metrics,optimize,parse_native
from native_oracle import FLAGS
from checked_registry import CheckedOracle,signature,candidate_bank,visible_subtrees,recursive_quotient,check_emission
from baselines import run_sympy_baseline


def tuple_tree(x):return tuple(tuple_tree(v) for v in x) if isinstance(x,list) else x
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def context(row):return E.Context(tuple((n,'tau') for n in row['free']),V=tuple(row['free']))
def native_receipts(obj):
    if isinstance(obj,dict):
        if all(k in obj for k in ('ordinal','command','elapsed_s','binary_sha256')):yield obj
        else:
            for v in obj.values():yield from native_receipts(v)
    elif isinstance(obj,(list,tuple)):
        for v in obj:yield from native_receipts(v)

def charge(*objects):
    records={r['ordinal']:r for o in objects for r in native_receipts(o)}
    return {'native_processes':len(records),'native_wall_s':sum(r['elapsed_s'] for r in records.values()),'ordinals':sorted(records)}


def unique_gate_cold_cost(*gates):
    """Charge one cold validation per actual emitted-certificate receipt pair."""
    seen=set();total=0.
    for index,gate in enumerate(gates):
        native=gate.get('native',{})
        if 'forward' in native and 'reverse' in native:
            key=(native['forward']['binary_sha256'],native['forward']['ordinal'],native['reverse']['ordinal'])
        else:key=('uncached_inconclusive',index)
        if key not in seen:
            seen.add(key);total+=gate.get('cold_elapsed_s',gate['elapsed_s'])
    return total


def build_pairs(root,native,ctx,oracle,limits):
    start=time.perf_counter();pairs=[];receipts=[];signatures=[];banks={};native_gate=None
    if native is not None and native!=root:
        pair,native_gate=oracle.pair(root,native,ctx,'native-normalization-proposal')
        receipts.append(native_gate)
        if pair:pairs.append(pair)
    subtrees=visible_subtrees(root);truncated=len(subtrees)>limits['subtrees'];subtrees=subtrees[:limits['subtrees']]
    for node in subtrees:
        if len(pairs)>=limits['pairs']:break
        sort=E.sort_of(node,ctx)
        if sort not in banks:
            bank=[]
            for candidate in candidate_bank(ctx,sort)[:limits['bank_candidates']]:
                sig,info=signature(candidate,ctx)
                if sig is not None:bank.append((candidate,sig))
            banks[sort]=bank
        t=time.perf_counter();sig,info=signature(node,ctx)
        signatures.append({'node':node,'status':info.get('status'),'elapsed_s':time.perf_counter()-t,'complete':sig is not None,'detail':info})
        if sig is None:continue
        matches=[a for a,s in banks[sort] if s==sig and a!=node]
        for candidate in matches[:limits['matches_per_subtree']]:
            if len(pairs)>=limits['pairs']:break
            pair,receipt=oracle.pair(node,candidate,ctx,'registry-'+str(len(receipts)))
            receipts.append(receipt)
            if pair and pair not in pairs:pairs.append(pair)
    return pairs,{'elapsed_s':time.perf_counter()-start,'signatures':signatures,'proposal_receipts':receipts,
        'native_proposal_gate':native_gate,'pairs':[asdict(p) for p in pairs],'visible_subtrees_considered':len(subtrees),
        'subtree_cap_reached':truncated,'pair_cap_reached':len(pairs)>=limits['pairs'],
        'banks':{k:len(v) for k,v in banks.items()},'candidate_policy':'fixed small grammar; exact support prefilter; up to3 cheapest matching alternatives per visible subtree'}


def run_case(row,binary,out,config):
    start=time.perf_counter();ctx=context(row);root=tuple_tree(row['original']);out.mkdir(parents=True,exist_ok=False)
    oracle=CheckedOracle(binary,out/'native',config['native_timeout_s'])
    normalization=oracle.native.normalize(root,ctx,row['name']);native=None;parse_reason=None
    if normalization['returncode']==0 and not normalization['stderr'].strip() and not normalization['timed_out']:
        try:native=parse_native(normalization['stdout'],ctx.V,E.sort_of(root,ctx))
        except (ValueError,RecursionError) as e:parse_reason=str(e)
    else:parse_reason='native diagnostic, timeout, or nonzero exit'
    parsed_native=native
    pairs,registry=build_pairs(root,native,ctx,oracle,config)
    admission_status=('ACCEPTED_IDENTITY' if native==root else (registry['native_proposal_gate'] or {}).get('status','UNAVAILABLE')) if native is not None else 'PARSE_OR_NORMALIZATION_FAILED'
    if native is not None and native!=root and not any(p.left==root and p.right==native for p in pairs):native=None
    roots=[root]+([native] if native is not None else [])+[p.right for p in pairs if p.left==root]+[p.left for p in pairs if p.right==root]
    root_pairs=[p for p in pairs if p.left==root or p.right==root]
    native_detail={'normalization':normalization,'parse_reason':parse_reason,'proposal_admission_status':admission_status,
        'parsed_native_candidate':parsed_native,'parsed_native_metrics':None if parsed_native is None else metrics(parsed_native,ctx),
        'retained_original_reason':None if native is not None else ('native_proposal_'+admission_status if parsed_native is not None else 'native_parse_or_normalization_failure')}
    candidates={'native_reserialized':(native if native is not None else root,dict(native_detail))}
    candidates['native_guarded']=(min([root]+([native] if native is not None else []),key=lambda x:objective(x,ctx)),dict(native_detail))
    t=time.perf_counter();selected=min(roots,key=lambda x:objective(x,ctx))
    candidates['semantic_list']=(selected,{'elapsed_s':time.perf_counter()-t,'root_menu_count':len(set(roots))})
    operations=['rewrite_guarded','recursive_congruence','semantic_graph','hybrid','hybrid_root_only','sympy']
    random.Random(row['seed']^0xBAD5EED).shuffle(operations)
    for arm in operations:
        t=time.perf_counter()
        if arm=='recursive_congruence':candidate,detail=recursive_quotient(root,ctx,pairs)
        elif arm=='sympy':
            result=run_sympy_baseline(root,ctx,max_propositions=config['sympy_max_propositions'],timeout_seconds=config['sympy_timeout_s'])
            candidate,detail=result.output,result.to_dict()
        else:
            these=() if arm=='rewrite_guarded' else root_pairs if arm=='hybrid_root_only' else pairs
            candidate,detail=optimize(root,ctx,these,iterations=config['iterations'],node_limit=config['enodes'],rewrites=arm!='semantic_graph')
        candidate=min([root,candidate],key=lambda x:objective(x,ctx))
        candidates[arm]=(candidate,{'method_wall_s':time.perf_counter()-t,**detail})
    # Native/SymPy portfolio includes both component costs; it supplies no free candidates to other arms.
    portfolio=min([root,candidates['native_guarded'][0],candidates['sympy'][0]],key=lambda x:objective(x,ctx))
    candidates['native_sympy_portfolio']=(portfolio,{'components':['native_guarded','sympy']})
    # A fully guarded hybrid retains the same explicit roots as the semantic selectors.
    for arm in ('recursive_congruence','semantic_graph','hybrid','hybrid_root_only'):
        c,d=candidates[arm];candidates[arm]=(min(roots+[c],key=lambda x:objective(x,ctx)),d)
    outputs={};order=list(candidates);random.Random(row['seed']^0xFACE).shuffle(order)
    for arm in order:
        candidate,detail=candidates[arm]
        gate=check_emission(oracle,root,candidate,ctx,row['name']+':'+arm)
        accepted=gate['status'].startswith('ACCEPTED')
        output=candidate if accepted else root
        # Structural fallback preserves the exact source AST even when validation is inconclusive.
        fallback=None if accepted else 'original_retained_after_'+gate['status']
        outputs[arm]={'candidate':candidate,'output':output,'gate':gate,'fallback':fallback,'metrics':metrics(output,ctx),
                      'candidate_metrics':metrics(candidate,ctx),'detail':detail,'candidate_was_explicit_root':candidate in roots}
        (out/(arm+'.tau')).write_text(metrics(output,ctx)['emitted']+'.\n')
    common_charge=charge(registry,normalization)
    for arm,result in outputs.items():
        gate=result['gate'];gate_cold=gate.get('cold_elapsed_s',gate['elapsed_s'])
        method_wall=result['detail'].get('method_wall_s',result['detail'].get('elapsed_s',0.))
        if arm=='native_sympy_portfolio':method_wall=outputs['sympy']['detail']['method_wall_s']
        if arm in ('semantic_list','recursive_congruence','semantic_graph','hybrid','hybrid_root_only'):
            native_charge=charge(registry,normalization,gate)
            accounted=registry['elapsed_s']+normalization['elapsed_s']+method_wall+gate_cold
            accounting='shared-transcript replay: full common construction assigned to each consumer; not independent online timing'
        elif arm.startswith('native'):
            native_charge=charge(normalization,registry['native_proposal_gate'],gate)
            accounted=normalization['elapsed_s']+(registry['native_proposal_gate'] or {}).get('elapsed_s',0.)+gate_cold
            if arm=='native_sympy_portfolio':
                native_gate=outputs['native_guarded']['gate'];sym_gate=outputs['sympy']['gate']
                native_charge=charge(normalization,registry['native_proposal_gate'],gate,native_gate,sym_gate)
                accounted=normalization['elapsed_s']+(registry['native_proposal_gate'] or {}).get('elapsed_s',0.)+method_wall+unique_gate_cold_cost(gate,native_gate,sym_gate)
            accounting='component accounting with first-emission cold receipt costs; portfolio pays both components, not an independent online measurement'
        else:
            native_charge=charge(gate);accounted=method_wall+gate_cold;accounting='method plus first-emission cold validation receipt; not independent online timing'
        result['accounting']={'description':accounting,'accounted_wall_s':accounted,'native_cold_charge':native_charge,'search_wall_s':method_wall}
    result={'case':row,'context':asdict(ctx),'profile':oracle.profile,'profile_key':oracle.profile_key,'original_metrics':metrics(root,ctx),
            'normalization_stdout_bytes':len(normalization['stdout'].encode()),
            'normalization_payload_bytes':len(re.sub(r'^%1:\s*','',normalization['stdout']).strip().encode()),
            'normalization_proposal_admission_status':admission_status,'parsed_native_metrics':native_detail['parsed_native_metrics'],'normalization':normalization,'normalization_parse_reason':parse_reason,
            'registry':registry,'arms':outputs,'method_order':operations,'final_gate_order':order,
            'native_summary':oracle.native.finish(),'elapsed_s':time.perf_counter()-start}
    write(out/'result.json',result);return result


def summary(rows):
    names=sorted(rows[0]['arms']) if rows else []
    arms={}
    for name in names:
        vals=[r['arms'][name] for r in rows]
        arms[name]={'expression_bytes':sum(x['metrics']['expression_bytes'] for x in vals),'tree_nodes':sum(x['metrics']['tree_nodes'] for x in vals),
                   'dag_nodes':sum(x['metrics']['dag_nodes'] for x in vals),'gate_statuses':dict(collections.Counter(x['gate']['status'] for x in vals)),
                   'fallbacks':sum(x['fallback'] is not None for x in vals),'search_wall_s':sum(x['accounting']['search_wall_s'] for x in vals),
                   'native_cold_charge_s':sum(x['accounting']['native_cold_charge']['native_wall_s'] for x in vals),
                   'component_accounted_wall_s':sum(x['accounting']['accounted_wall_s'] for x in vals),
                   'normalization_admission_statuses':dict(collections.Counter(x['detail'].get('proposal_admission_status') for x in vals if 'proposal_admission_status' in x['detail'])),
                   'normalization_retained_original':sum(x['detail'].get('retained_original_reason') is not None for x in vals)}
    comparisons={}
    for baseline in names:
        delta=[r['arms']['hybrid']['metrics']['expression_bytes']-r['arms'][baseline]['metrics']['expression_bytes'] for r in rows]
        comparisons[baseline]={'wins':sum(x<0 for x in delta),'ties':sum(x==0 for x in delta),'regressions':sum(x>0 for x in delta),'byte_difference':sum(delta)}
    return {'status':'COMPLETE','cases':len(rows),'arms':arms,'hybrid_vs':comparisons,'original_expression_bytes':sum(r['original_metrics']['expression_bytes'] for r in rows),
            'native_processes':sum(r['native_summary']['processes'] for r in rows),'actual_wall_s':sum(r['elapsed_s'] for r in rows),
            'normalization_admission_statuses':dict(collections.Counter(r['normalization_proposal_admission_status'] for r in rows)),
            'signature_statuses':dict(collections.Counter(s['status'] for r in rows for s in r['registry']['signatures'])),
            'proposal_gate_statuses':dict(collections.Counter(s['status'] for r in rows for s in r['registry']['proposal_receipts']))}

DEFAULT_CONFIG={'iterations':3,'enodes':1000,'native_timeout_s':5.,'sympy_timeout_s':5.,'sympy_max_propositions':8,
                'subtrees':64,'pairs':64,'bank_candidates':128,'matches_per_subtree':3}

def main():
    p=argparse.ArgumentParser();p.add_argument('--corpus',required=True);p.add_argument('--binary',required=True);p.add_argument('--out',required=True);p.add_argument('--limit',type=int);p.add_argument('--config');p.add_argument('--freeze');p.add_argument('--expect-freeze-sha256')
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    corpus=json.loads(Path(args.corpus).read_text());rows=corpus['cases'];config=DEFAULT_CONFIG.copy()
    if corpus['split']=='test' and not (args.freeze and args.expect_freeze_sha256):raise ValueError('heldout runs require an explicit frozen manifest and digest')
    if args.freeze:
        from freeze_protocol import verify
        verify(args.freeze,args.expect_freeze_sha256)
    if args.config:config.update(json.loads(Path(args.config).read_text()))
    if args.limit is not None:rows=rows[:args.limit]
    src=Path(__file__).parent
    manifest={'schema':'tau-study-run/v2','corpus_sha256':digest(args.corpus),'case_count':len(rows),'executed_case_digest':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),'config':config,'binary_sha256':digest(args.binary),
              'protocol_freeze_sha256':args.expect_freeze_sha256,'protocol_freeze_file':None if args.freeze is None else str(Path(args.freeze).resolve()),
              'binary_path':str(Path(args.binary).resolve()),'native_flags':list(FLAGS),'corpus_path':str(Path(args.corpus).resolve()),
              'source_sha256':{p.name:digest(p) for p in sorted(src.glob('*.py'))},'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'split':corpus['split']}
    write(out/'manifest-start.json',manifest);write(out/'corpus-executed.json',{'schema':corpus['schema'],'split':corpus['split'],'cases':rows});results=[]
    for i,row in enumerate(rows):
        result=run_case(row,args.binary,out/row['name'],config);results.append(result)
        print(json.dumps({'index':i,'case':row['name'],'bytes':{a:x['metrics']['expression_bytes'] for a,x in result['arms'].items()},'wall_s':result['elapsed_s']}),flush=True)
        write(out/'progress.json',summary(results))
    final=summary(results)
    final['source_unchanged']=manifest['source_sha256']=={p.name:digest(p) for p in sorted(src.glob('*.py'))}
    final['binary_unchanged']=manifest['binary_sha256']==digest(args.binary)
    final['case_binary_profiles_match']=all(r['profile']['binary_sha256']==manifest['binary_sha256'] and r['native_summary']['binary_sha256']==manifest['binary_sha256'] for r in results)
    if not all(final[k] for k in ('source_unchanged','binary_unchanged','case_binary_profiles_match')):final['status']='PROVENANCE_FAILED'
    write(out/'SUMMARY.json',final);print(json.dumps(final,indent=2))
    if final['status']!='COMPLETE':raise SystemExit(2)
if __name__=='__main__':main()
