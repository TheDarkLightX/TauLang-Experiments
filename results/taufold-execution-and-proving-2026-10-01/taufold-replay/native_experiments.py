#!/usr/bin/env python3
"""Compare native Tau execution and per-run constant binding on synthetic apps."""
import argparse, hashlib, json, os, re, sys, time
from pathlib import Path

sys.dont_write_bytecode = True
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--catalog', type=Path, required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--stock', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--repeats', type=int, default=3)
p.add_argument('--apps', nargs='+', default=['auction', 'payroll', 'inference'])
p.add_argument('--arms', nargs='+', default=['stock', 'retained', 'program_bound', 'run_bound'])
a = p.parse_args()
catalog = a.catalog.resolve()
sys.path[:0] = [str(catalog), str(catalog/'adapters'), str(catalog/'vm/tools')]
import replay as common
import native_tau_eval as retained
from native_tau_compact import CompactMemoryTau
from compile_tau import INPUT_PATHS, Parser, step

PIN = 'a739b90259729590dee7b424df05ba65bfdeacf2'
common.ordinary.TAU_COMMIT = PIN
retained.nt.TAU_COMMIT = PIN
source = (a.source/'spec/vm.tau').read_text()
assert source == (catalog/'vm/spec/vm.tau').read_text()
model = Parser(source).parse()
os.environ.update({name: '1' for name in ['TAU_EVAL_DECIMAL_ONLY',
    'TAU_EVAL_TRANSIENT_NORMALIZE','TAU_EVAL_TRIM','TAU_EVAL_ARENA_OUTPUTS',
    'TAU_EVAL_FLAT_LEAVES','TAU_EVAL_RELEASE_PARSE_SCRATCH']})
os.environ.update(TAU_MEMORY_TELEMETRY='0', TAU_CONCRETE_EVAL='1')

class BoundTau(CompactMemoryTau):
    def __init__(self, binary, source, values, count):
        self.bound = tuple(values[:count])
        super().__init__(binary, source)

    def _send(self, request, deadline):
        if not self.loaded_shared_source:
            for path, value in zip(INPUT_PATHS, self.bound):
                root, tail = path.split('.', 1)
                name = root + '[t].' + tail
                self.compact_source, n = re.subn(re.escape(name) + r'(?![A-Za-z0-9_])',
                    '{' + str(value) + '}:bv[32]', self.compact_source)
                if n == 0: raise ValueError('Missing fixed source field: ' + path)
        return super()._send(request, deadline)

    def step(self, values):
        if tuple(values[:len(self.bound)]) != self.bound:
            raise ValueError('Fixed values changed; create a new execution')
        return super().step(values)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
a.output.mkdir(exist_ok=False, parents=True)
data = {'status':'incomplete', 'scope':'Synthetic public examples; native execution only.',
        'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'candidate_sha256':sha(a.candidate), 'stock_sha256':sha(a.stock), 'rows':[]}
def save():
    (a.output/'results.json').write_text(json.dumps(data, indent=2)+'\n')

try:
    for repeat in range(a.repeats):
        arms = a.arms if repeat % 2 == 0 else list(reversed(a.arms))
        for name in a.apps:
            program = json.loads((a.source/'examples'/f'{name}.json').read_text())
            private = json.loads((a.source/'examples'/f'{name}.input.json').read_text())
            for arm in arms:
                initial = common.ordinary.initial_state()
                values = common.ordinary.inputs_for(program, private, initial)
                start = time.perf_counter()
                if arm == 'stock': client = common.ordinary.NativeTau(a.stock, source=source)
                elif arm == 'retained': client = CompactMemoryTau(a.candidate, source=source)
                else: client = BoundTau(a.candidate, source, values, 65 if arm=='program_bound' else 82)
                setup = time.perf_counter()-start
                with client:
                    trace = [initial]; rows = []
                    for index in range(512):
                        values = common.ordinary.inputs_for(program, private, trace[-1])
                        expected = tuple(step(model, values))
                        t = time.perf_counter(); actual = tuple(client.step(values)); elapsed=time.perf_counter()-t
                        if actual != expected: raise ValueError(f'{name}/{arm}: output mismatch at {index}')
                        trace.append(common.ordinary.state_from(actual))
                        rows.append({'seconds':elapsed, 'outputs':list(actual)})
                        if trace[-1]['halted']: break
                    if not trace[-1]['halted']: raise ValueError('Failed to terminate')
                    rss = common.memory_kib(client.process.pid)
                    shape = getattr(client, 'admit_frame', None)
                    if arm in ('program_bound','run_bound'):
                        wrong = list(values); wrong[0] ^= 1
                        try: client.step(wrong)
                        except ValueError as err:
                            if 'Fixed values changed' not in str(err): raise
                        else: raise ValueError('Changed fixed program was accepted')
                row={'app':name,'arm':arm,'repeat':repeat+1,'setup_seconds':setup,
                    'step_sum_seconds':sum(r['seconds'] for r in rows),
                    'total_seconds':setup+sum(r['seconds'] for r in rows),
                    'steps':len(rows),'rss_after_kib':rss,'admission':shape,'rows':rows,
                    'final_state':trace[-1]}
                data['rows'].append(row);save()
                # Synthetic witnesses stay separate from publication records.
                witness={'private_input':private,'salt':list(bytes(32)), 'trace':trace}
                wp=a.output/f'{name}-{arm}-{repeat+1}.witness.json'
                fd=os.open(wp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'w') as f: json.dump(witness,f)
                print(json.dumps({k:v for k,v in row.items() if k not in ('rows','final_state')}),flush=True)
    assert sha(a.candidate)==data['candidate_sha256'] and sha(a.stock)==data['stock_sha256']
    data['status']='passed'
except BaseException as error:
    data.update(status='failed',error=str(error));raise
finally: save()
