"""Reproduce a post-hoc native-parser attribution sensitivity.

The frozen primary corpus and its 336 outcomes are unchanged. This presentation
script reads only the fully validated result set and writes only paper-local
artifacts. --check compares the existing JSON without overwriting it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
BASELINES=('native_guarded','native_sympy_portfolio','recursive_congruence','semantic_list')
TERM_TAGS={'zero','one','var','not','and','or','xor'}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def quantified(ast):
    return isinstance(ast,list) and (ast[0]=='exists' or any(quantified(c) for c in ast[1:] if isinstance(c,list)))

def stratum(row):
    ast=row['case']['original']
    if ast[0] in TERM_TAGS:return 'pure_term'
    return 'quantified' if quantified(ast) else 'quantifier_free_formula'

def summarize(rows):
    h=sum(r['arms']['hybrid']['metrics']['expression_bytes'] for r in rows)
    comparisons={}
    for arm in BASELINES:
        b=sum(r['arms'][arm]['metrics']['expression_bytes'] for r in rows)
        delta=[r['arms']['hybrid']['metrics']['expression_bytes']-r['arms'][arm]['metrics']['expression_bytes'] for r in rows]
        comparisons[arm]={'baseline_bytes':b,'byte_saving':b-h,
            'saving_pct':(b-h)/b*100 if b else 0.,
            'wins':sum(d<0 for d in delta),'ties':sum(d==0 for d in delta),'regressions':sum(d>0 for d in delta)}
    return {'cases':len(rows),'hybrid_bytes':h,'comparisons':comparisons}

def equivalent(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(a,b,rel_tol=1e-13,abs_tol=1e-13)
    return a==b

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    run=STUDY/'results/heldout-001'
    validation_path=STUDY/'results/heldout-001-validation.json'
    analysis_path=STUDY/'results/heldout-001-analysis.json'
    validation=json.loads(validation_path.read_text());analysis=json.loads(analysis_path.read_text())
    assert validation['status']=='VALIDATION_PASS' and analysis['status']=='COMPLETE'
    assert digest(run/'manifest-start.json')==validation['manifest_sha256']==analysis['run_manifest_sha256']
    paths=sorted(run.glob('*/result.json'));rows=[json.loads(p.read_text()) for p in paths]
    assert len(rows)==validation['case_count']==analysis['cases']==336
    unsupported=[r for r in rows if r['normalization_proposal_admission_status']=='PARSE_OR_NORMALIZATION_FAILED']
    supported=[r for r in rows if r not in unsupported]
    # In this completed campaign all excluded cases are parser grammar limits,
    # not native timeout, stderr, nonzero-exit, or solver-failure classifications.
    assert len(unsupported)==3 and len(supported)==333
    assert all(r['normalization_parse_reason']=='only term equality/inequality to literal zero is accepted' for r in unsupported)
    assert all(r['normalization']['returncode']==0 and not r['normalization']['timed_out'] and not r['normalization']['stderr'].strip() for r in unsupported)
    all_summary=summarize(rows);excluded_summary=summarize(unsupported)
    result={'status':'POSTHOC_ATTRIBUTION_SENSITIVITY',
        'scope':'Frozen primary unchanged; this diagnostic separates unsupported native output syntax from optimizer-attributable comparisons.',
        'all_336':all_summary,'supported_native_333':summarize(supported),'unsupported_native_3':excluded_summary,
        'excluded_cases':[{'name':r['case']['name'],'native_stdout':r['normalization']['stdout'],
            'reason':r['normalization_parse_reason'],'original_bytes':r['original_metrics']['expression_bytes'],
            'hybrid_bytes':r['arms']['hybrid']['metrics']['expression_bytes']} for r in unsupported],
        'families':{},'strata':{},'unsupported_share_of_total_savings_pct':{}}
    for family in sorted({r['case']['family'] for r in rows}):
        result['families'][family]={'all':summarize([r for r in rows if r['case']['family']==family]),
            'native_supported':summarize([r for r in supported if r['case']['family']==family])}
    for kind,count in (('pure_term',192),('quantifier_free_formula',36),('quantified',108)):
        subset=[r for r in rows if stratum(r)==kind];assert len(subset)==count
        result['strata'][kind]={'all':summarize(subset),'native_supported':summarize([r for r in supported if stratum(r)==kind])}
    for arm in ('native_guarded','native_sympy_portfolio'):
        result['unsupported_share_of_total_savings_pct'][arm]=excluded_summary['comparisons'][arm]['byte_saving']/all_summary['comparisons'][arm]['byte_saving']*100
    target=HERE/'native-parser-sensitivity.json'
    if args.check:
        assert equivalent(result,json.loads(target.read_text())),'existing sensitivity does not match completed raw rows'
    else:
        target.write_text(json.dumps(result,indent=2)+'\n')
        provenance={'schema':'tau-paper-parser-sensitivity-provenance/v1',
            'status':'POSTHOC_ATTRIBUTION_SENSITIVITY','frozen_primary_unchanged':True,
            'derived_file_sha256':digest(target),'script_sha256':digest(Path(__file__)),
            'input_sha256':{str(p.relative_to(STUDY)):digest(p) for p in [validation_path,analysis_path,run/'manifest-start.json',*paths]}}
        (HERE/'native-parser-sensitivity-provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','mode':'check' if args.check else 'write','cases':len(rows),'supported':len(supported),'unsupported':len(unsupported)}))

if __name__=='__main__':main()
