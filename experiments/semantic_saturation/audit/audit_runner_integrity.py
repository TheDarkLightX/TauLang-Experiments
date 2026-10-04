"""Audit unique cold accounting and fail-closed run provenance without native work."""
from pathlib import Path
import argparse,contextlib,hashlib,io,json,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--development-results',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import run_study as Q
rows=[]
for f in sorted(a.development_results.glob('*/result.json')):
 r=json.loads(f.read_text());gates=[r['arms'][n]['gate'] for n in ('native_sympy_portfolio','native_guarded','sympy')];costs={}
 for i,g in enumerate(gates):
  n=g.get('native');k=(n['forward']['ordinal'],n['reverse']['ordinal']) if n else ('non-native',i);costs.setdefault(k,g.get('cold_elapsed_s',g['elapsed_s']))
 want=sum(costs.values());got=Q.unique_gate_cold_cost(*gates);rows.append({'case':r['case']['name'],'expected_unique_gates':len(costs),'expected_s':want,'actual_s':got,'pass':abs(want-got)<1e-12})
# No command is run. A fixture digest function emulates binary bytes changing
# between the initial manifest and terminal integrity check.
binary=a.out/'nonexecuted-binary-fixture';binary.write_text('not an executable\n');corpus=a.out/'empty-development.json';corpus.write_text(json.dumps({'split':'audit-development','cases':[]}))
real_digest=Q.digest;calls=0

def changing_digest(path):
 global calls
 if Path(path)==binary:
  calls+=1
  if calls>1:return 'f'*64
 return real_digest(path)

Q.digest=changing_digest;old=sys.argv;sys.argv=['run_study.py','--binary',str(binary),'--corpus',str(corpus),'--out',str(a.out/'provenance-run')];output=io.StringIO();exit_code=0
try:
 with contextlib.redirect_stdout(output):
  try:Q.main()
  except SystemExit as exc:exit_code=exc.code
finally:Q.digest=real_digest;sys.argv=old
terminal=json.loads((a.out/'provenance-run/SUMMARY.json').read_text());provenance_pass=exit_code==2 and terminal['status']=='PROVENANCE_FAILED' and not terminal['binary_unchanged']
report={'status':'PASS' if rows and all(r['pass'] for r in rows) and provenance_pass else 'FAIL','cold_accounting_cases':rows,'forced_provenance_failure':{'exit_code':exit_code,'summary_status':terminal['status'],'binary_unchanged':terminal['binary_unchanged'],'pass':provenance_pass},'run_study_sha256':real_digest(Q.__file__),'scope':'Local unit-level digest mutation and existing-receipt accounting; zero native subprocesses.'};(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(report['status']!='PASS')
