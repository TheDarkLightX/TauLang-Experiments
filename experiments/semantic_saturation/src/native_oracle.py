"""Strict two-direction native Tau gate; every command has its own receipt."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib,json,os,re,subprocess,time
import engine

FLAGS=('--charvar','false','--severity','error','--color','false',
       '--status','false','--benchmarks','false')

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def typed_render(ast, context, bound=frozenset()):
    if ast[0]=='var':
        descriptor=dict(context.terms).get(ast[1],context.term_sort)
        return f'({ast[1]} : {descriptor})'
    if ast[0]=='exists':
        descriptor=dict(context.terms).get(ast[1],context.term_sort)
        return f'ex {ast[1]} : {descriptor} ({typed_render(ast[2],context,bound|{ast[1]})})'
    if ast[0] in engine.LEAVES: return engine.render(ast,context)
    args=[typed_render(x,context,bound) for x in engine.children(ast)]
    if ast[0]=='not': return f"({args[0]})'"
    if ast[0]=='notF': return f'!({args[0]})'
    if ast[0] in ('eq0','ne0'): return f"({args[0]} {'=' if ast[0]=='eq0' else '!='} 0)"
    sym={'and':'&','or':'|','xor':'^','andF':'&&','orF':'||'}[ast[0]]
    return f'({args[0]} {sym} {args[1]})'

def exact_truth(record):
    if record['timed_out'] or record['returncode']!=0 or record['stderr'].strip():
        return 'UNKNOWN'
    match=re.fullmatch(r'\s*%1:\s*([TF])\s*',record['stdout'])
    return match.group(1) if match else 'UNKNOWN'

@dataclass(frozen=True)
class Equivalence:
    status: str
    forward: dict
    reverse: dict
    scope_key: str

class NativeOracle:
    def __init__(self,binary,receipt_dir,timeout=10):
        self.binary=str(Path(binary).resolve()); self.binary_sha256=digest(self.binary)
        self.directory=Path(receipt_dir); self.directory.mkdir(parents=True,exist_ok=True)
        self.timeout=timeout; self.records=[]; self.cache={}
        self.env={k:v for k,v in os.environ.items() if not k.startswith('TAU_')}
    def run(self,command,label):
        argv=[self.binary,*FLAGS,'-e',command]
        start=time.monotonic(); timed_out=False
        try:
            p=subprocess.run(argv,capture_output=True,text=True,timeout=self.timeout,env=self.env)
            code,out,err=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            timed_out=True;code=None
            def txt(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
            out,err=txt(e.stdout),txt(e.stderr)
        record={'ordinal':len(self.records)+1,'label':label,'argv':argv,'command':command,
                'binary_sha256':self.binary_sha256,'timeout_s':self.timeout,
                'timed_out':timed_out,'returncode':code,'stdout':out,'stderr':err,
                'elapsed_s':time.monotonic()-start,'TAU_environment_removed':True}
        record['truth']=exact_truth(record)
        self.records.append(record)
        (self.directory/f"{record['ordinal']:04d}.json").write_text(json.dumps(record,indent=2)+'\n')
        return record
    def equivalent(self,left,right,context,label):
        # Validate shape/sorts/interface before invoking a trusted native checker.
        for ast in (left,right):
            if engine.sort_of(ast,context)!='formula':raise ValueError('formula gate requires formulas')
            if not engine.free_vars(ast)<=context.interface:raise ValueError('changed input interface')
        key=(self.binary_sha256,context.key,left,right)
        if key in self.cache:return self.cache[key]
        a,b=engine.render(left,context),engine.render(right,context)
        names=context.V if context.V is not None else tuple(n for n,_ in context.terms)
        binders=', '.join(f'{n} : {dict(context.terms)[n]}' for n in names)
        prefix=f'all {binders} ' if binders else ''
        f=self.run(f'normalize {prefix}(({a}) -> ({b}))',label+':forward')
        r=self.run(f'normalize {prefix}(({b}) -> ({a}))',label+':reverse')
        status='EQUIVALENT' if f['truth']==r['truth']=='T' else ('DIFFERENT' if 'F' in (f['truth'],r['truth']) else 'UNKNOWN')
        result=Equivalence(status,f,r,context.key);self.cache[key]=result
        return result
    def normalize(self,original,context,label):
        # Explicit types here because no universal binder fixes free-variable sorts.
        return self.run('normalize '+typed_render(original,context),label+':normalize')
    def finish(self):
        if digest(self.binary)!=self.binary_sha256:raise RuntimeError('native binary changed during campaign')
        out={'binary':self.binary,'binary_sha256':self.binary_sha256,'timeout_s':self.timeout,
             'processes':len(self.records),'timeouts':sum(r['timed_out'] for r in self.records),
             'parse_or_unknown':sum(r['truth']=='UNKNOWN' for r in self.records),
             'native_wall_s':sum(r['elapsed_s'] for r in self.records),'cache_entries':len(self.cache)}
        (self.directory/'SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n')
        return out
