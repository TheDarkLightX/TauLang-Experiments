"""Replay publication-critical byte, receipt, scope, and source-manifest invariants."""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import argparse,hashlib,json,math,re
import engine as E
from checked_registry import comparison,validate_context,FORM_LIMITS,TERM_LIMITS
import support_oracle as S
from native_oracle import exact_truth,typed_render,FLAGS
from typed_parser import parse_emitted
from run_study import tuple_tree,context,digest,summary,write
from study_core import metrics,parse_native


def need(condition,message):
    if not condition:raise ValueError(message)


def validate(directory,*,check_source=True):
    base=Path(directory);manifest=json.loads((base/'manifest-start.json').read_text());stored=json.loads((base/'SUMMARY.json').read_text())
    need(stored['status']=='COMPLETE','run incomplete or provenance failed')
    if manifest['split']=='test':
        from freeze_protocol import verify
        freeze=Path(manifest['protocol_freeze_file'])
        if not freeze.exists():freeze=Path(__file__).parent.parent/'FREEZE.json'
        verify(freeze,manifest['protocol_freeze_sha256'])
    for key in ('source_unchanged','binary_unchanged','case_binary_profiles_match'):need(stored.get(key) is True,'missing/passing provenance '+key)
    if check_source:
        current={p.name:digest(p) for p in Path(__file__).parent.glob('*.py')}
        need(manifest['source_sha256']==current,'current source differs from executed source')
    corpus=json.loads((base/'corpus-executed.json').read_text());cases=corpus['cases']
    need(hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()==manifest['executed_case_digest'],'executed corpus digest mismatch')
    original_corpus=Path(manifest['corpus_path'])
    if not original_corpus.exists():original_corpus=Path(__file__).parent.parent/'corpora'/Path(manifest['corpus_path']).name
    need(original_corpus.exists() and digest(original_corpus)==manifest['corpus_sha256'],'original corpus digest mismatch')
    source_cases=json.loads(original_corpus.read_text())['cases'];need(cases==source_cases[:len(cases)],'executed rows do not match ordered original corpus')
    expected_cases={c['name']:c for c in cases};need(len(expected_cases)==len(cases),'duplicate case names')
    need(manifest['native_flags']==list(FLAGS),'native flags mismatch')
    rows=[];gates=0;changed=0;fallbacks=0;pairs=0
    for path in sorted(base.glob('*/result.json')):
        r=json.loads(path.read_text());rows.append(r);need(r['case']==expected_cases.get(path.parent.name),'case bytes differ from frozen corpus')
        ctx=context(r['case']);validate_context(ctx);root=tuple_tree(r['case']['original'])
        need(json.dumps(r['context'],sort_keys=True)==json.dumps(asdict(ctx),sort_keys=True),'stored context mismatch')
        need(r['original_metrics']==metrics(root,ctx),'original metrics mismatch')
        need(r['profile']['flags']==list(FLAGS),'profile flags mismatch')
        need((r['profile']['theory'],r['profile']['descriptor'],r['profile']['constants'],r['profile']['temporal'])==('nontrivialABA','tau',['0','1'],'none'),'profile semantic scope mismatch')
        need(r['profile']['timeout_s']==manifest['config']['native_timeout_s'],'profile timeout mismatch')
        need(r['profile']['formula_limits']==asdict(FORM_LIMITS) and r['profile']['term_limits']==asdict(TERM_LIMITS),'profile limits mismatch')
        need(r['profile']['support_source_sha256']==digest(S.__file__),'support source/profile mismatch')
        need(hashlib.sha256(json.dumps(r['profile'],sort_keys=True).encode()).hexdigest()==r['profile_key'],'profile key mismatch')
        need(r['profile']['binary_sha256']==manifest['binary_sha256'],'case binary/profile mismatch')
        need(r['native_summary']['binary_sha256']==manifest['binary_sha256'],'summary binary mismatch')
        raw={}
        for p in sorted((path.parent/'native').glob('*.json')):
            if p.name=='SUMMARY.json':continue
            receipt=json.loads(p.read_text());need(receipt['binary_sha256']==manifest['binary_sha256'],'receipt binary mismatch')
            need(type(receipt['elapsed_s']) in (float,int) and math.isfinite(receipt['elapsed_s']) and receipt['elapsed_s']>=0,'invalid native duration')
            need(receipt['truth']==exact_truth(receipt),'receipt truth parser mismatch')
            need(receipt['argv']==[manifest['binary_path'],*FLAGS,'-e',receipt['command']],'receipt argv mismatch')
            need(receipt['timeout_s']==manifest['config']['native_timeout_s'],'receipt timeout mismatch')
            need(receipt.get('TAU_environment_removed') is True,'unfixed native environment')
            need(receipt['ordinal'] not in raw,'duplicate receipt ordinal');raw[receipt['ordinal']]=receipt
        norm=r['normalization']
        need(norm==raw[norm['ordinal']],'normalization raw binding mismatch')
        need(norm['command']=='normalize '+typed_render(root,ctx),'normalization exact command mismatch')
        need(r['normalization_stdout_bytes']==len(norm['stdout'].encode()),'native stdout byte mismatch')
        need(r['normalization_payload_bytes']==len(re.sub(r'^%1:\s*','',norm['stdout']).strip().encode()),'native payload byte mismatch')
        parsed=None
        if norm['returncode']==0 and not norm['stderr'].strip() and not norm['timed_out']:
            try:parsed=parse_native(norm['stdout'],ctx.V,E.sort_of(root,ctx))
            except (ValueError,RecursionError):pass
        need(r['parsed_native_metrics']==(None if parsed is None else metrics(parsed,ctx)),'parsed native metric mismatch')
        native_summary=r['native_summary']
        expected_native={'binary':manifest['binary_path'],'binary_sha256':manifest['binary_sha256'],
            'timeout_s':manifest['config']['native_timeout_s'],'processes':len(raw),
            'timeouts':sum(q['timed_out'] for q in raw.values()),'parse_or_unknown':sum(q['truth']=='UNKNOWN' for q in raw.values()),
            'native_wall_s':sum(q['elapsed_s'] for q in raw.values())}
        for key,value in expected_native.items():need(native_summary[key]==value,'native summary mismatch '+key)
        need(native_summary==json.loads((path.parent/'native/SUMMARY.json').read_text()),'native summary file mismatch')
        def numeric(value,label):
            need(type(value) in (float,int) and math.isfinite(value) and value>=0,'invalid measured duration '+label)
        def charge_from(*objects):
            found={}
            def visit(o):
                if isinstance(o,dict):
                    if all(k in o for k in ('ordinal','command','elapsed_s','binary_sha256')):
                        need(o==raw[o['ordinal']],'accounting receipt cross-link mismatch');found[o['ordinal']]=raw[o['ordinal']]
                    else:
                        for v in o.values():visit(v)
                elif isinstance(o,(list,tuple)):
                    for v in o:visit(v)
            for o in objects:visit(o)
            return {'native_processes':len(found),'native_wall_s':sum(v['elapsed_s'] for v in found.values()),'ordinals':sorted(found)}
        def gate_cold(g):
            value=g.get('cold_elapsed_s',g['elapsed_s']);numeric(value,'cold gate')
            native=g.get('native',{})
            if 'forward' in native and 'reverse' in native:need(value+1e-8>=native['forward']['elapsed_s']+native['reverse']['elapsed_s'],'cold gate below native receipt durations')
            return value
        def unique_cold(gs):
            seen=set();total=0.
            for i,g in enumerate(gs):
                n=g.get('native',{});key=(n['forward']['binary_sha256'],n['forward']['ordinal'],n['reverse']['ordinal']) if 'forward' in n and 'reverse' in n else ('uncached',i)
                if key not in seen:seen.add(key);total+=gate_cold(g)
            return total
        registry=r['registry'];numeric(registry['elapsed_s'],'registry')
        need(registry['elapsed_s']+1e-8>=charge_from(registry)['native_wall_s'],'registry below consumed native durations')
        for arm_name,arm_value in r['arms'].items():
            gate=arm_value['gate'];detail=arm_value['detail'];cold=gate_cold(gate)
            method=detail.get('method_wall_s',detail.get('elapsed_s',0.));numeric(method,'method')
            if 'elapsed_s' in detail:need(method+1e-8>=detail['elapsed_s'],'outer method below inner method duration')
            if 'wall_seconds' in detail:need(method+1e-8>=detail['wall_seconds'],'outer method below SymPy duration')
            if arm_name=='native_sympy_portfolio':method=r['arms']['sympy']['detail']['method_wall_s']
            if arm_name in ('semantic_list','recursive_congruence','semantic_graph','hybrid','hybrid_root_only'):
                expected_charge=charge_from(registry,norm,gate);accounted=registry['elapsed_s']+norm['elapsed_s']+method+cold
            elif arm_name.startswith('native'):
                proposal=registry['native_proposal_gate'];expected_charge=charge_from(norm,proposal,gate)
                accounted=norm['elapsed_s']+(proposal or {}).get('elapsed_s',0.)+cold
                if arm_name=='native_sympy_portfolio':
                    ng=r['arms']['native_guarded']['gate'];sg=r['arms']['sympy']['gate']
                    expected_charge=charge_from(norm,proposal,gate,ng,sg)
                    accounted=norm['elapsed_s']+(proposal or {}).get('elapsed_s',0.)+method+unique_cold([gate,ng,sg])
            else:expected_charge=charge_from(gate);accounted=method+cold
            need(arm_value['accounting']['native_cold_charge']==expected_charge,'native accounting mismatch '+arm_name)
            need(arm_value['accounting']['search_wall_s']==method,'method accounting mismatch '+arm_name)
            need(arm_value['accounting']['accounted_wall_s']==accounted,'component accounting mismatch '+arm_name)
        def receipts(gate,left,right,emitted):
            sort=E.sort_of(left,ctx)
            if emitted:
                a,b=typed_render(left,ctx),typed_render(right,ctx)
                if sort!='formula':a,b=f'(({a}) ^ ({b})) = 0','T'
            else:
                if sort!='formula':left,right=('eq0',('xor',left,right)),('T',)
                a,b=E.render(left,ctx),E.render(right,ctx)
            names=', '.join(f'{n} : tau' for n in ctx.V);prefix=f'all {names} ' if names else ''
            commands={'forward':f'normalize {prefix}(({a}) -> ({b}))','reverse':f'normalize {prefix}(({b}) -> ({a}))'}
            need(gate['native']['forward']['ordinal']!=gate['native']['reverse']['ordinal'],'native directions must be separate invocation receipts')
            for d in ('forward','reverse'):
                q=gate['native'][d];need(q==raw[q['ordinal']],'embedded native receipt mismatch')
                need(exact_truth(q)=='T','missing exact native truth')
                need(q['command']==commands[d],'native command does not certify exact AST/context/direction')
        for pair in r['registry']['pairs']:
            l,h=tuple_tree(pair['left']),tuple_tree(pair['right']);need(pair['scope_key']==ctx.key,'pair scope mismatch')
            support=comparison(l,h,ctx);need(support.equivalent,'pair independent support replay');pairs+=1
            matching=[x for x in r['registry']['proposal_receipts'] if tuple_tree(x.get('left'))==l and tuple_tree(x.get('right'))==h and x.get('status')=='ACCEPTED']
            need(bool(matching),'pair lacks accepted proposal receipt');need(json.dumps(matching[0]['support'],sort_keys=True)==json.dumps(asdict(support),sort_keys=True),'proposal support receipt mismatch');need(matching[0]['context_key']==ctx.key and matching[0]['profile_key']==r['profile_key'],'pair receipt context/profile mismatch');receipts(matching[0],l,h,False)
        for name,arm in r['arms'].items():
            out=tuple_tree(arm['output']);candidate=tuple_tree(arm['candidate']);g=arm['gate'];gates+=1
            need(arm['metrics']==metrics(out,ctx),'output metrics mismatch')
            need(arm['candidate_metrics']==metrics(candidate,ctx),'candidate metrics mismatch')
            emitted=(path.parent/(name+'.tau')).read_text();need(emitted==typed_render(out,ctx)+'.\n','emitted file mismatch')
            need(parse_emitted(emitted[:-2],ctx.V)==out,'typed emitted parser mismatch')
            if g['status'] in ('ACCEPTED','ACCEPTED_IDENTITY'):
                need(g.get('structural_identity')==(candidate==root),'identity flag mismatch')
                need(g['status']==('ACCEPTED_IDENTITY' if candidate==root else 'ACCEPTED'),'identity status mismatch')
                need(out==candidate,'accepted candidate changed');need(g.get('roundtrip_ast_equal') is True,'missing roundtrip assertion');receipts(g,root,candidate,True)
                if out!=root:
                    support=comparison(root,out,ctx);need(support.equivalent,'changed output support replay');changed+=1
                    need(json.dumps(g['support'],sort_keys=True)==json.dumps(asdict(support),sort_keys=True),'final support receipt mismatch')
                else:need(g.get('structural_identity') is True and g.get('support') is None,'identity mislabeled')
            else:
                need(g['status'] in ('DIFFERENT','UNKNOWN','EMITTER_ROUNDTRIP_FAILED','REJECTED_INTERFACE','REJECTED_SUPPORT_DIFFERENT','REJECTED_SUPPORT_UNKNOWN','REJECTED_SUPPORT_REJECTED'),'unknown gate status')
                need(out==root,'failed gate did not retain original');fallbacks+=1
            if name!='native_reserialized':need(arm['metrics']['expression_bytes']<=r['original_metrics']['expression_bytes'],'guarded size regression')
    need(len(rows)==manifest['case_count'],'case count mismatch')
    recomputed=summary(rows)
    for key,value in recomputed.items():need(stored[key]==value,'summary mismatch '+key)
    return {'status':'VALIDATION_PASS','case_count':len(rows),'final_gates':gates,'transformed_outputs_rechecked':changed,'fallbacks_verified':fallbacks,
            'checked_pairs_replayed':pairs,'native_processes_launched':0,'native_evidence':'strict replay of retained raw receipts, not new native invocation',
            'source_checked':check_source,'manifest_sha256':digest(base/'manifest-start.json')}

def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);p.add_argument('--historical-source',action='store_true');a=p.parse_args();write(a.out,validate(a.run,check_source=not a.historical_source))
if __name__=='__main__':main()
