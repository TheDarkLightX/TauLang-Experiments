#!/usr/bin/env python3
"""Check saved comparisons against the original Tau expression model."""
import copy, hashlib, json, math, statistics
from functools import lru_cache
from pathlib import Path
import checker_codegen
root=Path(__file__).resolve().parent
manifest=root/'MANIFEST.sha256'
if manifest.exists():
    for line in manifest.read_text().splitlines():
        digest,name=line.split('  ',1)
        path=root/name
        assert path.is_relative_to(root) and path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
reference=checker_codegen.load(root/'reference/tools/compile_tau.py')
source=(root/'reference/spec/vm.tau').read_text();model=reference.Parser(source).parse()
@lru_cache(maxsize=None)
def evaluate(values):return tuple(reference.step(model,values))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify_native(data):
    assert data['status']=='passed'
    assert data['source_sha256']==hashlib.sha256(source.encode()).hexdigest()
    keys={(x['app'],x['arm'],x['repeat']) for x in data['rows']}
    assert len(data['rows'])==36 and keys=={
        (app,arm,repeat) for app in ['auction','payroll','inference']
        for arm in ['stock','retained','program_bound','run_bound'] for repeat in [1,2,3]}
    comparisons=0
    for row in data['rows']:
        p=json.loads((root/'reference/examples'/f'{row["app"]}.json').read_text())
        private=json.loads((root/'reference/examples'/f'{row["app"]}.input.json').read_text())
        program=[v for instruction in p['instructions'] for v in instruction]
        prefix=program+[0]*(64-len(program))+[len(p['instructions'])]+private+[0]*(16-len(private))+[len(private)]
        state=[0]*20
        for transition in row['rows']:
            assert state[19]==0
            expected=list(evaluate(tuple(prefix+state)))
            assert transition['outputs']==expected and expected[20]==0
            assert math.isfinite(transition['seconds']) and transition['seconds']>=0
            state=expected[:20];comparisons+=1
        assert state[19]==1 and row['steps']==len(row['rows'])
        assert row['final_state']==dict(accumulator=state[0],pc=state[1],memory=state[2:18],input_cursor=state[18],halted=state[19])
        assert row['steps']=={'auction':73,'payroll':56,'inference':32}[row['app']]
        assert state[0]=={'auction':58000,'payroll':1,'inference':1}[row['app']]
        if row['app']=='auction':assert state[6]==1
        assert math.isclose(row['step_sum_seconds'],sum(t['seconds'] for t in row['rows']),rel_tol=0,abs_tol=1e-9)
        assert math.isclose(row['total_seconds'],row['setup_seconds']+row['step_sum_seconds'],rel_tol=0,abs_tol=1e-9)
    return comparisons

data=json.loads((root/'saved/native-results.json').read_text())
comparisons=verify_native(data)
for mutation in ['output','missing','time']:
    changed=copy.deepcopy(data)
    if mutation=='output':changed['rows'][0]['rows'][0]['outputs'][0]^=1
    elif mutation=='missing':changed['rows'].pop()
    else:changed['rows'][0]['total_seconds']+=1
    try:verify_native(changed)
    except AssertionError:pass
    else:raise AssertionError('Changed saved record accepted: '+mutation)
vectors=json.loads((root/'saved/checker-vectors.json').read_text())
assert len(vectors['inputs'])==len(vectors['outputs'])==1992
for values,expected in zip(vectors['inputs'],vectors['outputs']):
    assert list(evaluate(tuple(values)))==expected
correctness=json.loads((root/'saved/checker-correctness.json').read_text())
assert correctness['status']=='passed' and correctness['variant_comparisons']==7968
builds=json.loads((root/'saved/checker-builds.json').read_text())
assert builds['status']=='passed' and len(builds['variants'])==4
for row in builds['variants']:
    name=row['name']
    generated=reference.generate(source) if name=='baseline' else checker_codegen.generate(source,reference,narrow=name!='shared128',share=name!='width32')[0]
    digest=hashlib.sha256(generated.encode()).hexdigest()
    assert digest==row['generated_sha256']==correctness['sources'][name+'.rs']
    assert row['test_exit_code']==0 and row['identity']['dev_mode'] is False
    for app in ['auction','payroll','inference']:
        profile=json.loads((root/'saved'/name/(app+'-profile.json')).read_text())
        assert profile['status']=='executed_and_checked'
        assert profile['guest_image_id']==row['identity']['guest_image_id']
        assert profile['user_cycles']==sum(s['cycles'] for s in profile['segments'])
proofs=json.loads((root/'saved/proof-results.json').read_text())
assert proofs['status']=='passed' and len(proofs['proofs'])==6
for row in proofs['proofs']:
    folder=root/'saved/proofs'/f'{row["app"]}-{row["variant"]}'
    assert sha(folder/'receipt.bin')==row['receipt_sha256']
    assert sha(folder/'claim.json')==row['claim_sha256']
    build=next(b for b in builds['variants'] if b['name']==row['variant'])
    assert row['host_sha256']==build['binary_sha256']
    assert row['result']['status']=='proved_and_verified' and row['verification']['status']=='verified'
    assert row['result']['guest_image_id']==row['verification']['guest_image_id']==build['identity']['guest_image_id']
    profile=json.loads((root/'saved'/row['variant']/(row['app']+'-profile.json')).read_text())
    assert row['result']['stats']['user_cycles']==profile['user_cycles']
    assert row['result']['stats']['total_cycles']==sum(1<<s['po2'] for s in profile['segments'])
    assert row['result']['proof_bytes']==(folder/'receipt.bin').stat().st_size
for app in ['auction','payroll','inference']:
    assert (root/'saved/proofs'/f'{app}-baseline/claim.json').read_bytes()==(root/'saved/proofs'/f'{app}-shared32/claim.json').read_bytes()
binding=json.loads((root/'saved/binding-results.json').read_text())
assert binding['status']=='passed' and len(binding['rows'])==14
assert binding['candidate_sha256']==data['candidate_sha256']
assert sum(r['transitions'] for r in binding['rows'])==402
assert sum(r['changed_fixed_values_rejected'] for r in binding['rows'])==42
boundary_count=0
for row in binding['rows']:
    p=json.loads((root/'reference/examples'/f'{row["app"]}.json').read_text())
    private=json.loads((root/'reference/examples'/f'{row["app"]}.input.json').read_text())
    program=[v for instruction in p['instructions'] for v in instruction]
    prefix=program+[0]*(64-len(program))+[len(p['instructions'])]+private+[0]*(16-len(private))+[len(private)]
    state=[0]*20
    for _ in range(row['transitions']):
        output=evaluate(tuple(prefix+state));assert output[20]==0;state=list(output[:20])
    assert state[19]==1
    assert row['final_state']==dict(accumulator=state[0],pc=state[1],memory=state[2:18],input_cursor=state[18],halted=state[19])
    for case in row['boundary_checks']:
        values=prefix+[0]*20;values[case['field']]=case['value']
        assert list(evaluate(tuple(values)))==case['outputs'];boundary_count+=1
assert boundary_count==420
import word_checker_codegen
prepared=json.loads((root/'saved/prepared32/receipt.json').read_text())
assert prepared['status']=='passed'
generated=word_checker_codegen.generate(source,reference)[0]
assert hashlib.sha256(generated.encode()).hexdigest()==prepared['generated_sha256']
assert generated==(root/'saved/prepared32/generated.rs').read_text()
relation=json.loads((root/'saved/prepared-relation.json').read_text())
assert relation['status']=='passed' and relation['vectors']==1992 and relation['out_of_range_rejections']==3
assert relation['binary_sha256']==prepared['binary_sha256']
assert relation['vectors_sha256']==sha(root/'saved/checker-vectors.json')
extra=json.loads((root/'saved/prepared-proof-results.json').read_text())
assert extra['status']=='passed' and len(extra['proofs'])==3
for row in extra['proofs']:
    folder=root/'saved/prepared-proofs'/row['app']
    assert row['wrong_image_rejected'] is True
    assert sha(folder/'receipt.bin')==row['receipt_sha256'] and sha(folder/'claim.json')==row['claim_sha256']
    assert row['host_sha256']==prepared['binary_sha256']
    assert row['result']['status']=='proved_and_verified' and row['result']['receipt_kind']=='succinct'
    assert row['verification']['status']=='verified'
    assert row['result']['guest_image_id']==row['verification']['guest_image_id']==prepared['identity']['guest_image_id']
    assert (folder/'claim.json').read_bytes()==(root/'saved/proofs'/f'{row["app"]}-baseline/claim.json').read_bytes()
    profile=json.loads((root/'saved/prepared32'/(row['app']+'-profile.json')).read_text())
    assert profile['user_cycles']==sum(s['cycles'] for s in profile['segments'])==row['result']['stats']['user_cycles']
    assert sum(1<<s['po2'] for s in profile['segments'])==row['result']['stats']['total_cycles']
for app in ['auction','payroll','inference']:
    print(app,{arm:round(statistics.median(r['total_seconds'] for r in data['rows'] if r['app']==app and r['arm']==arm),6) for arm in ['stock','retained','program_bound','run_bound']})
print(f'PASS: {comparisons} native transitions, 402 additional transitions, 420 boundary states, 1992 stored checker vectors, generated-source hashes, timing sums, nine receipt hashes and recorded verification results. Changed output, missing run and altered total rejected.')
print('This checks saved evidence; use the proof executable verify command for fresh cryptographic verification.')
