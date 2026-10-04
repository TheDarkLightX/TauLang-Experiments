"""Paper-local cold-inclusive reuse curves from the verified completed campaign."""
from pathlib import Path
import collections
import hashlib
import json
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/tau-paper-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent;STUDY=HERE.parent;ROOT=STUDY/'results'
summary=json.loads((ROOT/'reuse-001-summary.json').read_text());verification=json.loads((ROOT/'reuse-001-verification.json').read_text())
assert verification['status']=='VERIFIED' and summary['status']=='COMPLETE'
assert verification['runs']==len(summary['runs'])==30 and verification['requests']==7680
assert summary['freeze_sha256']==verification['freeze_sha256']
ARMS=('no_cache','exact_syntax','fixed_bank_signature','semantic_registry')
LABELS={'no_cache':'No cache','exact_syntax':'Exact memo','fixed_bank_signature':'Indexed bank','semantic_registry':'Semantic registry'}
COLOR={'no_cache':'#737373','exact_syntax':'#B56B20','fixed_bank_signature':'#27648B','semantic_registry':'#1F262B'}
DASH={'no_cache':'-','exact_syntax':'--','fixed_bank_signature':'-.','semantic_registry':':'}
MIXTURES=('100-0-0','50-50-0','25-25-50','0-0-100')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
 'axes.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,
 'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'})
fig,axes=plt.subplots(4,2,figsize=(7.0,8.4),sharex=True,sharey=True,layout='constrained')
for i,mix in enumerate(MIXTURES):
 for j,(sort,label) in enumerate((('term_tau','Terms'),('formula','Formulas'))):
  ax=axes[i,j];runs=[r for r in summary['runs'] if r['stream']==sort+'-'+mix]
  assert len(runs)==3
  for r in runs:
   for arm in ARMS:
    curve=r['curves'][arm];assert len(curve)==64
    ax.plot([p['requests'] for p in curve],[p['cumulative_wall_s'] for p in curve],
      color=COLOR[arm],linestyle=DASH[arm],alpha=.65,linewidth=1.05)
  ax.set_title(f'{label}  {mix.replace("-", "/")}',loc='left')
  ax.set_xlim(1,64);ax.set_ylim(0,13.2);ax.set_xticks([1,16,32,48,64]);ax.set_yticks([0,4,8,12])
  ax.grid(True,color='#E1E1E1',linewidth=.6);ax.set_axisbelow(True)
  if j==0:ax.set_ylabel('Cumulative seconds')
  if i==3:ax.set_xlabel('Request index')
handles=[Line2D([0],[0],color=COLOR[k],linestyle=DASH[k],lw=1.8,label=LABELS[k]) for k in ARMS]
fig.legend(handles=handles,loc='outside upper center',ncol=4,frameon=False,fontsize=9)
(HERE/'figures').mkdir(exist_ok=True)
for ext in ('svg','pdf','png'):fig.savefig(HERE/'figures'/f'reuse_cumulative_wall.{ext}',dpi=190,bbox_inches='tight')
plt.close(fig)
analysis=json.loads((ROOT/'reuse-001-ANALYSIS.json').read_text())
assert analysis['status']=='VERIFIED_COMPLETE'
novelty=analysis['stream_novelty']
totals={}
for arm in ARMS:
 status=collections.Counter()
 for r in summary['runs']:status.update(r['arms'][arm]['gate_statuses'])
 totals[arm]={'requests':1920,'gate_statuses':dict(status),**{k:sum(r['arms'][arm][k] for r in summary['runs']) for k in ('total_wall_s','native_processes','final_certificate_hits','output_bytes')}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backing={'schema':'tau-paper-reuse-displays/v1','sources_sha256':{str(p.relative_to(STUDY)):sha(p) for p in (ROOT/'reuse-001-summary.json',ROOT/'reuse-001-verification.json',ROOT/'reuse-001-ANALYSIS.json')},
 'totals':totals,'novelty':novelty,'runs':summary['runs'],
 'timing_caveat':'Concurrent paper figure rendering approximately 2026-10-04T04:48:53.5Z through 2026-10-04T04:49:01.5Z (8.9 seconds) overlapped repetition 1 formula-25-25-50. All repetitions retained; no causal timing correction or excluded rerun.'}
(HERE/'reuse-display-data.json').write_text(json.dumps(backing,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','runs':len(summary['runs']),'totals':totals,'novelty':novelty},indent=2))
