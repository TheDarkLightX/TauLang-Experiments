"""Freeze source, experimental inputs and protocol bytes before heldout execution."""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,time

ROOT=Path(__file__).resolve().parent.parent

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def files():
    selected=[]
    for folder in ('src','tests'):
        selected.extend(ROOT.joinpath(folder).glob('*.py'))
    selected.extend(ROOT.joinpath('scripts').glob('*.sh'))
    for name in ('PROTOCOL.md','EXPERIMENT_MATRIX.md','REUSE_PROTOCOL.md','PROOF_OBLIGATIONS.json'):
        selected.append(ROOT/'docs'/name)
    for name in ('train.json','dev.json','test.json','duplicate-audit.json','reuse-frozen-v1.json'):
        selected.append(ROOT/'corpora'/name)
    selected.append(ROOT/'corpora/resource-protocol/matrix.json')
    selected.extend(ROOT.joinpath('results/build').glob('*.json'))
    return sorted(selected)


def verify(path,expected_hash):
    path=Path(path)
    if digest(path)!=expected_hash:raise ValueError('freeze digest differs from explicit expected digest')
    data=json.loads(path.read_text())
    for name,sha in data['files'].items():
        p=ROOT/name
        if not p.is_file() or digest(p)!=sha:raise ValueError('frozen artifact changed: '+name)
    return data


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out)
    if out.exists():raise ValueError('freeze path must be fresh')
    paths=files()
    if any(not x.is_file() for x in paths):raise ValueError('missing protocol/input file')
    manifest={'schema':'tau-study-prospective-freeze/v1','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
       'base_revision':'65ef69bdc5e6f1e479236d9dfb4d9b6d2e5302d1','status':'prospectively frozen before holdout outputs; private record, not a public preregistration service',
       'files':{str(x.relative_to(ROOT)):digest(x) for x in paths},'test_cases':336,'train_cases_generated':84,'development_cases':84,
       'heldout_evaluation_started':False,'primary_method_claim':'scoped checked semantic-saturation implementation; no generic architecture novelty claim'}
    out.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(out),'sha256':digest(out),'files':len(paths)}))
if __name__=='__main__':main()
