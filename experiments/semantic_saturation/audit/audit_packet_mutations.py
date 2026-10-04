"""Local scientific-evidence mutations; no solver or external service runs.
Each mutation operates only on a fresh copy of a two-case development packet.
"""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import validate_run as V,run_study as Q,native_oracle as N,study_core as C
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sourcehash=sha(a.source/'validate_run.py')
# A passing unmutated control is mandatory, otherwise rejection is uninterpretable.
control=V.validate(a.run,check_source=False)

def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def rowfile(d):return sorted(d.glob('*/result.json'))[0]
def loadrow(d):
 p=rowfile(d);return p,json.loads(p.read_text())
def recalc(d):
 rows=[json.loads(p.read_text()) for p in sorted(d.glob('*/result.json'))];old=json.loads((d/'SUMMARY.json').read_text());old.update(Q.summary(rows));write(d/'SUMMARY.json',old)
def mutate_gate(d,mode):
 p,r=loadrow(d);g=r['arms']['hybrid']['gate']
 if mode=='reuse_forward':g['native']['reverse']=copy.deepcopy(g['native']['forward'])
 if mode=='swap_directions':g['native']['forward'],g['native']['reverse']=g['native']['reverse'],g['native']['forward']
 if mode=='missing_reverse':del g['native']['reverse']
 write(p,r)
def rewrite_record(d,field,value):
 p,r=loadrow(d);q=copy.deepcopy(r['arms']['hybrid']['gate']['native']['forward']);ordinal=q['ordinal'];q[field]=value(q[field]) if callable(value) else value
 if field=='command':q['argv'][-1]=q['command']
 def walk(x):
  if isinstance(x,dict):
   if x.get('ordinal')==ordinal and 'command' in x:return copy.deepcopy(q)
   return {k:walk(v) for k,v in x.items()}
  if isinstance(x,list):return [walk(v) for v in x]
  return x
 raw=p.parent/'native'/f'{ordinal:04}.json';write(raw,q);write(p,walk(r))
def field_row(d,field,value):
 p,r=loadrow(d);obj=r
 for k in field[:-1]:obj=obj[k]
 obj[field[-1]]=value(obj[field[-1]]) if callable(value) else value;write(p,r)
def stale_ast(d):
 p,r=loadrow(d);arm=r['arms']['hybrid'];out=Q.tuple_tree(arm['output']);new=('and',out,('one',)) if out[0] not in EFORM else ('andF',out,('T',));ctx=Q.context(r['case']);arm['candidate']=arm['output']=new;arm['candidate_metrics']=arm['metrics']=C.metrics(new,ctx);(p.parent/'hybrid.tau').write_text(N.typed_render(new,ctx)+'.\n');write(p,r);recalc(d)
EFORM={'eq0','ne0','T','F','andF','orF','notF','exists'}
def zeros_accounting(d):
 for p in d.glob('*/result.json'):
  r=json.loads(p.read_text())
  for arm in r['arms'].values():
   arm['accounting']['accounted_wall_s']=0.;arm['accounting']['search_wall_s']=0.;arm['accounting']['native_cold_charge']={'native_processes':0,'native_wall_s':0.,'ordinals':[]}
  write(p,r)
 recalc(d)
def zeros_native_summary(d):
 for p in d.glob('*/result.json'):
  r=json.loads(p.read_text());r['native_summary']['processes']=0;r['native_summary']['native_wall_s']=0.;write(p,r)
 recalc(d)
def summary_cost(d):
 p=d/'SUMMARY.json';r=json.loads(p.read_text());r['arms']['hybrid']['component_accounted_wall_s']=0.;write(p,r)
def frozen_rows(d):
 p=d/'corpus-executed.json';r=json.loads(p.read_text());r['cases'][0]['original']=['zero'];write(p,r)
 m=d/'manifest-start.json';v=json.loads(m.read_text());v['executed_case_digest']=hashlib.sha256(json.dumps(r['cases'],sort_keys=True).encode()).hexdigest();write(m,v)
mutations=[
 ('reuse_forward_as_reverse',lambda d:mutate_gate(d,'reuse_forward')),
 ('swap_directions',lambda d:mutate_gate(d,'swap_directions')),
 ('missing_reverse',lambda d:mutate_gate(d,'missing_reverse')),
 ('stale_equivalent_emitted_ast',stale_ast),
 ('stale_context',lambda d:field_row(d,['context','V'],lambda v:list(reversed(v)))),
 ('wrong_binary_receipt',lambda d:rewrite_record(d,'binary_sha256','0'*64)),
 ('wrong_native_command',lambda d:rewrite_record(d,'command','normalize T')),
 ('wrong_free_closure',lambda d:rewrite_record(d,'command',lambda v:v.replace('all a : tau, b : tau ',''))),
 ('wrong_native_type',lambda d:rewrite_record(d,'command',lambda v:v.replace(': tau',': sbf',1))),
 ('timeout_marked_true',lambda d:rewrite_record(d,'timed_out',True)),
 ('nonzero_exit_marked_true',lambda d:rewrite_record(d,'returncode',1)),
 ('stale_profile_key',lambda d:field_row(d,['profile_key'],'0'*64)),
 ('stale_support_source',lambda d:field_row(d,['profile','support_source_sha256'],'0'*64)),
 ('inflated_original_bytes',lambda d:field_row(d,['original_metrics','expression_bytes'],lambda v:v+100)),
 ('wrong_candidate_metrics',lambda d:field_row(d,['arms','hybrid','candidate_metrics','expression_bytes'],0)),
 ('altered_frozen_rows_with_digest',frozen_rows),
 ('summary_only_cost_tamper',summary_cost),
 ('zero_all_accounting_recompute_summary',zeros_accounting),
 ('zero_native_process_summary_recompute',zeros_native_summary),
]
results=[]
for name,mutate in mutations:
 d=a.out/name;shutil.copytree(a.run,d);mutate(d)
 try:v=V.validate(d,check_source=False);rejected=False;error=None
 except Exception as exc:v=None;rejected=True;error=type(exc).__name__+': '+str(exc)
 results.append({'mutation':name,'rejected':rejected,'error':error,'verdict':v})
report={'status':'PASS' if all(x['rejected'] for x in results) else 'FAIL','control':control,'mutations':results,'mutations_rejected':sum(x['rejected'] for x in results),'mutation_count':len(results),'validator_sha256':sourcehash,'run_study_sha256':sha(a.source/'run_study.py'),'scope':'Local copied development packets, zero native processes. Historical-source mode necessary because the development run predates validator hardening; final current-source replay remains required.'};write(a.out/'SUMMARY.json',report);print(json.dumps(report,indent=2));raise SystemExit(report['status']!='PASS')
