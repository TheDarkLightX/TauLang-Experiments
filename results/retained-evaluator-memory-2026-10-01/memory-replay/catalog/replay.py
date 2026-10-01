#!/usr/bin/env python3
"""Compare ordinary VM-adapter solving with retained evaluation on saved inputs."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,platform,statistics,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'adapters'),str(ROOT/'vm/tools')]
import native_tau as ordinary
import native_tau_eval as retained
from compile_tau import Parser,step

def read(name):
    return json.loads((ROOT/'inputs'/name).read_text())

def memory_kib(pid):
    return retained.rss_kib(pid)

def checked_step(client,tree,values):
    expected=tuple(step(tree,tuple(values)))
    start=time.perf_counter()
    actual=tuple(client.step(values))
    elapsed=time.perf_counter()-start
    if actual!=expected:
        raise ValueError('Output mismatch: '+repr({'expected':expected,'actual':actual}))
    return {'seconds':elapsed,'outputs':list(actual)}

def trace(client,tree,program,private,expected_steps):
    state=ordinary.initial_state();rows=[]
    for _ in range(expected_steps):
        values=ordinary.inputs_for(program,private,state)
        row=checked_step(client,tree,values);rows.append(row)
        state=ordinary.state_from(row['outputs'])
        if state['halted']:break
    if len(rows)!=expected_steps or not state['halted']:
        raise ValueError('Unexpected trace length or final state')
    return rows

def run(binary,output,repeats,count,cpu):
    if cpu is not None:
        if not hasattr(os,'sched_setaffinity'):
            raise ValueError('--cpu requires Linux')
        os.sched_setaffinity(0,{cpu})
    if output.exists():
        raise ValueError('Output directory must be new')
    output.mkdir(parents=True)
    source=(ROOT/'vm/spec/vm.tau').read_text()
    tree=Parser(source).parse()
    vectors=read('conformance-cases.json')['inputs']
    cases=read('distinct-cases.json')['inputs'][:count]
    programs=read('programs.json')
    version=subprocess.check_output([str(binary),'--version'],text=True,timeout=15)
    if not ordinary.matches_pinned_version(version):
        raise ValueError('Build the pinned Tau revision described in README.md')
    result={'status':'incomplete','version':version.strip(),
            'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
            'vm_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'platform':platform.platform(),'cpu_affinity':cpu,'repeats':[],
            'distinct':{},'scope':'Wall time includes the Python adapter and pipe round trips. RSS samples are not lifetime peaks.'}
    def opened(arm):
        os.environ['TAU_CONCRETE_EVAL']='1' if arm=='retained' else '0'
        return (retained.EvalspecTau if arm=='retained' else ordinary.NativeTau)(binary,source=source)
    try:
        for index in range(repeats):
            order=['ordinary','retained'] if index%2==0 else ['retained','ordinary']
            for arm in order:
                start=time.perf_counter()
                with opened(arm) as client:
                    setup=time.perf_counter()-start
                    mem={'after_setup_kib':memory_kib(client.process.pid)}
                    if arm=='retained':
                        mem.update(after_load_kib=client.rss_after_load_kib,
                                   after_admission_kib=client.rss_after_admit_kib)
                    workload={'smoke':trace(client,tree,programs['smoke'],[],3),
                              'payroll':trace(client,tree,programs['payroll'],[10],17),
                              'conformance':[checked_step(client,tree,v) for v in vectors]}
                    mem['after_workload_kib']=memory_kib(client.process.pid)
                times=[v['seconds'] for rows in workload.values() for v in rows]
                row={'repeat':index+1,'arm':arm,'order':order,'setup_seconds':setup,
                     'step_median_seconds':statistics.median(times),'step_sum_seconds':sum(times),
                     'steps':len(times),'memory':mem,'workload':workload}
                if arm=='retained':
                    row['setup_breakdown_seconds']={'load':client.load_seconds,
                        'admission':client.admit_seconds}
                    row['admission']=client.admit_frame
                result['repeats'].append(row)
                print(json.dumps({k:v for k,v in row.items() if k!='workload'}),flush=True)
        for arm in ['retained','ordinary']:
            start=time.perf_counter()
            with opened(arm) as client:
                setup=time.perf_counter()-start
                rows=[checked_step(client,tree,v) for v in cases]
                mem=memory_kib(client.process.pid)
            result['distinct'][arm]={'setup_seconds':setup,'rows':rows,
                'step_sum_seconds':sum(v['seconds'] for v in rows),'rss_after_workload_kib':mem}
        med={a:statistics.median(x['step_median_seconds'] for x in result['repeats'] if x['arm']==a)
             for a in ['ordinary','retained']}
        total={a:result['distinct'][a]['setup_seconds']+result['distinct'][a]['step_sum_seconds']
               for a in ['ordinary','retained']}
        result['summary']={'median_step_ratio':med['ordinary']/med['retained'],
            'setup_inclusive_distinct_ratio':total['ordinary']/total['retained'],
            'checked_transitions_per_arm':55*repeats+len(cases),'distinct_inputs':len(cases)}
        result['status']='passed'
    except Exception as error:
        result['status']='failed';result['error']=str(error)
        raise
    finally:
        (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary',type=pathlib.Path)
    parser.add_argument('--output',type=pathlib.Path,required=True)
    parser.add_argument('--repeats',type=int,default=5)
    parser.add_argument('--count',type=int,default=256)
    parser.add_argument('--cpu',type=int)
    a=parser.parse_args()
    if not 1<=a.repeats<=10 or not 1<=a.count<=256:
        parser.error('Use 1..10 repeats and 1..256 saved inputs')
    run(a.binary.resolve(),a.output,a.repeats,a.count,a.cpu)
