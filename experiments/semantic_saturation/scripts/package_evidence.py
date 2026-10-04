"""Deterministic archives of original study receipts; never include Tau sources."""
from pathlib import Path
import argparse,gzip,hashlib,json,tarfile,time
ROOT=Path(__file__).resolve().parent.parent
SETS={
 'heldout-001':['results/heldout-001'],
 'reuse-001':['results/reuse-001'],
 'development-evidence':['results/dev-smoke-001','results/development-001','results/dev-accounting-002','results/dev-binding-003','results/final-prefreeze-smoke-004'],
}

def build(name,out):
 files=sorted(p for d in SETS[name] for p in (ROOT/d).rglob('*') if p.is_file())
 if not files:raise ValueError('missing raw evidence; unpack archives first')
 if any(p.is_symlink() for p in files):raise ValueError('symlinks excluded')
 with out.open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=f,mtime=0) as z:
   with tarfile.open(fileobj=z,mode='w|') as tar:
    for p in files:
     info=tar.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
     with p.open('rb') as data:tar.addfile(info,data)
 return {'archive':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'files':len(files)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--name',choices=SETS,required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
 if out.exists():raise ValueError('archive destination must be fresh')
 print(json.dumps(build(a.name,out),sort_keys=True))
if __name__=='__main__':main()
