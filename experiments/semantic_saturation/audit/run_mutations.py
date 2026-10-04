"""Targeted local mathematical mutants, never touches imported source files."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
mutants=[
 ('remove_both_child_case','support_oracle.py','product((1, 2, 3), repeat=len(patterns))','product((1, 2), repeat=len(patterns))'),
 ('resolve_shadowed_name_outermost','support_oracle.py',"len(state.names) - 1 - state.names[::-1].index(ast[1])","state.names.index(ast[1])"),
 ('reuse_caches_across_refinements','support_oracle.py','self.formula(ast[2], child, {}, {})','self.formula(ast[2], child, terms, formulas)'),
 ('accept_one_direction','native_oracle.py',"f['truth']==r['truth']=='T'","f['truth']=='T'"),
]
rows=[]
for name,file,old,new in mutants:
 d=a.out/name;d.mkdir(exist_ok=True)
 for f in ('support_oracle.py','engine.py','normalized_parser.py','native_oracle.py'):shutil.copyfile(a.source/f,d/f)
 txt=(d/file).read_text();assert txt.count(old)==1,(name,txt.count(old));(d/file).write_text(txt.replace(old,new))
 cmd=[sys.executable,'-B',str(Path(__file__).with_name('audit_math_harness.py')),'--source',str(d),'--out',str(d/'result.json')]
 run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 (d/'stdout.log').write_text(run.stdout);(d/'stderr.log').write_text(run.stderr)
 data=json.loads((d/'result.json').read_text()) if (d/'result.json').exists() else None
 rows.append({'mutation':name,'file':file,'old':old,'new':new,'mutant_sha256':hashlib.sha256((d/file).read_bytes()).hexdigest(),'returncode':run.returncode,'killed':run.returncode!=0,'failure_count':len(data['failures']) if data else None,'first_failure':data['failures'][0] if data and data['failures'] else None,'argv':cmd})
report={'status':'PASS' if all(r['killed'] for r in rows) else 'FAIL','mutation_count':len(rows),'results':rows,'limitations':['These are selected mutations of mathematical logic and receipt parsing, not exhaustive fault coverage.','No native executable was called.']}
(a.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(report['status']!='PASS')
