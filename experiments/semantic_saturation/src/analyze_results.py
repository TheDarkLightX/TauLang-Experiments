"""Prespecified descriptive analysis; no p-value selection or post-hoc filtering."""
from __future__ import annotations
from pathlib import Path
import argparse,collections,hashlib,json,random,statistics
from run_study import write,summary
from validate_run import validate
from engine import free_vars,render
from run_study import context

BOOTSTRAP_SEED=2026100401
BOOTSTRAP_REPLICATES=2000
COMPARISONS=[('hybrid','native_guarded'),('hybrid','native_sympy_portfolio'),('hybrid','semantic_list'),('hybrid','recursive_congruence'),('semantic_graph','recursive_congruence'),('hybrid','hybrid_root_only')]


def interval(rows,a,b):
    groups=collections.defaultdict(list)
    for r in rows:groups[r['case']['family']].append(r['arms'][a]['metrics']['expression_bytes']-r['arms'][b]['metrics']['expression_bytes'])
    rng=random.Random(BOOTSTRAP_SEED);values=[]
    for _ in range(BOOTSTRAP_REPLICATES):
        sample=[rng.choice(xs) for family,xs in sorted(groups.items()) for _ in xs]
        values.append(statistics.mean(sample))
    values.sort();delta=[x for xs in groups.values() for x in xs]
    return {'mean_paired_byte_difference':statistics.mean(delta),'median_paired_byte_difference':statistics.median(delta),
            'stratified_bootstrap_mean_difference_95pct':[values[49],values[1949]],'bootstrap_seed':BOOTSTRAP_SEED,'bootstrap_replicates':BOOTSTRAP_REPLICATES,
            'scope':'finite synthetic generator corpus uncertainty; not a real-world workload population interval'}


def analyze(directory):
    validation=validate(directory)
    base=Path(directory);manifest=json.loads((base/'manifest-start.json').read_text());rows=[json.loads(p.read_text()) for p in sorted(base.glob('*/result.json'))]
    if len(rows)!=manifest['case_count']:raise ValueError('incomplete run')
    result=summary(rows);result['validation']=validation;result['run_manifest_sha256']=hashlib.sha256((base/'manifest-start.json').read_bytes()).hexdigest()
    result['families']={f:summary([r for r in rows if r['case']['family']==f]) for f in sorted({r['case']['family'] for r in rows})}
    result['intervals']={a+'_vs_'+b:interval(rows,a,b) for a,b in COMPARISONS}
    result['scope_and_caps']={'declared_variable_counts':dict(collections.Counter(len(r['case']['free']) for r in rows)),
      'used_free_variable_counts':dict(collections.Counter(len(free_vars(_tuple(r['case']['original']))) for r in rows)),
      'hybrid_stop_reasons':dict(collections.Counter(r['arms']['hybrid']['detail'].get('stop_reason') for r in rows)),
      'semantic_graph_stop_reasons':dict(collections.Counter(r['arms']['semantic_graph']['detail'].get('stop_reason') for r in rows)),
      'sympy_statuses':dict(collections.Counter(r['arms']['sympy']['detail'].get('status') for r in rows)),
      'registry_subtree_caps':sum(r['registry']['subtree_cap_reached'] for r in rows),'registry_pair_caps':sum(r['registry']['pair_cap_reached'] for r in rows)}
    result['alternative_cost_sensitivity']={'metric':'untyped fully parenthesized render bytes; secondary display-only sensitivity, not the checked emitted program metric','totals':{arm:sum(len(render(_tuple(r['arms'][arm]['output']),context(r['case'])).encode()) for r in rows) for arm in sorted(rows[0]['arms'])}}
    result['constant_outputs']={arm:sum(r['arms'][arm]['output'][0] in ('zero','one','T','F') for r in rows) for arm in sorted(rows[0]['arms'])}
    result['quantifier_pattern_counts']=dict(collections.Counter(quantifier_pattern(r['case']['original']) for r in rows if r['case']['family']=='mixed_quantifier_pair_holdout'))
    result['composition']={a:{'outputs_absent_from_explicit_root_menu':sum(not r['arms'][a]['candidate_was_explicit_root'] for r in rows),
        'strict_wins_over_root_menu':sum(r['arms'][a]['metrics']['expression_bytes']<r['arms']['semantic_list']['metrics']['expression_bytes'] for r in rows)} for a in ('recursive_congruence','semantic_graph','hybrid')}
    result['representation_byte_disagreements']=[r['case']['name'] for r in rows if r['arms']['semantic_graph']['metrics']['expression_bytes']!=r['arms']['recursive_congruence']['metrics']['expression_bytes']]
    result['mandatory_nonclaims']=['Byte nonregression is a guarded selection invariant.','Generic semantic egraphs, support-based QE, and caching have prior art.',
        'Hybrid-vs-congruence differences include extra rewrite-generated alternatives.','Shared-transcript component timing is not independent online optimizer timing.',
        'Support exactness theorem is for atomless set subalgebras; Python and Tau implementation refinement remains tested, not proved.',
        'No general compiler execution speedup, full-Tau coverage, global minimality, or scholarly acceptance is claimed.']
    return result

def quantifier_pattern(ast):
    if ast[0]=='exists':return 'exists/'+quantifier_pattern(ast[2])
    if ast[0]=='notF' and ast[1][0]=='exists' and ast[1][2][0]=='notF':return 'forall/'+quantifier_pattern(ast[1][2][1])
    return 'body'


def _tuple(x):return tuple(_tuple(v) for v in x) if isinstance(x,list) else x

def main():
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);args=p.parse_args();write(args.out,analyze(args.run))
if __name__=='__main__':main()
