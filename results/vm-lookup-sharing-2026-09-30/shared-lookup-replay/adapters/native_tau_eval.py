#!/usr/bin/env python3
"""Adapter variant for the retained-DAG evaluator (Tau `evalspec`, TAU_CONCRETE_EVAL=1).

Loads the complete VM spec once (history %1), asks Tau for the admitted input and
output names, and then sends one `evalspec %1 v1 ... vN` line per transition.
Everything else (version check, process lifetime, framing, deadlines) is the
persistent adapter's. No Python evaluation of any guard or output.
"""
from __future__ import annotations
import importlib.util, json, os, pathlib, re, time
spec = importlib.util.spec_from_file_location('native_tau_persistent', pathlib.Path(__file__).with_name('native_tau.py'))
nt = importlib.util.module_from_spec(spec); spec.loader.exec_module(nt)
from compile_tau import INPUT_PATHS, OUTPUT_PATHS, INPUT_WIDTHS, OUTPUT_WIDTHS

def rss_kib(pid):
    path = pathlib.Path(f'/proc/{pid}/status')
    if path.exists():
        return int(re.search(r'^VmRSS:\s+(\d+) kB', path.read_text(), re.M)[1])
    return int(nt.subprocess.check_output(['ps', '-o', 'rss=', '-p', str(pid)], text=True).strip())

def parse_frame(raw):
    """The machine-readable response: one `evalspec-result:` line of name=value
    pairs followed by `evalspec-end`.  Anything else is a protocol error."""
    lines = raw.splitlines()
    starts = [i for i, l in enumerate(lines) if l.startswith('evalspec-result: ')]
    if len(starts) != 1: raise ValueError("expected exactly one evalspec-result line")
    i = starts[0]
    if i + 1 >= len(lines) or lines[i + 1] != 'evalspec-end': raise ValueError("missing evalspec-end terminator")
    fields = {}
    for pair in lines[i][len('evalspec-result: '):].split(' '):
        name, eq, value = pair.partition('=')
        if not eq or not name or name in fields: raise ValueError("malformed frame field " + pair)
        fields[name] = value
    return fields

def tau_name_to_path(name):
    name = re.sub(r':bv\[\d+\]$', '', name)
    return name.replace('[t]', '')

class EvalspecTau(nt.NativeTau):
    query_log = None
    def _start_repl(self):
        self.process = nt.subprocess.Popen(
            [self.binary, "--severity", "error", "--benchmarks", "false",
             "--charvar", "false", "--color", "false", "-q"],
            stdin=nt.subprocess.PIPE, stdout=nt.subprocess.PIPE, stderr=nt.subprocess.PIPE,
            cwd=self.scratch.name, bufsize=0, start_new_session=True,
            env={**os.environ, "TAU_CONCRETE_EVAL": "1"})
        self.io_selector = nt.selectors.DefaultSelector()
        for name, pipe in (("stdout", self.process.stdout), ("stderr", self.process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            self.io_selector.register(pipe, nt.selectors.EVENT_READ, name)
        self._read_response()
        deadline = time.monotonic() + nt.LOAD_DEADLINE
        t0 = time.monotonic()
        self._send(self.request_line(self.source), deadline)
        output, error = self._read_response(deadline)
        self.load_seconds = time.monotonic() - t0
        if "error" in error.lower() or "%1" not in output:
            raise ValueError("native Tau did not accept the VM specification")
        self.rss_after_load_kib = rss_kib(self.process.pid)
        t0 = time.monotonic()
        raw = self.command("evalspec %1")
        self.admit_seconds = time.monotonic() - t0
        self.rss_after_admit_kib = rss_kib(self.process.pid)
        self.admit_frame = parse_frame(raw)
        if self.admit_frame.get('status') != 'admitted':
            raise ValueError("native Tau did not admit the VM specification: " + str(self.admit_frame))
        m_in = re.search(r'^inputs:((?: \S+)*)$', raw, re.M); m_out = re.search(r'^outputs:((?: \S+)*)$', raw, re.M)
        m_shape = re.search(r'^decisions: (\d+) leaves: (\d+) expressions: (\d+)$', raw, re.M)
        if not (m_in and m_out and m_shape):
            raise ValueError("native Tau did not admit the VM specification")
        self.shape = dict(decisions=int(m_shape[1]), leaves=int(m_shape[2]), expressions=int(m_shape[3]))
        self.tau_inputs = m_in[1].split(); self.tau_outputs = m_out[1].split()
        index = {p: i for i, p in enumerate(INPUT_PATHS)}
        self.input_order = []
        for name in self.tau_inputs:
            path = tau_name_to_path(name)
            if path not in index: raise ValueError(f"unexpected Tau input {name}")
            self.input_order.append(index[path])
        outs = [tau_name_to_path(n) for n in self.tau_outputs]
        if sorted(outs) != sorted(OUTPUT_PATHS) or len(outs) != len(OUTPUT_PATHS):
            raise ValueError("Tau output set differs from the VM output tuple")
        self.output_names = {tau_name_to_path(n): n for n in self.tau_outputs}

    def command(self, line):
        deadline = time.monotonic() + nt.DEADLINE
        try:
            self._send(line + "\n", deadline)
            output, error = self._read_response(deadline)
        except Exception:
            self._invalidate_process(); raise
        if "error" in error.lower():
            self._invalidate_process()
            raise ValueError("native Tau reported an error: " + error.strip()[:200])
        return output

    def step(self, inputs):
        if len(inputs) != len(INPUT_WIDTHS) or any(type(v) is not int or not 0 <= v < 1 << w for v, w in zip(inputs, INPUT_WIDTHS)):
            raise ValueError("invalid Tau input vector")
        line = "evalspec %1 " + " ".join(str(inputs[i]) for i in self.input_order)
        t0 = time.monotonic(); raw = self.command(line); dt = time.monotonic() - t0
        if EvalspecTau.query_log is not None:
            EvalspecTau.query_log.write(json.dumps({'bytes': len(line), 'seconds': dt, 'query': line, 'solution': raw}) + '\n')
        frame = parse_frame(raw)
        if frame.get('status') != 'ok': raise ValueError("native Tau declined the valuation: " + str(frame))
        if int(frame['outputs']) != len(OUTPUT_PATHS): raise ValueError("unexpected output count")
        bindings = {}
        for name, token in frame.items():
            if name in ('status', 'leaf', 'outputs'): continue
            if not re.fullmatch(r'[0-9]+', token) or (len(token) > 1 and token[0] == '0'):
                raise ValueError("unrecognized output value")
            path = tau_name_to_path(name)
            if path in bindings: raise ValueError(f"duplicate binding {name}")
            bindings[path] = int(token)
        values = []
        for path, width in zip(OUTPUT_PATHS, OUTPUT_WIDTHS):
            if path not in bindings: raise ValueError(f"missing output {path}")
            v = int(bindings[path])
            if v >= 1 << width: raise ValueError("output out of range")
            values.append(v)
        if len(bindings) != len(OUTPUT_PATHS): raise ValueError("unexpected bindings")
        return tuple(values)
