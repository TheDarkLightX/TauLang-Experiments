"""One-time deterministic fixture construction; replay uses the saved JSON.
No random selection and no held-out experimental corpus is consulted.
"""
import hashlib, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CHECKPOINT=ROOT.parent/'private/import/tau-pilot-cloud-checkpoint'
rows=[]; seen=set()
def add(ast,names,origin):
    key=json.dumps([names,ast],sort_keys=True)
    if key in seen:return
    seen.add(key)
    rows.append({'id':f'f{len(rows):04d}','free_variables':list(names),'ast':ast,'origin':origin})
def terms(names):
    base=[('zero',),('one',)]+[('var',x) for x in names]
    return base+[('not',a) for a in base]+[(op,a,b) for op in ('and','or','xor') for a in base for b in base]
for n in range(3):
    names=tuple('ab'[:n]); ts=terms(names)
    for t in ts:
        for op in ('eq0','ne0'): add((op,t),names,'complete depth-one term predicates, 0-2 variables')
    atoms=[('eq0',t) for t in [('zero',),('one',)]+[('var',x) for x in names]]
    for a in atoms:
        add(('notF',a),names,'negated shallow predicates')
        for b in atoms:
            for op in ('andF','orF'):add((op,a,b),names,'complete pairs of shallow predicates')
    body_names=names+('x',)
    for t in terms(body_names):
        for op in ('eq0','ne0'):add(('exists','x',(op,t)),names,'complete existential depth-one term predicates, up to 3 slots')
    # Force interaction of two occupancy assertions inside the binder.
    x=('var','x')
    for t in ts:
        add(('exists','x',('andF',('ne0',('and',x,t)),('ne0',('and',('not',x),t)))),names,'proper splitting every depth-one parameter term')
for n in range(2):
    names=tuple('a'[:n]);x=('var','x'); y=('var','y')
    for t in terms(names+('x','y')):
        add(('exists','x',('exists','y',('eq0',t))),names,'nested binders with up to 3 total slots')
        add(('exists','x',('notF',('exists','y',('ne0',t)))),names,'alternating ex/all via negation, up to 3 total slots')
# Deliberately redundant/free and shadowed names; these exercise lexical lookup.
for names in (('x',),('a','x'),('x','a'),('a','b'),('b','a')):
    for outer in ('x',names[0]):
        for inner in (outer,'z'):
            if len(names)>1: continue # nested total bound stays <=3
            for testname in sorted(set(names+(outer,inner))):
                add(('exists',outer,('exists',inner,('ne0',('var',testname)))),names,'repeated/shadowed names')
    for binder in names:
        add(('exists',binder,('eq0',('xor',('var',binder),('var',names[-1])))),names,'free-name shadowing and slot-order control')
corpus=json.loads((CHECKPOINT/'corpus.json').read_text())
for c in corpus:
    add(c['original'],c['free'],'inherited pilot original:'+c['name'])
    for a in c['registry_menu']:add(a,c['free'],'inherited pilot registry menu:'+c['name'])
# Exact native-output bytes and the recorded parser AST are both retained.
parser_receipts=[]
for path in sorted((CHECKPOINT/'runs/pilot-003').glob('*.json')):
    d=json.loads(path.read_text())
    if 'arms' not in d:continue
    a=d['arms'].get('native_normalizer',{}); detail=a.get('detail',{})
    nr=detail.get('normalization')
    if not nr or not detail.get('parsed'):continue
    rec={'case':d['case']['name'],'free_variables':d['case']['free'],
         'stdout':nr['stdout'],'returncode':nr['returncode'],'stderr':nr['stderr'],
         'candidate':a['candidate'],'binary_sha256':nr['binary_sha256'],
         'source_receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'origin':'inherited Mac pilot-003, not fresh Linux execution'}
    parser_receipts.append(rec)
    add(a['candidate'],d['case']['free'],'parsed native stdout:'+d['case']['name'])
out={'schema':'tau-support-proof-fixtures/v1','selection':'deterministic development/correctness fixtures; not experimental holdout',
     'maximum_total_slots':3,'fixtures':rows,'native_parser_receipts':parser_receipts,
     'pilot_corpus_sha256':hashlib.sha256((CHECKPOINT/'corpus.json').read_bytes()).hexdigest()}
(HERE/'fixtures.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(len(rows),'fixtures;',len(parser_receipts),'native parser receipts')
