"""Five fixed fresh-process normalization repeats on inherited factoring controls."""
from pathlib import Path
import argparse,collections,hashlib,json,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(a.source));import engine as E,native_oracle as N,study_core as C

def tup(x):return tuple(tup(y) for y in x) if isinstance(x,list) else x

oracle=N.NativeOracle(a.binary,a.out/'native',timeout=10);corpus=json.loads(a.corpus.read_text());cases=corpus['cases'] if isinstance(corpus,dict) else corpus;rows=[]
for case in cases:
 if case['name'] not in ('factor_nonzero','factor_zero'):continue
 ctx=E.Context(tuple((x,'tau') for x in case['free']),V=tuple(case['free']));ast=tup(case['original']);runs=[]
 for i in range(5):
  r=oracle.normalize(ast,ctx,case['name']+':repeat'+str(i))
  out=C.parse_native(r['stdout'],ctx.V,'formula') if r['returncode']==0 and not r['stderr'].strip() and not r['timed_out'] else None
  runs.append({'ordinal':r['ordinal'],'stdout':r['stdout'],'parsed':out,'typed_bytes':C.emitted_cost(out,ctx) if out else None})
 rows.append({'case':case['name'],'runs':runs,'distinct_native_outputs':len({x['stdout'] for x in runs}),'typed_byte_values':sorted({x['typed_bytes'] for x in runs},key=repr)})
report={'status':'PASS' if len(rows)==2 and all(x['distinct_native_outputs']==1 and None not in x['typed_byte_values'] for x in rows) else 'VARIATION_OR_FAILURE','rows':rows,'native_summary':oracle.finish(),'corpus_sha256':hashlib.sha256(a.corpus.read_bytes()).hexdigest(),'repetitions':5,'scope':'Repeatability on two inherited development cases only; no cross-build cause attribution.'};(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
