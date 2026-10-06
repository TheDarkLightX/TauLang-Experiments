#!/usr/bin/env python3
"""Recheck retained answers, generated inputs, search and timing summaries.

This checks stored evidence. It does not execute Tau or prove its implementation.
"""
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
E=ROOT/'evidence/earlier'
sys.path.insert(0,str(ROOT/'repro'))
import check_finite_semantics as finite
import check_outputs as outputs
import tau_dispatch_blowup as generator

def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def plain(path): return re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',path.read_text())
def values(path,stream):
    return [(int(i),v) for i,v in re.findall(rf'{stream}\[(\d+)\]\s*:=\s*(\S+)',plain(path))]

def process(folder,expected=None):
    a=read(folder/'result.json')
    assert a['ok'] and a['rc']==0 and a['stopped'] is None,folder
    for name,h in a['sha256'].items(): assert digest(folder/name)==h,(folder,name)
    expected=a['expected_o5'] if expected is None else list(map(str,expected))
    assert a['expected_o5']==expected
    actual=values(folder/'stdout.txt','o5')
    assert actual==list(enumerate(expected,a['o5_first_step'])),folder
    assert [v for _,v in actual]==a['actual_o5'] and a['o5_indices_ok']
    assert re.search(r'\bError\b|\bUNKNOWN\b',plain(folder/'stdout.txt')+plain(folder/'stderr.txt')) is None
    return a

def check():
    count=0
    for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
        h,name=line.split('  ',1); assert digest(ROOT/name)==h,name;count+=1
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/'search'
        subprocess.run([sys.executable,'-B',str(ROOT/'repro/discover_rule_guards.py'),str(target)],
                       check=True,stdout=subprocess.DEVNULL)
        for name in ['results.json','bank.json']:
            assert read(target/name)==read(E/'rule-discovery-pilot'/name)
    finite_answers=0
    for name in ['finite-growth-only','finite-candidate','finite-candidate-split-off',
                 'finite-candidate-defelim-off','discovery-native-replay','discovery-native-defelim-off']:
        folder=E/name; d=read(folder/'result.json'); cases=read(folder/'cases.json')
        want=finite.make_cases() if name.startswith('finite-') else [
            dict(c,expected='T' if c['expected'] else 'F') for c in read(E/'rule-discovery-pilot/bank.json')]
        assert cases==want,name
        answers=re.findall(r'^%\d+: (T|F)\s*$',plain(folder/'stdout.txt'),re.M)
        assert answers==[c['expected'] for c in cases] and len(answers)==d['answers']==d['cases']
        assert d['ok'] and d['exit_code']==0 and d['mismatches']==[]
        assert re.search(r'\bError\b|\bUNKNOWN\b',plain(folder/'stdout.txt')+plain(folder/'stderr.txt')) is None
        finite_answers+=len(answers)

    timing=read(E/'sequential-comparison/results.json');attempts=0
    assert timing['ok'] and timing['binary_sha256']==timing['binary_sha256_after']
    for row in timing['rows']:
        kind,size,path=row['kind'],row['size'],row['path']
        wl=generator.terms_workload(size,8) if kind=='terms' else generator.chain_workload(size,8,False)
        if path=='repeated_steps':wl.checks*=20
        for name,agg in row['variants'].items():
            assert agg['ok'] and len(agg['attempts'])==3
            for i,a in enumerate(agg['attempts'],1):
                folder=E/'sequential-comparison'/f'{kind}-{size}-{path}-{name}-{i}'
                assert process(folder,[c.expect for c in wl.checks])==a
                assert (folder/'boot.tau').read_text()==(generator.ROUTER if path=='revision' else wl.spec)
                assert (folder/'stdin.txt').read_text()==(generator.stdin_router(wl) if path=='revision' else generator.stdin_spec(wl))
                attempts+=1
            for field in ['cpu_s','wall_s','peak_rss_mib']:
                assert statistics.median(a[field] for a in agg['attempts'])==agg['median_'+field]
    assert attempts==81

    for row in read(E/'independent-rule-outputs/results.json')['rows']:
        kind=row['kind'];wl=generator.terms_workload(12,8) if kind=='terms' else generator.chain_workload(12,8,False)
        wl.checks=outputs.make_checks(kind,12)
        folder=E/'independent-rule-outputs'/f"{kind}-{row['variant']}"
        assert process(folder,[c.expect for c in wl.checks])==row['result']
        assert (folder/'boot.tau').read_text()==wl.spec
        assert (folder/'stdin.txt').read_text()==generator.stdin_spec(wl)
        assert values(folder/'stdout.txt','o1')==[(i,c.values[1]) for i,c in enumerate(wl.checks)]
    for row in read(E/'wide-checks/results.json')['rows']:
        kind,size,route=row['kind'],row['size'],row['route']
        wl=generator.terms_workload(size,384) if kind=='terms' else generator.chain_workload(size,384,False)
        folder=E/'wide-checks'/f"{kind}-{size}-{route}-{row['variant']}"
        assert process(folder,[c.expect for c in wl.checks])==row['result']
        assert (folder/'boot.tau').read_text()==(wl.spec if route=='spec' else generator.ROUTER)
        assert (folder/'stdin.txt').read_text()==(generator.stdin_spec(wl) if route=='spec' else generator.stdin_router(wl))
        start=0 if route=='spec' else 2
        assert [(i,v) for i,v in values(folder/'stdout.txt','o1') if i>=start]==[(i+start,c.values[1]) for i,c in enumerate(wl.checks)]
    for row in read(E/'reparse-checks/results.json')['rows']:
        kind,size,producer=row['kind'],row['size'],row['producer']
        wl=generator.terms_workload(size,8) if kind=='terms' else generator.chain_workload(size,8,False)
        source=E/'reparse-checks'/f'{kind}-{size}-revision-{producer}'
        updates=generator.UPDATED.findall(plain(source/'stdout.txt'));assert len(updates)==2
        if row['path']=='revision':
            process(source,[c.expect for c in wl.checks])
        else:
            folder=E/'reparse-checks'/f"{kind}-{size}-reparse-{producer}-on-{row['consumer']}"
            assert process(folder,[c.expect for c in wl.checks])==row['result']
            assert (folder/'boot.tau').read_text()==updates[-1]+'.\n'
            assert values(folder/'stdout.txt','o1')==[(i,c.values[1]) for i,c in enumerate(wl.checks)]
    for group in ['control-checks','timed-controls']:
        for row in read(E/group/'results.json')['rows']:
            folder=E/group/(Path(row['source']).stem+'-'+row['variant'])
            a=process(folder);assert a==row['result']
            vals=dict(re.findall(r'^(o\d+\[\d+\])\s*:=\s*(.*)$',plain(folder/'stdout.txt'),re.M))
            assert all(vals.get(k)==v for k,v in a['expected_values'].items())
    tests=E/'tests'
    focused=ET.parse(tests/'focused-build2.xml').getroot()
    initial=ET.parse(tests/'repl-build1.xml').getroot()
    retry=ET.parse(tests/'repl-build1-environment-retry.xml').getroot()
    assert focused.attrib['tests']=='17' and focused.attrib['failures']=='0'
    assert initial.attrib['tests']=='2566' and initial.attrib['failures']=='7'
    failed={t.attrib['name'] for t in initial.findall('testcase') if t.find('failure') is not None}
    assert len(failed)==7 and failed=={t.attrib['name'] for t in retry.findall('testcase')}
    assert retry.attrib['failures']=='0'
    for t in initial.findall('testcase'):
        if t.attrib['name'] in failed:
            assert "'array' file not found" in ''.join(t.itertext())
    print(f'PASS: {count} file hashes; regenerated rule search; {finite_answers} finite answers; '
          f'{attempts} timing attempts; output, reparse, wide and control records; focused and REPL test accounting.')

if __name__=='__main__':check()
