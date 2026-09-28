#!/usr/bin/env python3
"""Validate the recorded evidence without running Tau; diagnostics remain failures."""
from collections import Counter
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile
import check
import check_definitions as definitions
ROOT=Path(__file__).resolve().parent

def require(ok,message):
    if not ok:raise RuntimeError(message)
def read(name):return json.loads((ROOT/name).read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

for line in (ROOT/'SHA256SUMS').read_text().splitlines():
    wanted,name=line.split('  ',1)
    require(digest(ROOT/name)==wanted,'file hash: '+name)
info=read('build-info.json')
for name,wanted in info['patch_sha256'].items():require(digest(ROOT/name)==wanted,'patch hash: '+name)
with tempfile.TemporaryDirectory(prefix='tau-minmax-expected-') as d:
    tmp=Path(d);shutil.copy2(ROOT/'exact_cases.py',tmp/'exact_cases.py')
    subprocess.run(['python3',str(tmp/'exact_cases.py')],check=True,capture_output=True,text=True)
    require((tmp/'exact-cases.json').read_bytes()==(ROOT/'exact-cases.json').read_bytes(),'case generation')
cases=read('exact-cases.json');byid={r['id']:r for r in cases}
require(len(cases)==len(byid)==2352,'exact case identities')
require(Counter(r['expected'] for r in cases)=={'T':1176,'F':1176},'expected answer balance')
record=read('exact.json')
require(record['binary_sha256']==info['corrected_binary_sha256'],'exact binary identity')
require(record['cases_sha256']==digest(ROOT/'exact-cases.json'),'exact corpus identity')
require(len(record['rows'])==len(cases) and {r['id'] for r in record['rows']}==set(byid),'exact results')
for row in record['rows']:
    good=(row['returncode']==0 and not row['timeout'] and not row['stderr'] and
          re.fullmatch(r'%\d+:\s*'+byid[row['id']]['expected']+r'\s*',row['stdout']) is not None)
    require(good and row['passed']==good,'exact verdict: '+row['id'])
require(record['checks']==record['passed']==2352 and record['failed']==0,'exact summary')

for file,identity in [('focused.json','corrected_binary_sha256'),('operand-reference-focused.json','operand_reference_binary_sha256')]:
    record=read(file);require(record['binary_sha256']==info[identity],'focused binary identity')
    require(record['checks']==record['passed']==10 and record['failed']==0,'focused summary')
    require([r['case'] for r in record['results']]==read('cases.json'),'focused identities')
    for result in record['results']:
        row=result['observation'];expected=result['case']['expected']
        require(row['command']==result['case']['command'],'focused command')
        if expected=='roundtrip':
            formula=re.fullmatch(r'%\d+:\s*([^\n]+)\s*',row['stdout']);followup=row.get('reparsed')
            good=bool(check.clean(row) and formula and followup and
                      followup['command']=='sat '+formula[1].rstrip('.')+'.' and check.verdict(followup,'T'))
        elif expected in ('T','F'):good=check.verdict(row,expected)
        else:good=check.model(row,expected)
        require(good and result['passed']==good,'focused verdict')

newcases=definitions.cases();require(len(newcases)==128,'definition cases')
newresults={}
for file,wanted,identity in [('corrected-definition-values.json',72,'corrected_binary_sha256'),
                            ('operand-reference-values.json',0,'operand_reference_binary_sha256'),
                            ('pre-operand-reference-values.json',0,'pre_operand_reference_binary_sha256')]:
    record=read(file);require(record['binary_sha256']==info[identity],'definition binary identity')
    require(len(record['cases'])==128 and record['passed'] is False,'definition record size/status')
    accepted=0
    for expected,row in zip(newcases,record['cases']):
        require(all(row[k]==v for k,v in expected.items()),'definition input or mathematical expectation')
        actual=definitions.verdict(expected,row);good=actual==expected['expected']
        require(row['passed']==good and row['actual']==actual,'definition acceptance')
        accepted+=good
    require(accepted==wanted,'definition acceptance count: '+file)
    newresults[file]=record
corrected=newresults['corrected-definition-values.json']['cases']
failed=[r for r in corrected if not r['passed']]
require(len(failed)==56,'remaining diagnostic count')
require(all('disagrees with the argument types' in r['stderr'] for r in failed),'diagnostic identity')
for row in corrected:
    require(row['returncode']==0 and not row.get('timeout') and
            re.search(r'^%1: '+row['expected']+r'$',row['stdout'],re.M),'printed Boolean value')
controls=read('parenthesized-definition-controls.json')
require(len(controls)==2 and {r['variant'] for r in controls}=={'reference','corrected'},'control builds')
for record in controls:
    require(record['binary_sha256']==info['pre_operand_reference_binary_sha256' if record['variant']=='reference' else 'corrected_binary_sha256'],'control binary identity')
    require(len(record['cases'])==56,'control count')
    for bare,control in zip(failed,record['cases']):
        before,after=bare['input'].split(' := ',1);call,command=after.split('. ',1)
        require(control['input']==before+' := ('+call+'). '+command,'control differs beyond parentheses')
        for key in ['returncode','stdout','stderr']:
            require(control[key]==bare[key],'parenthesized output: '+key)
        require(control['passed'] is False and definitions.verdict(control,control) is None,'control diagnostics not accepted')

tests=read('release-tests.json')
names=[r['name'] for r in tests['tests']]
require(len(names)==len(set(names))==tests['registered_tests']==2543,'registered test identities')
require(all(r['status'] in ('passed','failed') for r in tests['tests']),'registered status')
require(tests['returncode']==8,'full suite exit')
require([r['name'] for r in tests['tests'] if r['status']=='failed']==['test_repl-run_cmd-values_stay_within_constant_size_budget'],'full suite failure identity')
for name,assertions,passed,failed_count in [('operand-reference-grammar.txt',260,244,16),('corrected-grammar.txt',272,272,0)]:
    log=(ROOT/name).read_text()
    require(re.search(r'assertions:\s*'+str(assertions)+r'\s*\|\s*'+str(passed)+r' passed\s*\|\s*'+str(failed_count)+r' failed',log),'API assertion counts')
prior=read('prior-constant-budget-comparison.json')
values=[]
for row in prior:
    lines=re.findall(r'^o1\[\d+\] := .*$',row['stdout'],re.M)
    require(len(lines)==9 and not any(l.startswith('o1[9]') for l in lines),'prior budget outputs')
    values.append(lines)
require(values[0]==values[1],'prior budget output comparison')
current_values=re.findall(r'^o1\[\d+\] := .*$',(ROOT/'release-failure.txt').read_text(),re.M)
require(current_values==values[0],'current full-suite budget values differ from prior reference')
print(json.dumps(dict(exact_checks_passed=2352,focused_checks_passed=10,
                     new_checks=dict(passed=72,failed_with_diagnostic=56),
                     controls_match=112,registered=dict(passed=2542,failed=1),
                     corrected_api_assertions_passed=272,operand_reference_api_assertions_failed=16,
                     hashes_verified=True),indent=2))
