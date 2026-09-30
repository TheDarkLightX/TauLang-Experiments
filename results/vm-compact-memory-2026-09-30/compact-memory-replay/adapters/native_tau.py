#!/usr/bin/env python3
"""Execute the Tau-authored step relation with concrete inputs in native Tau.

The shell feeds back state and supplies program/input words. Tau computes all
output fields, including instruction fetch and memory changes. No instruction
implementation or expression evaluator is used on this execution path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import tempfile
import time

from compile_tau import INPUT_PATHS, OUTPUT_PATHS, INPUT_WIDTHS, OUTPUT_WIDTHS, ROOT, Parser, assignments

TAU_COMMIT = "15d091723f2b17175bc41f9a9ab6fb5a7760751f"
# harness knobs: deadlines stretch under callgrind (seconds)
DEADLINE = float(os.environ.get('TAU_HARNESS_DEADLINE', '30'))
LOAD_DEADLINE = float(os.environ.get('TAU_HARNESS_LOAD_DEADLINE', '120'))
TAU_PROMPT = re.compile(rb'(?:^|\n)\[[^\n]*\] tau> $')


def matches_pinned_version(version):
    """Git may extend its displayed abbreviation as the repository grows."""
    lines = version.strip().splitlines()
    match = re.fullmatch(r'Tau Language Framework version 0\.7\.0-alpha \(([0-9a-f]{7,40})\)',
                         lines[0]) if lines else None
    return match is not None and TAU_COMMIT.startswith(match[1])
NAMES = {"i1": "a", "i2": "b", "i3": "c", "o1": "x", "o2": "y"}


def native_path(path):
    root, dot, tail = path.partition(".")
    return NAMES[root] + dot + tail


def word_list(value, maximum=16):
    if type(value) is not list or len(value) > maximum or any(type(x) is not int or not 0 <= x < 1 << 32 for x in value):
        raise ValueError(f"expected at most {maximum} unsigned 32-bit values")
    return value


def load_program(path):
    value = strict_json(path)
    if type(value) is not dict or set(value) != {"version", "instructions", "public_memory"} or type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("invalid program schema/version")
    instructions = value["instructions"]
    if type(instructions) is not list or not 1 <= len(instructions) <= 32:
        raise ValueError("program must have 1..32 instructions")
    for word in instructions:
        word_list(word, 2)
        if len(word) != 2:
            raise ValueError("instructions require opcode and operand")
    addresses = word_list(value["public_memory"])
    if any(x >= 16 for x in addresses) or addresses != sorted(set(addresses)):
        raise ValueError("public memory addresses must be strictly increasing in 0..15")
    return value


def strict_json(path):
    with open(path, "rb") as stream:
        data = stream.read((1 << 20) + 1)
    if len(data) > 1 << 20:
        raise ValueError("JSON exceeds 1 MiB")

    def object_pairs(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate JSON field")
            obj[key] = value
        return obj
    return json.loads(data, object_pairs_hook=object_pairs)


def initial_state():
    return dict(accumulator=0, pc=0, memory=[0] * 16, input_cursor=0, halted=0)


def inputs_for(program, private_input, state):
    code = [field for word in program["instructions"] for field in word]
    return tuple(code + [0] * (64 - len(code)) + [len(program["instructions"])] +
                 private_input + [0] * (16 - len(private_input)) + [len(private_input)] +
                 [state["accumulator"], state["pc"]] + state["memory"] +
                 [state["input_cursor"], state["halted"]])


def state_from(outputs):
    if outputs[20] != 0:
        raise ValueError("Tau rejected the instruction/state")
    return dict(accumulator=outputs[0], pc=outputs[1], memory=list(outputs[2:18]),
                input_cursor=outputs[18], halted=outputs[19])


class NativeTau:
    def __init__(self, binary, source=None):
        self.process = None
        self.io_selector = None
        self.binary = str(Path(binary).resolve())
        self.source = source if source is not None else (ROOT / "spec/vm.tau").read_text()
        parser = Parser(self.source)
        root = parser.parse()
        self.function_widths = {name: width for name, (_, width, _) in parser.functions.items()}
        self.closed_call = re.compile(r'\b(?:' + '|'.join(map(re.escape,[*self.function_widths,'min','max'])) + r')\([^()]*\)')
        self.leaves = []
        self.leaf_values = []
        def selector(node):
            if node.op == 'if':
                guard, yes, no = node.args
                return f"(({parser.spans[id(guard)]}) ? {selector(yes)} : {selector(no)})"
            index = len(self.leaves)
            self.leaves.append(parser.spans[id(node)])
            expressions = assignments(node)
            self.leaf_values.append([parser.spans[id(expressions[f'o{i+1}'])] for i in range(len(OUTPUT_PATHS))])
            return f"(z0:bv[32] = {{{index}}}:bv[32])"
        self.selector = selector(root)
        self.prefix = self.source.split("i1:Program", 1)[0]
        self.body = self.source.split("always ", 1)[1].strip().removesuffix(".")
        self.scratch = tempfile.TemporaryDirectory(prefix="taufold-tau-")
        result = subprocess.run([self.binary, "--version"], cwd=self.scratch.name,
                                capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not matches_pinned_version(result.stdout):
            self.close()
            raise ValueError(f"native execution requires pinned Tau commit {TAU_COMMIT}")
        self.version = result.stdout.strip()
        self.ground_cache = {}
        try:
            self._start_repl()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                try:
                    self.process.stdin.close()
                except OSError:
                    pass
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(self.process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    self.process.wait()
            if self.io_selector is not None:
                self.io_selector.close()
            for pipe in (self.process.stdin, self.process.stdout,
                         self.process.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()
            self.process = None
            self.io_selector = None
        self.scratch.cleanup()

    def _invalidate_process(self):
        """Make a failed or desynchronized session impossible to reuse."""
        if self.process is None:
            return
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.process.wait()
        if self.io_selector is not None:
            self.io_selector.close()
        for pipe in (self.process.stdin, self.process.stdout,
                     self.process.stderr):
            if pipe is not None and not pipe.closed:
                pipe.close()
        self.process = None
        self.io_selector = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @staticmethod
    def request_line(text):
        return " ".join(re.sub(r"#[^\n]*", "", text).splitlines()) + "\n"

    def _start_repl(self):
        self.process = subprocess.Popen(
            [self.binary, "--severity", "error", "--benchmarks", "false",
             "--charvar", "false", "--color", "false", "-q"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.scratch.name, bufsize=0, start_new_session=True)
        self.io_selector = selectors.DefaultSelector()
        for name, pipe in (("stdout", self.process.stdout),
                           ("stderr", self.process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            self.io_selector.register(pipe, selectors.EVENT_READ, name)
        self._read_response()
        deadline = time.monotonic() + DEADLINE
        self._send(self.request_line(self.prefix), deadline)
        _, error = self._read_response(deadline)
        if "error" in error.lower():
            raise ValueError("native Tau did not accept the VM definitions")

    def _send(self, request, deadline):
        if self.process is None or self.process.poll() is not None:
            raise ValueError("native Tau exited before accepting a query")
        payload = memoryview(request.encode())
        os.set_blocking(self.process.stdin.fileno(), False)
        with selectors.DefaultSelector() as writer:
            writer.register(self.process.stdin, selectors.EVENT_WRITE)
            while payload:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError("native Tau step exceeded 30 seconds")
                if self.process.poll() is not None:
                    raise ValueError("native Tau exited before accepting a query")
                if not writer.select(min(remaining, 0.1)):
                    continue
                try:
                    written = os.write(self.process.stdin.fileno(), payload)
                except BlockingIOError:
                    continue
                if written <= 0:
                    raise ValueError("native Tau stopped accepting query input")
                payload = payload[written:]

    def _read_response(self, deadline=None):
        output, error = bytearray(), bytearray()
        if deadline is None:
            deadline = time.monotonic() + DEADLINE
        while True:
            if TAU_PROMPT.search(output):
                return output.decode(), error.decode()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("native Tau step exceeded 30 seconds")
            for key, _ in self.io_selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if chunk:
                    (output if key.data == "stdout" else error).extend(chunk)
                elif self.process.poll() is not None:
                    raise ValueError("native Tau exited before producing a prompt")
            if self.process.poll() is not None:
                raise ValueError("native Tau exited before producing a prompt")

    def concrete(self, text, inputs):
        if len(inputs) != len(INPUT_WIDTHS) or any(type(v) is not int or not 0 <= v < 1 << w
                                                  for v, w in zip(inputs, INPUT_WIDTHS)):
            raise ValueError("invalid Tau input vector")

        constants = {path: f"{{{value}}}:bv[{width}]" for path, value, width in zip(INPUT_PATHS, inputs, INPUT_WIDTHS)}
        def replace(match):
            path = match[1] + match[2]
            return constants[path] if path in constants else native_path(path)
        return re.sub(r"\b([io]\d+)\[t\]((?:\.[A-Za-z][A-Za-z0-9_]*)*)", replace, text)

    def formula(self, inputs):
        formula = self.concrete(self.body, inputs)
        # A bijective wire encoding avoids native Tau's costly simultaneous
        # model search for 21 separate variables. All 21 equations remain in
        # the direct formula; each member names a slice of the same 672-bit word.
        for index,path in sorted(enumerate(OUTPUT_PATHS),key=lambda item:-len(item[1])):
            name = native_path(path)
            formula = re.sub(r'\b'+re.escape(name)+r'(?![A-Za-z0-9_.])',
                             f'((bv[32]) (z0:bv[672] >> {{{32*index}}}:bv[672]))',formula)
        return formula

    def step(self, inputs):
        # Total guards contain inputs only. Tau first selects a leaf of the
        # original conditional tree, then solves that leaf for the full ADT
        # output. No Python/Rust evaluator is used to decide a guard or output.
        selected = self.fold_lookups(self.concrete(self.selector, inputs))
        raw = self.solve(selected)
        match = re.search(r"z0\s*:=\s*\{\s*(\d+)\s*\}:bv\[32\]", raw)
        if match is None or not 0 <= int(match[1]) < len(self.leaves):
            raise ValueError("native Tau did not select a valid transition leaf")
        values = [self.concrete(value,inputs) for value in self.leaf_values[int(match[1])]]
        packed = ' | '.join(f'(((bv[672]) ({value})) << {{{32*i}}}:bv[672])' for i,value in enumerate(values))
        return self.packed_output(self.solve(self.fold_lookups(f'z0:bv[672] = ({packed})')))

    def direct_step(self, inputs):
        """Unstaged reference evaluation for differential conformance checks."""
        return self.packed_output(self.solve(self.formula(inputs)))

    @staticmethod
    def packed_output(solution):
        match = re.fullmatch(r'solution:\s*\{\s*z0\s*:=\s*\{\s*(\d+)\s*\}:bv\[672\]\s*\}',solution)
        if match is None or int(match[1]) >= 1 << 672:
            raise ValueError('native Tau returned an invalid packed output')
        word = int(match[1])
        return tuple((word >> (32*i)) & 0xffffffff for i in range(len(OUTPUT_PATHS)))

    def fold_lookups(self, formula):
        # These closed terms recur throughout the formula. Ask Tau to evaluate
        # them once, then substitute Tau's values. This shell does no fetching,
        # branching, arithmetic, or expression evaluation of its own.
        while True:
            calls = list(dict.fromkeys(self.closed_call.findall(formula)))
            if not calls:
                return formula
            missing = [call for call in calls if call not in self.ground_cache]
            for offset in range(0,len(missing),4):
                batch=missing[offset:offset+4]
                widths=[self.function_widths.get(call.split('(',1)[0],int(re.search(r'bv\[(\d+)\]',call)[1])) for call in batch]
                query = " && ".join(f"z{index}:bv[{width}] = {call}" for index,(call,width) in enumerate(zip(batch,widths)))
                raw = self.solve(query)
                matches = re.findall(r"z(\d+)\s*:=\s*\{\s*(\d+)\s*\}:bv\[(\d+)\]", raw)
                values = {int(index): (int(value),int(width)) for index,value,width in matches}
                if len(matches)!=len(batch) or set(values)!=set(range(len(batch))) or any(values[i][1]!=w or values[i][0]>=1<<w for i,w in enumerate(widths)):
                    raise ValueError("native Tau did not evaluate all closed terms")
                for index,call in enumerate(batch):
                    self.ground_cache[call]=f"{{{values[index][0]}}}:bv[{widths[index]}]"
            for call in calls:
                formula = formula.replace(call,self.ground_cache[call])

    def solve(self, formula):
        # Definitions are loaded once when the verifier is created. Private
        # constants still travel over stdin and every query has its own deadline.
        deadline = time.monotonic() + DEADLINE
        try:
            self._send(self.request_line("solve " + formula + "."), deadline)
            output, error = self._read_response(deadline)
        except Exception:
            self._invalidate_process()
            raise
        if "error" in error.lower() or "solution:" not in output:
            self._invalidate_process()
            raise ValueError("native Tau did not produce a solution")
        solution = "solution:" + output.rsplit("solution:", 1)[1].strip()
        solution = solution[:solution.rfind("\n}") + 2]
        solution = solution.replace("solution:{", "solution: {", 1)
        if not solution.startswith("solution: {") or not solution.endswith("}"):
            self._invalidate_process()
            raise ValueError("unexpected native Tau output")
        return solution

def execute(program, private_input, binary, on_step=None, source=None):
    word_list(private_input)
    trace = [initial_state()]
    with NativeTau(binary, source=source) as tau:
        for _ in range(512):
            trace.append(state_from(tau.step(inputs_for(program, private_input, trace[-1]))))
            if on_step is not None:
                on_step(len(trace) - 1)
            if trace[-1]["halted"] == 1:
                return {"private_input": list(private_input), "salt": list(os.urandom(32)), "trace": trace}
    raise ValueError("program did not halt within 512 transitions")


def save_private(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(value, stream)
        stream.write("\n")


def source_hash():
    return hashlib.sha256((ROOT / "spec/vm.tau").read_bytes()).hexdigest()
