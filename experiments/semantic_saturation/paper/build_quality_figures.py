"""Render paper-only figures and tables from completed, validated study evidence.

No study source, freeze, input corpus, or raw result is modified. This script is
an artifact presentation step, not a new optimizer or a changed analysis.
"""
from __future__ import annotations
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
OUT = HERE / 'figures'
OUT.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', '/tmp/tau-paper-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ANALYSIS = STUDY / 'results/heldout-001-analysis.json'
VALIDATION = STUDY / 'results/heldout-001-validation.json'
RUN = STUDY / 'results/heldout-001'
a = json.loads(ANALYSIS.read_text())
v = json.loads(VALIDATION.read_text())
assert v['status'] == 'VALIDATION_PASS' and a['status'] == 'COMPLETE'
assert a['cases'] == v['case_count'] == 336 and v['final_gates'] == 3360
paths = sorted(RUN.glob('*/result.json'))
rows = [json.loads(p.read_text()) for p in paths]
assert len(rows) == 336
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert a['run_manifest_sha256'] == sha(RUN / 'manifest-start.json') == v['manifest_sha256']

ORDER = ['native_reserialized', 'native_guarded', 'rewrite_guarded', 'semantic_list',
         'recursive_congruence', 'semantic_graph', 'hybrid', 'hybrid_root_only',
         'sympy', 'native_sympy_portfolio']
LABELS = {'native_reserialized': 'Native reserialized', 'native_guarded': 'Native guarded',
          'rewrite_guarded': 'Rewrite guarded', 'semantic_list': 'Semantic root list',
          'recursive_congruence': 'Scoped recursive congruence', 'semantic_graph': 'Semantic graph without rewrites',
          'hybrid': 'Hybrid', 'hybrid_root_only': 'Root-only hybrid',
          'sympy': 'SymPy', 'native_sympy_portfolio': 'Native + SymPy portfolio'}
FAMILIES = ['random_term', 'random_formula', 'quantified_random', 'factoring_composition',
            'multiplexer_holdout', 'parity_holdout', 'proper_split_composition_holdout',
            'mixed_quantifier_pair_holdout']
FLABEL = {'random_term': 'Random terms', 'random_formula': 'Random formulas',
          'quantified_random': 'Quantified random', 'factoring_composition': 'Factoring composition',
          'multiplexer_holdout': 'Multiplexer holdout', 'parity_holdout': 'Parity holdout',
          'proper_split_composition_holdout': 'Proper-split holdout',
          'mixed_quantifier_pair_holdout': 'Mixed-quantifier holdout'}
BLUE = '#27648B'
ORANGE = '#B56B20'
GRAY = '#6D747A'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.titlesize': 11, 'axes.labelsize': 10, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.edgecolor': '#444444', 'text.color': '#222222',
    'axes.labelcolor': '#222222', 'xtick.color': '#333333', 'ytick.color': '#333333',
    'svg.fonttype': 'none', 'pdf.fonttype': 42, 'figure.facecolor': 'white',
    'savefig.facecolor': 'white'})

def save(fig, name):
    for ext in ('svg', 'pdf', 'png'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=190, bbox_inches='tight')
    plt.close(fig)

# Exact tabular backing data is independently checked against completed rows.
for arm in ORDER:
    assert sum(r['arms'][arm]['metrics']['expression_bytes'] for r in rows) == a['arms'][arm]['expression_bytes']
    assert sum(r['arms'][arm]['metrics']['tree_nodes'] for r in rows) == a['arms'][arm]['tree_nodes']
    assert sum(r['arms'][arm]['metrics']['dag_nodes'] for r in rows) == a['arms'][arm]['dag_nodes']

fig, ax = plt.subplots(figsize=(7.0, 5.0), layout='constrained')
vals = [a['arms'][name]['expression_bytes'] for name in ORDER]
colors = [BLUE if name == 'hybrid' else GRAY for name in ORDER]
ax.barh(range(len(ORDER)), vals, height=.62, color=colors)
ax.set_yticks(range(len(ORDER)), [LABELS[n] for n in ORDER]); ax.invert_yaxis()
ax.set_xlim(0, max(vals)*1.14)
ax.set_xlabel('Total typed UTF-8 expression bytes across 336 cases')
ax.set_title('Output size under one common serializer', loc='left', pad=14)
ax.xaxis.grid(True, color='#E2E2E2', linewidth=.65); ax.set_axisbelow(True)
for i, value in enumerate(vals): ax.text(value+max(vals)*.012, i, f'{value:,}', va='center', fontsize=10)
save(fig, 'quality_totals')

comparisons = [('native_sympy_portfolio', 'Hybrid minus native + SymPy portfolio'),
               ('recursive_congruence', 'Hybrid minus scoped recursive congruence')]
all_deltas = [r['arms']['hybrid']['metrics']['expression_bytes'] - r['arms'][base]['metrics']['expression_bytes']
              for base,_ in comparisons for r in rows]
lo,hi = min(all_deltas),max(all_deltas)
pad = max(8,(hi-lo)*.06)
fig, axes = plt.subplots(2,1,figsize=(7.0,8.3), sharey=True, sharex=True, layout='constrained')
rng = random.Random(2026100401)
for ax,(base,title) in zip(axes,comparisons):
    ax.axvline(0,color='#333333',linewidth=1)
    for y,fam in enumerate(FAMILIES):
        selected=[r for r in rows if r['case']['family']==fam]
        for r in selected:
            d=r['arms']['hybrid']['metrics']['expression_bytes']-r['arms'][base]['metrics']['expression_bytes']
            capped=r['arms']['hybrid']['detail'].get('stop_reason')=='node_limit'
            color=BLUE if d<0 else ORANGE if d>0 else GRAY
            ax.scatter(d,y+rng.uniform(-.19,.19),s=15,marker='^' if r['normalization_proposal_admission_status']=='PARSE_OR_NORMALIZATION_FAILED' else 'x' if capped else 'o',
                       c=color,alpha=.65,linewidths=.65)
    ax.set_title(title,loc='left',pad=12)
    ax.set_xlim(lo-pad,hi+pad)
    ax.set_xlabel('Paired typed-byte difference (negative favors hybrid)')
    ax.xaxis.grid(True,color='#E2E2E2',linewidth=.65); ax.set_axisbelow(True)
axes[0].set_yticks(range(len(FAMILIES)), [f'{FLABEL[f]} (n={a["families"][f]["cases"]})' for f in FAMILIES])
axes[0].invert_yaxis()
fig.legend(handles=[Line2D([0],[0],marker='o',linestyle='None',color=GRAY,label='Uncapped, parser supported'), Line2D([0],[0],marker='x',linestyle='None',color=GRAY,label='Hybrid node cap'), Line2D([0],[0],marker='^',linestyle='None',color=GRAY,label='Native parser unsupported')], loc='outside upper center', ncol=3, frameon=False, fontsize=8)
save(fig,'paired_quality_differences')

pairs=collections.Counter((r['arms']['recursive_congruence']['metrics']['expression_bytes'],
                           r['arms']['semantic_graph']['metrics']['expression_bytes']) for r in rows)
assert all(x==y for x,y in pairs)
assert a['representation_byte_disagreements']==[]
maxcost=max(x for x,y in pairs)
fig,ax=plt.subplots(figsize=(6.5,6.0),layout='constrained')
ax.plot([0,maxcost*1.06],[0,maxcost*1.06],color='#444444',linestyle='--',linewidth=1,label='Equal byte cost')
for (x,y),count in sorted(pairs.items()):
    ax.scatter(x,y,s=18+16*math.log2(count),facecolors='white',edgecolors=BLUE,linewidths=1.1,zorder=3)
ax.set_xlim(0,maxcost*1.07); ax.set_ylim(0,maxcost*1.07); ax.set_aspect('equal')
ax.set_xlabel('Scoped recursive congruence typed bytes per case')
ax.set_ylabel('No-rewrite semantic graph typed bytes per case')
ax.set_title('Representation comparison on the held-out corpus',loc='left',pad=12)
ax.text(.04,.94,'336 / 336 byte ties\n0 semantic-graph cap stops\n70 different output ASTs',transform=ax.transAxes,va='top',fontsize=11)
ax.grid(True,color='#E2E2E2',linewidth=.65); ax.set_axisbelow(True)
save(fig,'representation_parity')

source_records={str(p.relative_to(STUDY)):sha(p) for p in [ANALYSIS,VALIDATION,RUN/'manifest-start.json',*paths]}
backing={'schema':'tau-paper-quality-displays/v1','sources_sha256':source_records,
 'case_count':len(rows),'arms':{k:a['arms'][k] for k in ORDER},
 'families':{f:{'cases':a['families'][f]['cases'],'bytes':{k:a['families'][f]['arms'][k]['expression_bytes'] for k in ORDER},
                  'hybrid_vs':a['families'][f]['hybrid_vs']} for f in FAMILIES},
 'intervals':a['intervals'],'composition':a['composition'],'scope_and_caps':a['scope_and_caps'],
 'exact_ast_disagreements':sum(r['arms']['recursive_congruence']['output']!=r['arms']['semantic_graph']['output'] for r in rows),
 'case_bytes':[{'case':r['case']['name'],'family':r['case']['family'],
                'bytes':{k:r['arms'][k]['metrics']['expression_bytes'] for k in ORDER},
                'hybrid_stop_reason':r['arms']['hybrid']['detail'].get('stop_reason'),
                'semantic_graph_stop_reason':r['arms']['semantic_graph']['detail'].get('stop_reason')} for r in rows]}
(HERE/'quality-display-data.json').write_text(json.dumps(backing,indent=2,sort_keys=True)+'\n')
lines=['# Validated heldout quality tables','',
 'Source: completed `heldout-001` run, validated analysis and validation JSON. All methods have 336 outcomes. W/T/L means hybrid wins/ties/losses against the named row. Costs are typed UTF-8 expression bytes.','',
 '| Method | Bytes | AST nodes | Structural DAG nodes | Changed accepted | Retained identity | Hybrid W/T/L |',
 '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
for k in ORDER:
    z=a['arms'][k];c=a['hybrid_vs'][k]
    lines.append(f'| {LABELS[k]} | {z["expression_bytes"]:,} | {z["tree_nodes"]:,} | {z["dag_nodes"]:,} | {z["gate_statuses"].get("ACCEPTED",0)} | {z["gate_statuses"].get("ACCEPTED_IDENTITY",0)} | {c["wins"]}/{c["ties"]}/{c["regressions"]} |')
lines+=['','## Family totals','',
 '| Family | Cases | Native guarded | Native + SymPy | Recursive congruence | Hybrid | Hybrid vs portfolio W/T/L |',
 '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
for f in FAMILIES:
    z=a['families'][f];c=z['hybrid_vs']['native_sympy_portfolio']; b=z['arms']
    lines.append(f'| {FLABEL[f]} | {z["cases"]} | {b["native_guarded"]["expression_bytes"]:,} | {b["native_sympy_portfolio"]["expression_bytes"]:,} | {b["recursive_congruence"]["expression_bytes"]:,} | {b["hybrid"]["expression_bytes"]:,} | {c["wins"]}/{c["ties"]}/{c["regressions"]} |')
lines+=['','## Prespecified paired differences','',
 'Every median is zero. Intervals are 95% family-stratified bootstrap intervals for the mean on this synthetic corpus, with 2,000 fixed-seed resamples. They are not population generalization intervals.','',
 '| First arm minus second arm | Mean bytes | Median bytes | 95% interval for mean |',
 '| --- | ---: | ---: | --- |']
for key,z in a['intervals'].items():
    first,second=key.split('_vs_');lo,hi=z['stratified_bootstrap_mean_difference_95pct']
    lines.append(f'| {LABELS[first]} minus {LABELS[second]} | {z["mean_paired_byte_difference"]:.3f} | {z["median_paired_byte_difference"]:.0f} | [{lo:.3f}, {hi:.3f}] |')
lines+=['','## Descriptive component accounting','',
 'These are shared-transcript charges, not independent online method timings. Components are nested; columns must not be summed. The sum of per-case harness wall times was 633.586 seconds, with 10,148 native processes across the campaign.','',
 '| Method | Search seconds | Cold native charge seconds | Component-accounted seconds |',
 '| --- | ---: | ---: | ---: |']
for k in ORDER:
    z=a['arms'][k]
    lines.append(f'| {LABELS[k]} | {z["search_wall_s"]:.3f} | {z["native_cold_charge_s"]:.3f} | {z["component_accounted_wall_s"]:.3f} |')
(HERE/'QUALITY_TABLES.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'case_count':len(rows),'figures':[str(p.relative_to(HERE)) for p in sorted(OUT.iterdir())],
                  'backing_data_sha256':sha(HERE/'quality-display-data.json')},indent=2))
