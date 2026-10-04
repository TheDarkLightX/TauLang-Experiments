"""Force oracle exhaustion and verify it remains visible through native fallback."""
from pathlib import Path
import argparse,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import checked_registry as R,support_oracle as S,run_study as Q,engine as E
old=R.FORM_LIMITS;R.FORM_LIMITS=S.Limits(max_states=0)
try:
 row={'name':'forced-support-unknown','split':'audit-development','family':'forced-resource-boundary','free':['a'],'original':('exists','x',('eq0',('var','x'))),'seed':5197,'size_parameter':1}
 result=Q.run_case(row,str(a.binary),a.out/'case',Q.DEFAULT_CONFIG.copy());summary=Q.summary([result]);ctx=E.Context((('a','tau'),),V=('a',));oracle=R.CheckedOracle(a.binary,a.out/'unknown-cache-native')
 first=oracle.check(('T',),('T',),ctx,'forced-unknown-1');second=oracle.check(('T',),('T',),ctx,'forced-unknown-2')
 checks={'native_parsed_metrics_retained':result['parsed_native_metrics'] is not None,'native_proposal_unknown_visible':result['normalization_proposal_admission_status']=='REJECTED_SUPPORT_UNKNOWN','summary_unknown_visible':summary['normalization_admission_statuses'].get('REJECTED_SUPPORT_UNKNOWN')==1,'native_retention_reason':result['arms']['native_reserialized']['detail']['retained_original_reason']=='native_proposal_REJECTED_SUPPORT_UNKNOWN','unknown_not_cached':first['status']==second['status']=='REJECTED_SUPPORT_UNKNOWN' and not first['cache_hit'] and not second['cache_hit'] and not oracle.cache,'unknown_no_native_gate':len(oracle.native.records)==0,'identity_distinguished':result['arms']['native_reserialized']['gate']['status']=='ACCEPTED_IDENTITY'}
 report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'runtime_mutation':'FORM_LIMITS=max_states0, restored after audit','summary':summary,'source_sha256':{f:hashlib.sha256((a.source/f).read_bytes()).hexdigest() for f in ('run_study.py','checked_registry.py')},'scope':'Forced development resource failure; not benchmark performance.'};(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='summary'},indent=2))
finally:R.FORM_LIMITS=old
