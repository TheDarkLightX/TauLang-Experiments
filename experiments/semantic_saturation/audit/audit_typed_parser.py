"""Exact typed-emission round trips and malformed mathematical syntax controls."""
from pathlib import Path
import argparse,hashlib,json,random,sys
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();sys.path.insert(0,str(a.source));import engine as E,native_oracle as N,typed_parser as P
sys.path.insert(0,str(Path(__file__).parent));from audit_math_harness import gen_formula,gen_term
rng=random.Random(31470702);failures=[];n=0;ctx=E.Context((('a','tau'),('b','tau')),V=('a','b'))
for i in range(500):
 ast=gen_formula(rng,('a','b'),5,2) if i%2 else gen_term(rng,('a','b'),5)
 text=N.typed_render(ast,ctx);parsed=P.parse_emitted(text,ctx.V);n+=1
 if parsed!=ast:failures.append({'type':'roundtrip','input':ast,'text':text,'output':parsed})
bad=['(a : sbf)','(c : tau)','(a : tau) && (b : tau)','((a : tau) && (b : tau))',"T'",'!(0)','ex x : tau ((x : tau))','ex xx : tau (T)','((a : tau) = 1)','(a : tau) trailing','(a : tau).','all a : tau (T)','(T | F)','((a : tau) & T)','(a : tau',')','((a : tau) = 0) = 0']
for text in bad:
 try:
  output=P.parse_emitted(text,ctx.V);failures.append({'type':'accepted_invalid','text':text,'output':output})
 except P.TypedParseError:pass
 n+=1
report={'status':'PASS' if not failures else 'FAIL','seed':31470702,'checks':n,'roundtrips':500,'negative_cases':len(bad),'failures':failures,'source_sha256':{f:hashlib.sha256((a.source/f).read_bytes()).hexdigest() for f in ('typed_parser.py','native_oracle.py')},'limitations':['This parser implements the study grammar, not the native Tau parser.','No native execution or universal parser-refinement proof.']};a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
