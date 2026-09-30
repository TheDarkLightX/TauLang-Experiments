#!/usr/bin/env python3
"""Check the package hashes, saved model answers, output tuples and arithmetic."""
from __future__ import annotations
import hashlib,json,math,pathlib,statistics,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'vm/tools'))
from compile_tau import Parser,step

def read(path):return json.loads((ROOT/path).read_text())
if (ROOT/'MANIFEST.sha256').exists():
    for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
        digest,name=line.split('  ',1)
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise SystemExit('Checksum mismatch: '+name)
validation_path=ROOT/'recorded/validation.json'
if validation_path.exists():
    validation=read('recorded/validation.json')
    stock={r['name']:r['printed_formulas'] for r in validation['stock_printing_comparison']['tests']}
    inventories=[]
    for suite in validation['full_suites']:
        records=read('recorded/'+suite['test_records'])
        names={r['name'] for r in records}
        if len(records)!=2398 or len(names)!=2398:raise SystemExit('Suite inventory differs')
        inventories.append(names)
        if sum(r['status']=='passed' for r in records)!=2395:raise SystemExit('Suite pass count differs')
        failed={r['name']:r['printed_formulas'] for r in records if r['status']=='failed'}
        if failed!=stock:raise SystemExit('Failures differ from the stock printing comparison')
        if sum(r.get('internal_cases',{}).get('skipped',0) for r in records)!=12:
            raise SystemExit('Internal skip count differs')
    if len(inventories)!=2 or inventories[0]!=inventories[1]:raise SystemExit('Switch-mode inventories differ')
    for check in validation['algebra_build_checks']:
        if len(check['test_records'])!=check['tests'] or any(r['status']!='passed' for r in check['test_records']):
            raise SystemExit('Algebra check differs')
    print('Saved test counts and stock printing comparison checked.')
root=Parser((ROOT/'vm/spec/vm.tau').read_text()).parse()
expected={}
for name in ('conformance','distinct'):
    data=read('inputs/'+name+'-cases.json')
    if len(data['inputs'])!=len(data['expected_outputs']):raise SystemExit('Case count mismatch')
    for values,want in zip(data['inputs'],data['expected_outputs']):
        if list(step(root,tuple(values)))!=want:raise SystemExit('Saved model answer differs')
    expected[name]=data['expected_outputs']
programs=read('inputs/programs.json')
for name,private,steps in [('smoke',[],3),('payroll',[10],17)]:
    words=[v for word in programs[name]['instructions'] for v in word]
    state=[0]*20;rows=[]
    for _ in range(steps):
        values=words+[0]*(64-len(words))+[len(words)//2]+private+[0]*(16-len(private))+[len(private)]+state
        row=list(step(root,tuple(values)))
        if row[20]:raise SystemExit('Unexpected VM fault in trace')
        rows.append(row);state=row[:20]
    if not state[19]:raise SystemExit('Trace did not halt')
    expected[name]=rows
path=ROOT/'recorded/evaluator-only-results.json'
if path.exists():
    results=json.loads(path.read_text())
    if results['status']!='passed':raise SystemExit('Recorded replay did not pass')
    build=read('recorded/build.json')
    if results['binary_sha256']!=build['binary_sha256']:raise SystemExit('Measured binary differs')
    if hashlib.sha256((ROOT/'retained-evaluator.patch').read_bytes()).hexdigest()!=build['evaluator_patch_sha256']:
        raise SystemExit('Measured patch differs')
    if hashlib.sha256((ROOT/'vm/spec/vm.tau').read_bytes()).hexdigest()!=results['vm_sha256']:
        raise SystemExit('Recorded VM hash differs')
    seen=set()
    for repeat in results['repeats']:
        key=(repeat['repeat'],repeat['arm'])
        if key in seen:raise SystemExit('Duplicate repeat')
        seen.add(key)
        if set(repeat['workload'])!={'smoke','payroll','conformance'}:
            raise SystemExit('Workload set differs')
        times=[]
        for name,rows in repeat['workload'].items():
            if [r['outputs'] for r in rows]!=expected[name]:raise SystemExit('Recorded output differs')
            times += [r['seconds'] for r in rows]
        if len(times)!=55 or not all(x>0 for x in times):raise SystemExit('Invalid timing set')
        if not math.isclose(statistics.median(times),repeat['step_median_seconds']):raise SystemExit('Median differs')
        if not math.isclose(sum(times),repeat['step_sum_seconds']):raise SystemExit('Step sum differs')
        if repeat['steps']!=55 or repeat['setup_seconds']<=0:raise SystemExit('Invalid repeat summary')
    if seen!={(i,arm) for i in range(1,6) for arm in ('ordinary','retained')}:
        raise SystemExit('Expected five complete repeats per version')
    total={}
    for arm in ('ordinary','retained'):
        record=results['distinct'][arm];rows=record['rows']
        if [r['outputs'] for r in rows]!=expected['distinct']:raise SystemExit('Distinct output differs')
        elapsed=sum(r['seconds'] for r in rows)
        if not all(r['seconds']>0 for r in rows):raise SystemExit('Invalid distinct timing')
        if not math.isclose(elapsed,record['step_sum_seconds']):raise SystemExit('Distinct sum differs')
        if record['setup_seconds']<=0:raise SystemExit('Invalid distinct setup')
        total[arm]=elapsed+record['setup_seconds']
    med={arm:statistics.median(r['step_median_seconds'] for r in results['repeats'] if r['arm']==arm) for arm in ('ordinary','retained')}
    ratio=med['ordinary']/med['retained']
    if not math.isclose(ratio,results['summary']['median_step_ratio']):raise SystemExit('Ratio differs')
    inclusive=total['ordinary']/total['retained']
    if not math.isclose(inclusive,results['summary']['setup_inclusive_distinct_ratio']):raise SystemExit('Setup-inclusive ratio differs')
    if results['summary']['checked_transitions_per_arm']!=531 or results['summary']['distinct_inputs']!=256:
        raise SystemExit('Recorded counts differ')
    print(json.dumps({'status':'passed','median_step_ratio':ratio,
        'setup_inclusive_distinct_ratio':inclusive,'checked_transitions_per_arm':531,
        'scope':'Saved results and model recomputation; no Tau execution.'}))
else:
    print('Model answers checked; no fresh evaluator-only recording yet.')
