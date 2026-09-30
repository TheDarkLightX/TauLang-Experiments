#!/usr/bin/env python3
"""Compile the explicitly bounded TauFold expression profile; reject everything else.

This compiler contains no instruction/opcode semantics. Those live in vm.tau.
Widths and assignments are checked before either evaluation or Rust emission.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATHS = tuple(f"i1.code.r{n}.{field}" for n in range(32) for field in ("opcode", "operand")) + ("i1.length",) + tuple(f"i2.words.r{n}" for n in range(16)) + ("i2.length", "i3.accumulator", "i3.pc") + tuple(f"i3.memory.r{n}" for n in range(16)) + ("i3.input_cursor", "i3.halted")
OUTPUT_PATHS = ("o1.accumulator", "o1.pc") + tuple(f"o1.memory.r{n}" for n in range(16)) + ("o1.input_cursor", "o1.halted", "o2")
INPUT_WIDTHS = (32,) * len(INPUT_PATHS)
OUTPUT_WIDTHS = (32,) * len(OUTPUT_PATHS)
TOKEN = re.compile(r"\s*(?:(\d+)|([A-Za-z][A-Za-z0-9_]*)|(:=|&&|\|\||!=|<=|>=|<<|>>|[()\[\]{}:.,?=<>+*\-^&|'!]))")
PREC = {"||": 2, "&&": 3, "=": 4, "!=": 4, "<": 4, "<=": 4,
        ">": 4, ">=": 4, "<<": 5, ">>": 5, "+": 6, "-": 6,
        "*": 7, "|": 8, "^": 9, "&": 10}


@dataclass(frozen=True)
class Expr:
    op: str
    width: int
    args: tuple[Expr, ...] = ()
    value: int | str = 0


class ProfileError(ValueError):
    pass


class Parser:
    def __init__(self, source: str, *, input_layout=None, output_layout=None, widths=(8, 32, 128), allow_functions=True):
        self.source = source
        clean = re.sub(r"#[^\n]*", "", source)
        self.tokens: list[str] = []
        self.clean = clean
        self.offsets = []
        self.ends = []
        self.spans = {}
        pos = 0
        while clean[pos:].strip():
            match = TOKEN.match(clean, pos)
            if not match:
                raise ProfileError(f"unsupported syntax at {clean[pos:pos + 50]!r}")
            self.tokens.append(next(x for x in match.groups() if x is not None))
            self.offsets.append(next(match.start(i) for i in range(1, 4) if match.group(i) is not None))
            self.ends.append(match.end())
            pos = match.end()
        self.pos = 0
        self.streams: dict[str, int] = {}
        self.types = {}
        self.functions = {}
        self.parameters = {}
        self.variables = {}
        # V1 retains its exact default ABI. Successor profiles supply immutable
        # independently retained layouts, never infer an ABI from source alone.
        self.input_layout = tuple(zip(INPUT_PATHS, INPUT_WIDTHS)) if input_layout is None else input_layout
        self.output_layout = tuple(zip(OUTPUT_PATHS, OUTPUT_WIDTHS)) if output_layout is None else output_layout
        self.widths = widths
        self.allow_functions = allow_functions

    def peek(self) -> str:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else "<EOF>"

    def take(self, expected: str | None = None) -> str:
        value = self.peek()
        if value == "<EOF>" or (expected is not None and value != expected):
            raise ProfileError(f"expected {expected}, got {value} at token {self.pos}")
        self.pos += 1
        return value

    def width(self) -> int:
        self.take("bv")
        self.take("[")
        value = self.take()
        if value not in tuple(map(str, self.widths)):
            raise ProfileError("unsupported bitvector width for the selected profile")
        self.take("]")
        return int(value)

    def type_body(self):
        if self.peek() == "bv":
            return self.width()
        if self.peek() != "{":
            name = self.take()
            if name not in self.types:
                raise ProfileError("unknown or recursive type")
            return self.types[name]
        self.take("{")
        fields = {}
        while True:
            name = self.take()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) or name in fields:
                raise ProfileError("invalid or duplicate member")
            self.take(":")
            fields[name] = self.type_body()
            if self.peek() != ",":
                break
            self.take(",")
        self.take("}")
        return fields

    @staticmethod
    def flatten(prefix, shape):
        if isinstance(shape, int):
            return [(prefix, shape)]
        return [leaf for name, child in shape.items() for leaf in Parser.flatten(prefix + "." + name, child)]

    def parse(self) -> Expr:
        while self.peek() == "type":
            self.take("type")
            name = self.take()
            if name in self.types or name in ("bv", "min", "max"):
                raise ProfileError("duplicate or reserved type")
            self.take("=")
            self.types[name] = self.type_body()
            self.take(".")
        while self.peek() not in ("i1", "<EOF>"):
            if not self.allow_functions:
                raise ProfileError("functions are not in the selected transition profile")
            name = self.take()
            if name in self.functions or name in ("min", "max"):
                raise ProfileError("duplicate or reserved function")
            self.take("(")
            params = [self.take()]
            while self.peek() == ",":
                self.take(",")
                params.append(self.take())
            if len(set(params)) != len(params) or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", p) for p in params):
                raise ProfileError("invalid function parameters")
            self.take(")")
            self.take(":")
            width = self.width()
            self.take(":=")
            self.parameters = {p: Expr("param", width, value=p) for p in params}
            body = self.expr()
            if body.width != width:
                raise ProfileError("function result width differs")
            self.parameters = {}
            self.take(".")
            self.functions[name] = (params, width, body)
        declarations = [("i1", "in"), ("i2", "in"), ("i3", "in"), ("o1", "out"), ("o2", "out")]
        seen = {"in": [], "out": []}
        for name, direction in declarations:
            self.take(name)
            self.take(":")
            shape = self.type_body()
            self.take(":=")
            self.take(direction)
            self.take("console")
            self.take(".")
            self.streams[name] = shape
            for path, width in self.flatten(name, shape):
                seen[direction].append((path, width))
                self.variables[path] = Expr("var", width, value=direction[0] + str(len(seen[direction])))
        if seen["in"] != list(self.input_layout) or seen["out"] != list(self.output_layout):
            raise ProfileError("ADT stream layout differs from the VM ABI")
        self.take("always")
        root = self.expr()
        self.take(".")
        if self.peek() != "<EOF>":
            raise ProfileError("trailing syntax")
        validate_tree(root, len(self.output_layout))
        return root

    def expr(self, minimum: int = 0) -> Expr:
        start = self.pos
        token = self.take()
        if token == "(":
            if self.peek() == "bv":
                width = self.width()
                self.take(")")
                child = self.expr(11)
                if not child.width:
                    raise ProfileError("cannot cast a formula")
                left = Expr("cast", width, (child,))
            else:
                left = self.expr()
                self.take(")")
        elif token == "{":
            digits = self.take()
            if not digits.isdecimal():
                raise ProfileError("expected unsigned decimal constant")
            self.take("}")
            self.take(":")
            width = self.width()
            value = int(digits)
            if value >= 1 << width:
                raise ProfileError("constant is outside its declared width")
            left = Expr("const", width, value=value)
        elif token == "!":
            child = self.expr(4)
            if child.width:
                raise ProfileError("! requires a formula")
            left = Expr("not", 0, (child,))
        elif token in self.parameters:
            left = self.parameters[token]
        elif token in self.functions or token in ("min", "max"):
            self.take("(")
            args = [self.expr()]
            while self.peek() == ",":
                self.take(",")
                args.append(self.expr())
            self.take(")")
            if token in ("min", "max"):
                if len(args) != 2 or args[0].width <= 0 or args[0].width != args[1].width:
                    raise ProfileError("min/max require two equal-width bitvectors")
                left = Expr(token, args[0].width, tuple(args))
            else:
                params, width, body = self.functions[token]
                if len(args) != len(params) or any(a.width != width for a in args):
                    raise ProfileError("function argument shape differs")
                bindings = dict(zip(params, args))
                def substitute(node):
                    return bindings[str(node.value)] if node.op == "param" else Expr(node.op, node.width, tuple(substitute(a) for a in node.args), node.value)
                left = substitute(body)
        elif token in self.streams:
            self.take("[")
            self.take("t")
            self.take("]")
            path, shape = token, self.streams[token]
            while self.peek() == "." and self.pos + 1 < len(self.tokens) and isinstance(shape, dict) and self.tokens[self.pos + 1] in shape:
                self.take(".")
                member = self.take()
                path += "." + member
                shape = shape[member]
            leaves = self.flatten(path, shape)
            left = self.variables[path] if isinstance(shape, int) else Expr("tuple", -1, tuple(self.variables[p] for p, _ in leaves), value=repr(shape))
        else:
            raise ProfileError(f"unsupported atom {token}")
        while True:
            self.spans[id(left)] = self.clean[self.offsets[start]:self.ends[self.pos - 1]]
            operator = self.peek()
            if operator == "'" and 11 >= minimum:
                self.take()
                if not left.width:
                    raise ProfileError("complement requires a bitvector")
                left = Expr("complement", left.width, (left,))
                continue
            if operator == "?" and minimum <= 1:
                self.take()
                yes = self.expr()
                self.take(":")
                no = self.expr(1)
                if left.width or yes.width or no.width:
                    raise ProfileError("Tau conditional operands must be formulas")
                left = Expr("if", 0, (left, yes, no))
                continue
            precedence = PREC.get(operator, -1)
            if precedence < minimum:
                break
            self.take()
            right = self.expr(precedence + 1)
            if left.width == -1 or right.width == -1:
                if operator != "=" or left.width != right.width or left.value != right.value:
                    raise ProfileError("only same-shape tuple equality is supported")
                equalities = [Expr("=", 0, (a, b)) for a, b in zip(left.args, right.args)]
                left = equalities[0]
                for equality in equalities[1:]:
                    left = Expr("&&", 0, (left, equality))
                continue
            if operator in ("&&", "||"):
                if left.width or right.width:
                    raise ProfileError("logical operator requires formulas")
                width = 0
            else:
                if not left.width or left.width != right.width:
                    raise ProfileError(f"width mismatch at {operator}")
                width = 0 if operator in ("=", "!=", "<", "<=", ">", ">=") else left.width
            left = Expr(operator, width, (left, right))
        self.spans[id(left)] = self.clean[self.offsets[start]:self.ends[self.pos - 1]]
        return left


def input_only(node: Expr) -> None:
    if node.op == "var" and str(node.value).startswith("o"):
        raise ProfileError("outputs may only appear on the left of leaf assignments")
    if node.op == "if":
        raise ProfileError("nested conditionals are only supported as decision nodes")
    for child in node.args:
        input_only(child)


def assignments(node: Expr, output_count: int = len(OUTPUT_WIDTHS)) -> dict[str, Expr]:
    found: dict[str, Expr] = {}

    def visit(part: Expr) -> None:
        if part.op == "&&":
            for child in part.args:
                visit(child)
        elif part.op == "=" and part.args[0].op == "var":
            name = str(part.args[0].value)
            if not name.startswith("o") or name in found:
                raise ProfileError("duplicate or non-output leaf assignment")
            input_only(part.args[1])
            found[name] = part.args[1]
        else:
            raise ProfileError("leaf must contain only output assignments")
    visit(node)
    if set(found) != {f"o{i+1}" for i in range(output_count)}:
        raise ProfileError("every leaf must assign every output exactly once")
    return found


def validate_tree(root: Expr, output_count: int = len(OUTPUT_WIDTHS)) -> None:
    if root.op == "if":
        input_only(root.args[0])
        validate_tree(root.args[1], output_count)
        validate_tree(root.args[2], output_count)
    else:
        assignments(root, output_count)


def evaluate(node: Expr, inputs: tuple[int, ...]) -> int | bool:
    if node.op == "const":
        return int(node.value)
    if node.op == "var":
        return inputs[int(str(node.value)[1:]) - 1]
    if node.op == "&&":
        return bool(evaluate(node.args[0], inputs) and evaluate(node.args[1], inputs))
    if node.op == "||":
        return bool(evaluate(node.args[0], inputs) or evaluate(node.args[1], inputs))
    values = [evaluate(child, inputs) for child in node.args]
    a = values[0]
    if node.op == "cast":
        return a & ((1 << node.width) - 1)
    if node.op == "complement":
        return (~a) & ((1 << node.width) - 1)
    if node.op == "not":
        return not a
    b = values[1]
    if node.op in ("<<", ">>"):
        value = 0 if b >= node.width else (a << b if node.op == "<<" else a >> b)
    else:
        operations = {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b,
                      "&": lambda: a & b, "|": lambda: a | b, "^": lambda: a ^ b,
                      "=": lambda: a == b, "!=": lambda: a != b,
                      "<": lambda: a < b, "<=": lambda: a <= b,
                      ">": lambda: a > b, ">=": lambda: a >= b,
                      "&&": lambda: bool(a and b), "||": lambda: bool(a or b),
                      "min": lambda: min(a, b), "max": lambda: max(a, b)}
        value = operations[node.op]()
    return value & ((1 << node.width) - 1) if node.width else bool(value)


def step(root: Expr, inputs: tuple[int, ...]) -> tuple[int, ...]:
    if len(inputs) != len(INPUT_WIDTHS) or any(type(v) is not int or not 0 <= v < 1 << w
                                               for v, w in zip(inputs, INPUT_WIDTHS)):
        raise ProfileError("invalid input vector")
    while root.op == "if":
        root = root.args[1 if evaluate(root.args[0], inputs) else 2]
    result = assignments(root)
    return tuple(int(evaluate(result[f"o{i+1}"], inputs)) for i in range(len(OUTPUT_WIDTHS)))


def rust_expr(node: Expr) -> str:
    if node.op == "const":
        return f"{node.value}u128"
    if node.op == "var":
        return f"input[{int(str(node.value)[1:]) - 1}]"
    args = [rust_expr(child) for child in node.args]
    mask = f"{(1 << node.width) - 1}u128" if node.width else ""
    if node.op == "cast":
        return f"({args[0]} & {mask})"
    if node.op == "complement":
        return f"(!{args[0]} & {mask})"
    if node.op == "not":
        return f"(!{args[0]})"
    a, b = args
    if node.op in ("min", "max"):
        return f"core::cmp::{node.op}({a}, {b})"
    if node.op in ("+", "-", "*"):
        method = {"+": "wrapping_add", "-": "wrapping_sub", "*": "wrapping_mul"}[node.op]
        return f"(({a}).{method}({b}) & {mask})"
    if node.op in ("<<", ">>"):
        method = "shift_left" if node.op == "<<" else "shift_right"
        return f"{method}({a}, {b}, {node.width})"
    return f"({a} {'==' if node.op == '=' else node.op} {b})"


def rust_tree(node: Expr, indent: str = "    ") -> str:
    if node.op == "if":
        guard, yes, no = node.args
        return (f"{indent}if {rust_expr(guard)} {{\n{rust_tree(yes, indent + '    ')}\n"
                f"{indent}}} else {{\n{rust_tree(no, indent + '    ')}\n{indent}}}")
    output = assignments(node)
    return indent + "[\n" + ",\n".join(indent + "    " + rust_expr(output[f"o{i+1}"])
                                        for i in range(len(OUTPUT_WIDTHS))) + "\n" + indent + "]"


def generate(source: str) -> str:
    root = Parser(source).parse()
    digest = hashlib.sha256(source.encode()).digest()
    return ("// Generated by tools/compile_tau.py from spec/vm.tau. Do not edit.\n"
            f"pub const SPEC_HASH: [u8; 32] = {list(digest)!r};\n"
            "fn mask(width: u32) -> u128 { u128::MAX >> (128 - width) }\n"
            "fn shift_left(a: u128, b: u128, width: u32) -> u128 {\n"
            "    if b >= u128::from(width) { 0 } else { (a << (b as u32)) & mask(width) }\n}\n"
            "fn shift_right(a: u128, b: u128, width: u32) -> u128 {\n"
            "    if b >= u128::from(width) { 0 } else { a >> (b as u32) }\n}\n"
            "#[allow(unused_parens)]\n"
            f"pub fn tau_step(input: &[u128; {len(INPUT_WIDTHS)}]) -> [u128; {len(OUTPUT_WIDTHS)}] {{\n"
            + rust_tree(root) + "\n}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "spec/vm.tau").read_text()
    output = ROOT / "core/src/generated.rs"
    generated = generate(source)
    if args.check:
        if not output.exists() or output.read_text() != generated:
            raise SystemExit("Tau source and generated checker differ; run compile_tau.py")
        print("Tau-generated checker is current")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(generated)
        print(f"Generated {output}")


if __name__ == "__main__":
    main()
