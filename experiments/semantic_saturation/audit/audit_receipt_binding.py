"""Benign local artifact mutation: reuse forward receipt as reverse evidence.
A verifier claiming both native directions must reject this altered packet.
No native subprocess or external service is invoked.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import validate_run as V
sourcehash=hashlib.sha256((a.source/'validate_run.py').read_bytes()).hexdigest();clone=a.out/'mutated-run';shutil.copytree(a.run,clone)
changed=None
for path in sorted(clone.glob('*/result.json')):
 row=json.loads(path.read_text())
 for name,arm in row['arms'].items():
  gate=arm['gate']
  if gate['status']=='ACCEPTED' and gate['native']['forward']['command']!=gate['native']['reverse']['command']:
   old=gate['native']['reverse'];gate['native']['reverse']=gate['native']['forward'];path.write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
   changed={'case':row['case']['name'],'arm':name,'original_reverse_ordinal':old['ordinal'],'reused_forward_ordinal':gate['native']['forward']['ordinal'],'original_reverse_command':old['command'],'replacement_command':gate['native']['forward']['command']};break
 if changed:break
assert changed
try:verdict=V.validate(clone,check_source=False);rejected=False;error=None
except Exception as e:verdict=None;rejected=True;error=str(e)
report={'status':'PASS' if rejected else 'FAIL','mutation_rejected':rejected,'mutation':changed,'validator_result':verdict,'error':error,'validator_source_sha256':sourcehash,'scope':'Packet binding mutation only; all ASTs/output programs and raw native receipts left unchanged. historical source mode used because six-case development receipts predate current validator.'};(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(not rejected)
