#!/usr/bin/env python3
"""Recheck retained outputs, generated inputs, medians and finite decisions."""
import argparse,hashlib,importlib.util,json,math,re,statistics,subprocess,sys,tempfile
from pathlib import Path
import xml.etree.ElementTree as ET

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(test,message):
    if not test:raise SystemExit(message)
def clean(s):return re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',s)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path);args=ap.parse_args();p=args.package.resolve()
    for line in (p/'MANIFEST.sha256').read_text().splitlines():
        h,n=line.split('  ',1);f=(p/n).resolve()
        require(f.is_relative_to(p),f'path leaves package: {n}')
        require(digest(f)==h,f'hash differs: {n}')
    sys.path.insert(0,str(p/'repro'))
    import tau_dispatch_blowup as g
    from check_single_step_semantics import make_bank
    count=0;outputs=0;data=read(p/'evidence/component-comparison/results.json')
    require(data['ok'] and data['binary_sha256']==data['binary_sha256_after'],'binary comparison incomplete')
    for row in data['rows']:
        kind,size,path=row['kind'],row['size'],row['path']
        wl=g.terms_workload(size,8) if kind=='terms' else g.chain_workload(size,8,False)
        if path=='repeated_steps':wl.checks*=20
        revision=path=='revision';expected=[str(c.expect) for c in wl.checks]
        require(row['checked_steps']==len(expected),'step count differs')
        require(set(row['variants'])=={'growth_only','one_step','structural'},'variant missing')
        for name,variant in row['variants'].items():
            require(variant['ok'] and len(variant['attempts'])==3,'attempt missing or failed')
            for i,attempt in enumerate(variant['attempts'],1):
                d=p/'evidence/component-comparison'/f'{kind}-{size}-{path}-{name}-{i}'
                require(read(d/'result.json')==attempt,'raw and aggregate attempt differ')
                require((d/'boot.tau').read_text()==(g.ROUTER if revision else wl.spec),'boot differs from generator')
                require((d/'stdin.txt').read_text()==(g.stdin_router(wl) if revision else g.stdin_spec(wl)),'input differs from generator')
                for f,h in attempt['sha256'].items():require(digest(d/f)==h,f'raw hash differs: {d.name}/{f}')
                out=clean((d/'stdout.txt').read_text());err=clean((d/'stderr.txt').read_text())
                actual=re.findall(r'o5\[(\d+)\]\s*:=\s*(\S+)',out)
                first=2 if revision else 0
                require(actual==list(zip(map(str,range(first,first+len(expected))),expected)),f'output mismatch: {d.name}')
                require(attempt['ok'] and attempt['rc']==0 and attempt['stopped'] is None,'failed process')
                require(not re.search(r'\b(error|unknown)\b',out+err,re.I),'diagnostic error')
                count+=1;outputs+=len(expected)
            for field in ('cpu_s','wall_s','peak_rss_mib'):
                actual=statistics.median(a[field] for a in variant['attempts'])
                require(math.isclose(actual,variant['median_'+field],rel_tol=0,abs_tol=1e-12),'median differs')
    require(count==63 and outputs==1809,'comparison coverage differs')
    bank=make_bank();api_count=0
    for name in ('growth-only','one-step','candidate'):
        d=p/'evidence'/('memoryless-'+name+'-api');r=read(d/'result.json')
        require(r['ok'] and r['formulas']==414 and r['queries']==828 and r['binary_unchanged'],'finite command run failed')
        require(read(d/'cases.json')==bank,'oracle cases differ')
        for w in (1,2,3):
            f=d/f'width-{w}';r=read(f/'result.json')
            require(r['ok'] and r['aligned'] and r['exit_code']==0,'query alignment failed')
            for n,h in r['files'].items():require(digest(f/n)==h,'finite transcript hash differs')
            commands=[];expected=[]
            for c in bank:
                if c['width']!=w:continue
                commands.extend(['sat always '+c['body'],'valid always '+c['body']])
                expected.extend(['T' if c['satisfiable'] else 'F','T' if c['valid'] else 'F'])
            chunks=clean((f/'stdout.txt').read_text()).split('tau> ');observed=[]
            for chunk in chunks:
                cmd,_,body=chunk.partition('\n')
                if cmd in commands:observed.append((cmd,re.findall(r'^%\d+: (T|F)\s*$',body,re.M)))
            require(observed==list(zip(commands,[[v] for v in expected])),'finite public answer differs')
            api_count+=len(observed)
    with tempfile.TemporaryDirectory() as tmp:
        regenerated=Path(tmp)/'bank.cpp'
        subprocess.run([sys.executable,'-B',str(p/'repro/generate_native_bank.py'),str(regenerated)],check=True)
        require(regenerated.read_bytes()==(p/'repro/direct-finite-bank.cpp').read_bytes(),'native bank differs from independent generator')
    direct={}
    for name,assertions in (('baseline',2484),('candidate',3223)):
        raw=(p/'evidence'/f'direct-finite-{name}.stdout').read_text()
        require('[doctest] Status: SUCCESS!' in raw and re.search(r'assertions:\s*'+str(assertions)+r'\s*\|\s*'+str(assertions)+r' passed',raw),'direct native check failed')
        rows=re.findall(r'^ROW (\d+) SAT ([01]) IMPLICATION ([01]) TRACE ([01])$',raw,re.M)
        require(len(rows)==414,'direct native coverage differs')
        for index,(n,sat,implication,trace) in enumerate(rows):
            require(int(n)==index and int(sat)==bank[index]['satisfiable'] and int(trace)==bank[index]['valid'],'direct native truth differs')
        direct[name]=rows
        if name=='candidate':require('ROUTE_COUNTS ACTIVE 718 DECLINED 110' in raw,'helper coverage differs')
    require(direct['baseline']==direct['candidate'],'direct implication comparison differs')
    native=ET.parse(p/'evidence/full-native.xml').getroot()
    retry=ET.parse(p/'evidence/native-retry.xml').getroot()
    first={t.get('name'):t for t in native.iter('testcase')}
    second={t.get('name'):t for t in retry.iter('testcase')}
    def passed(t):
        return t.get('status')=='run' and all(t.find(n) is None for n in ('failure','error','skipped'))
    require(len(first)==173 and len(second)==42,'native coverage differs')
    require('build_tree' in first and not passed(first['build_tree']),'initial setup failure missing')
    require(first['build_tree'].find('failure').get('message')=='Timeout','setup timeout record missing')
    missed={n for n,t in first.items() if n!='build_tree' and not passed(t)}
    require(len(missed)==41 and missed <= set(second),'missing native tests not retried')
    require(set(second)==missed|{'test_interpreter'},'retry selection differs')
    require(all(passed(t) for t in second.values()),'native retry failed')
    effective={n for n,t in first.items() if n!='build_tree' and passed(t)}|set(second)
    require(len(effective)==172,'native executable coverage incomplete')
    repl=ET.parse(p/'evidence/changed-repl.xml').getroot()
    require(len(list(repl.iter('testcase')))==2 and all(passed(t) for t in repl.iter('testcase')),'changed command tests failed')
    print(json.dumps({'timing_attempts':count,'checked_outputs':outputs,'finite_public_queries':api_count,'direct_finite_rows_compared':414,'native_tests_passed_across_initial_and_retry':len(effective),'initial_build_setup_timeout_retained':True,'changed_command_tests':2,'ok':True},indent=2))

if __name__=='__main__':main()
