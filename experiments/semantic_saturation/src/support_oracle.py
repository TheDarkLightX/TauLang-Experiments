"""Independent finite-support oracle for a restricted atomless-BA formula AST.

This module does not call Tau and does not replace a native Tau equivalence gate.
It interprets only the explicit AST below, over nontrivial atomless Boolean
algebras. It rejects unknown tags, malformed ASTs, unsupported interfaces, and
resource exhaustion. There is no Lean proof or claim about arbitrary Tau syntax,
temporal recurrence, sentence-valued constants, or bitvector interpretations.

Terms: ('var', name), ('zero',), ('one',), ('not', a), ('and', a, b),
       ('or', a, b), ('xor', a, b).
Formulas: ('eq0', term), ('ne0', term), ('T',), ('F',), ('notF', f),
          ('andF', f, g), ('orF', f, g), ('exists', name, f).

For n parameters, joint Boolean cells have indices 0 .. 2**n-1. Bit i of a
nonzero support mask records that cell i is nonempty. A term denotes a subset
of these active cells. An existential binder appends a fresh membership slot:
every active cell becomes low-only, high-only, or both. Atomlessness permits a
nonempty cell to split into two nonempty cells; these choices can be made
independently across the finite partition. Structural induction therefore gives
an exact support-pattern interpretation for the admitted signature. This is a
mathematical argument accompanying bounded executable checks, not a machine
checked proof. In particular, it is not a two-valued assignment to BA variables.

The public results are immutable. Only EQUIVALENT with complete=True counts as
acceptance. UNKNOWN and REJECTED always have equivalent=False, even if partial
observations happen to agree. Variable order is part of every returned result.
External callers must additionally fix their Tau types, widths, and context.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import product
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Sequence, Tuple

AST = Tuple[Any, ...]


class ScopeRejected(ValueError):
    """The input or requested scope is outside the admitted fragment."""


class BudgetExceeded(RuntimeError):
    """A deterministic work cap prevented a complete result."""


@dataclass(frozen=True)
class Limits:
    max_free_variables: int = 3
    max_quantifier_depth: int = 4
    max_variable_slots: int = 8
    max_initial_supports: int = 255
    max_states: int = 250_000
    max_node_evaluations: int = 2_000_000
    max_ast_nodes: int = 10_000
    max_ast_depth: int = 100

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if type(value) is not int or value < 0:
                raise ScopeRejected("limit %s must be a nonnegative integer" % name)
        # Bound bitset allocation independently of the number of enumerated states.
        if self.max_variable_slots > 16 or self.max_free_variables > 16:
            raise ScopeRejected("at most 16 variable slots are supported")
        if self.max_ast_depth > 200:
            raise ScopeRejected("at most 200 AST levels are supported")


@dataclass(frozen=True)
class Stats:
    support_patterns_total: int = 0
    support_patterns_evaluated: int = 0
    states_evaluated: int = 0
    existential_refinements: int = 0
    term_evaluations: int = 0
    formula_evaluations: int = 0


@dataclass(frozen=True)
class FormulaValue:
    support_mask: int
    value: bool


@dataclass(frozen=True)
class FormulaObservation:
    support_mask: int
    left: bool
    right: bool


@dataclass(frozen=True)
class FormulaEvaluation:
    status: str
    free_variables: Tuple[str, ...]
    observations: Tuple[FormulaValue, ...]
    stats: Stats
    complete: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class FormulaComparison:
    status: str
    free_variables: Tuple[str, ...]
    observations: Tuple[FormulaObservation, ...]
    stats: Stats
    complete: bool
    counterexample: Optional[FormulaObservation] = None
    reason: Optional[str] = None

    @property
    def equivalent(self) -> bool:
        return self.status == "EQUIVALENT" and self.complete


@dataclass(frozen=True)
class TermObservation:
    assignment: int
    left: bool
    right: bool


@dataclass(frozen=True)
class TermComparison:
    status: str
    free_variables: Tuple[str, ...]
    observations: Tuple[TermObservation, ...]
    complete: bool
    counterexample: Optional[TermObservation] = None
    reason: Optional[str] = None

    @property
    def equivalent(self) -> bool:
        return self.status == "EQUIVALENT" and self.complete

    @property
    def left_signature(self) -> Tuple[bool, ...]:
        return tuple(item.left for item in self.observations)

    @property
    def right_signature(self) -> Tuple[bool, ...]:
        return tuple(item.right for item in self.observations)


class _Validator:
    def __init__(self, limits: Limits):
        self.limits = limits
        self.nodes = 0

    def _node(self, node: AST, depth: int) -> str:
        if type(node) is not tuple or not node or type(node[0]) is not str:
            raise ScopeRejected("AST nodes must be nonempty tuples with a string tag")
        self.nodes += 1
        if self.nodes > self.limits.max_ast_nodes:
            raise ScopeRejected("AST node cap exceeded")
        if depth > self.limits.max_ast_depth:
            raise ScopeRejected("AST depth cap exceeded")
        return node[0]

    @staticmethod
    def _arity(node: AST, arity: int) -> None:
        if len(node) != arity:
            raise ScopeRejected("wrong arity for %r" % (node[0],))

    @staticmethod
    def _name(name: Any) -> str:
        if type(name) is not str or not name:
            raise ScopeRejected("variable names must be nonempty strings")
        return name

    def term(self, node: AST, bound: Tuple[str, ...] = (), depth: int = 0) -> set:
        tag = self._node(node, depth)
        if tag == "var":
            self._arity(node, 2)
            name = self._name(node[1])
            return set() if name in bound else {name}
        if tag in ("zero", "one"):
            self._arity(node, 1)
            return set()
        if tag == "not":
            self._arity(node, 2)
            return self.term(node[1], bound, depth + 1)
        if tag in ("and", "or", "xor"):
            self._arity(node, 3)
            return self.term(node[1], bound, depth + 1) | self.term(node[2], bound, depth + 1)
        raise ScopeRejected("unknown BA-term tag %r" % (tag,))

    def formula(self, node: AST, bound: Tuple[str, ...] = (), depth: int = 0,
                quantifier_depth: int = 0) -> set:
        tag = self._node(node, depth)
        if tag in ("T", "F"):
            self._arity(node, 1)
            return set()
        if tag in ("eq0", "ne0"):
            self._arity(node, 2)
            return self.term(node[1], bound, depth + 1)
        if tag == "notF":
            self._arity(node, 2)
            return self.formula(node[1], bound, depth + 1, quantifier_depth)
        if tag in ("andF", "orF"):
            self._arity(node, 3)
            return (self.formula(node[1], bound, depth + 1, quantifier_depth)
                    | self.formula(node[2], bound, depth + 1, quantifier_depth))
        if tag == "exists":
            self._arity(node, 3)
            name = self._name(node[1])
            if quantifier_depth + 1 > self.limits.max_quantifier_depth:
                raise ScopeRejected("quantifier-depth cap exceeded")
            return self.formula(node[2], bound + (name,), depth + 1, quantifier_depth + 1)
        raise ScopeRejected("unknown formula tag %r" % (tag,))


def _interface(required: set, free_variables: Optional[Sequence[str]], limits: Limits) -> Tuple[str, ...]:
    if free_variables is None:
        names = tuple(sorted(required))
    else:
        if not isinstance(free_variables, Sequence) or isinstance(free_variables, (str, bytes)):
            raise ScopeRejected("free_variables must be a sequence of distinct names")
        names = tuple(free_variables)
        for name in names:
            _Validator._name(name)
        if len(set(names)) != len(names):
            raise ScopeRejected("duplicate free-variable names")
        if not required.issubset(names):
            raise ScopeRejected("interface omits free variables: %s" % sorted(required - set(names)))
    if len(names) > limits.max_free_variables:
        raise ScopeRejected("free-variable cap exceeded")
    if len(names) > limits.max_variable_slots:
        raise ScopeRejected("variable-slot cap exceeded")
    return names


def active_patterns(support_mask: int) -> Tuple[int, ...]:
    """Return active cell indices, in deterministic ascending order."""
    if type(support_mask) is not int or support_mask <= 0:
        raise ScopeRejected("support must be a positive integer (nontrivial algebra)")
    result = []
    remaining = support_mask
    while remaining:
        bit = remaining & -remaining
        result.append(bit.bit_length() - 1)
        remaining ^= bit
    return tuple(result)


def support_count(variable_count: int) -> int:
    if type(variable_count) is not int or not 0 <= variable_count <= 16:
        raise ScopeRejected("variable_count must lie between 0 and 16")
    return (1 << (1 << variable_count)) - 1


def refinement_supports(support_mask: int, variable_count: int) -> Iterator[int]:
    """Enumerate all exact one-binder extensions, low/high/both per active cell.

    The new slot is the most significant membership bit. This helper itself has
    no work budget; callers must bound its iteration. The public evaluator does.
    """
    support_count(variable_count)
    if variable_count >= 16:
        raise ScopeRejected("refinement would exceed 16 variable slots")
    patterns = active_patterns(support_mask)
    if patterns[-1] >= (1 << variable_count):
        raise ScopeRejected("support contains a cell outside the variable interface")
    offset = 1 << variable_count
    for choices in product((1, 2, 3), repeat=len(patterns)):
        refined = 0
        for pattern, choice in zip(patterns, choices):
            if choice & 1:
                refined |= 1 << pattern
            if choice & 2:
                refined |= 1 << (pattern + offset)
        yield refined


def describe_support(free_variables: Sequence[str], support_mask: int) -> Tuple[Tuple[int, ...], ...]:
    """Decode a counterexample into active cells, in the supplied variable order."""
    patterns = active_patterns(support_mask)
    if patterns[-1] >= 1 << len(free_variables):
        raise ScopeRejected("support contains a cell outside the variable interface")
    return tuple(tuple((pattern >> i) & 1 for i in range(len(free_variables)))
                 for pattern in patterns)


@dataclass(frozen=True)
class _State:
    names: Tuple[str, ...]
    support: int


class _Evaluator:
    def __init__(self, limits: Limits, total: int):
        self.limits = limits
        self.total = total
        self.supports_evaluated = 0
        self.states = 0
        self.refinements = 0
        self.term_nodes = 0
        self.formula_nodes = 0

    def stats(self) -> Stats:
        return Stats(self.total, self.supports_evaluated, self.states, self.refinements,
                     self.term_nodes, self.formula_nodes)

    def state(self, refinement: bool = False) -> None:
        if self.states >= self.limits.max_states:
            raise BudgetExceeded("state cap exceeded")
        self.states += 1
        if refinement:
            self.refinements += 1

    def node(self, term: bool) -> None:
        if self.term_nodes + self.formula_nodes >= self.limits.max_node_evaluations:
            raise BudgetExceeded("node-evaluation cap exceeded")
        if term:
            self.term_nodes += 1
        else:
            self.formula_nodes += 1

    def term(self, ast: AST, state: _State, cache: Dict[AST, int]) -> int:
        if ast in cache:
            return cache[ast]
        self.node(term=True)
        tag = ast[0]
        if tag == "zero":
            result = 0
        elif tag == "one":
            result = state.support
        elif tag == "var":
            # A binder always appends a fresh slot. Search backwards for lexical shadowing.
            slot = len(state.names) - 1 - state.names[::-1].index(ast[1])
            result = sum(1 << p for p in active_patterns(state.support) if (p >> slot) & 1)
        elif tag == "not":
            result = state.support ^ self.term(ast[1], state, cache)
        else:
            left = self.term(ast[1], state, cache)
            right = self.term(ast[2], state, cache)
            result = {"and": int.__and__, "or": int.__or__, "xor": int.__xor__}[tag](left, right)
        cache[ast] = result
        return result

    def formula(self, ast: AST, state: _State, terms: Dict[AST, int],
                formulas: Dict[AST, bool]) -> bool:
        if ast in formulas:
            return formulas[ast]
        self.node(term=False)
        tag = ast[0]
        if tag == "T":
            result = True
        elif tag == "F":
            result = False
        elif tag in ("eq0", "ne0"):
            empty = self.term(ast[1], state, terms) == 0
            result = empty if tag == "eq0" else not empty
        elif tag == "notF":
            result = not self.formula(ast[1], state, terms, formulas)
        elif tag == "andF":
            result = (self.formula(ast[1], state, terms, formulas)
                      and self.formula(ast[2], state, terms, formulas))
        elif tag == "orF":
            result = (self.formula(ast[1], state, terms, formulas)
                      or self.formula(ast[2], state, terms, formulas))
        else:  # 'exists', guaranteed by validation
            if len(state.names) >= self.limits.max_variable_slots:
                raise ScopeRejected("variable-slot cap exceeded during quantification")
            result = False
            for support in refinement_supports(state.support, len(state.names)):
                self.state(refinement=True)
                child = _State(state.names + (ast[1],), support)
                # Caches belong to a single partition/environment, never to a raw AST alone.
                if self.formula(ast[2], child, {}, {}):
                    result = True
                    break
        formulas[ast] = result
        return result


def _prepare_formulas(asts: Iterable[AST], free_variables: Optional[Sequence[str]],
                      limits: Limits) -> Tuple[Tuple[str, ...], int]:
    limits.validate()
    validator = _Validator(limits)
    required = set()
    for ast in asts:
        required |= validator.formula(ast)
    names = _interface(required, free_variables, limits)
    total = support_count(len(names))
    if total > limits.max_initial_supports:
        raise ScopeRejected("initial-support cap exceeded (%d required)" % total)
    return names, total


def evaluate_formula(formula: AST, *, free_variables: Optional[Sequence[str]] = None,
                     limits: Limits = Limits()) -> FormulaEvaluation:
    """Evaluate all nonempty free-parameter occupancies or return a fail-closed result."""
    names = ()
    observations = []
    evaluator = _Evaluator(limits, 0)
    try:
        names, total = _prepare_formulas((formula,), free_variables, limits)
        evaluator.total = total
        for support in range(1, total + 1):
            evaluator.state()
            value = evaluator.formula(formula, _State(names, support), {}, {})
            observations.append(FormulaValue(support, value))
            evaluator.supports_evaluated += 1
        return FormulaEvaluation("COMPLETE", names, tuple(observations), evaluator.stats(), True)
    except (ScopeRejected, BudgetExceeded, RecursionError) as exc:
        status = "REJECTED" if isinstance(exc, ScopeRejected) else "UNKNOWN"
        return FormulaEvaluation(status, names, tuple(observations), evaluator.stats(), False, str(exc))


def compare_formulas(left: AST, right: AST, *, free_variables: Optional[Sequence[str]] = None,
                     limits: Limits = Limits()) -> FormulaComparison:
    """Compare formulas under one fixed interface, preserving all complete observations."""
    names = ()
    observations = []
    counterexample = None
    evaluator = _Evaluator(limits, 0)
    try:
        names, total = _prepare_formulas((left, right), free_variables, limits)
        evaluator.total = total
        for support in range(1, total + 1):
            evaluator.state()
            state = _State(names, support)
            terms, formulas = {}, {}
            lv = evaluator.formula(left, state, terms, formulas)
            rv = evaluator.formula(right, state, terms, formulas)
            observation = FormulaObservation(support, lv, rv)
            observations.append(observation)
            evaluator.supports_evaluated += 1
            if lv != rv and counterexample is None:
                counterexample = observation
        status = "EQUIVALENT" if counterexample is None else "DIFFERENT"
        return FormulaComparison(status, names, tuple(observations), evaluator.stats(), True, counterexample)
    except (ScopeRejected, BudgetExceeded, RecursionError) as exc:
        status = "REJECTED" if isinstance(exc, ScopeRejected) else "UNKNOWN"
        return FormulaComparison(status, names, tuple(observations), evaluator.stats(), False,
                                 counterexample, str(exc))


def _pointwise_term(ast: AST, assignment: Dict[str, bool]) -> bool:
    """Separate scalar Boolean evaluator: shares neither cell logic nor caches."""
    tag = ast[0]
    if tag == "var":
        return assignment[ast[1]]
    if tag == "zero":
        return False
    if tag == "one":
        return True
    if tag == "not":
        return not _pointwise_term(ast[1], assignment)
    left = _pointwise_term(ast[1], assignment)
    right = _pointwise_term(ast[2], assignment)
    if tag == "and":
        return left and right
    if tag == "or":
        return left or right
    return left != right


def compare_terms(left: AST, right: AST, *, free_variables: Optional[Sequence[str]] = None,
                  limits: Limits = Limits()) -> TermComparison:
    """Independent full Boolean signatures, admitted only for pure 0/1 BA terms."""
    names = ()
    observations = []
    counterexample = None
    try:
        limits.validate()
        validator = _Validator(limits)
        names = _interface(validator.term(left) | validator.term(right), free_variables, limits)
        total = 1 << len(names)
        if total > limits.max_states:
            raise BudgetExceeded("state cap exceeded")
        # The uncached scalar evaluator visits each AST node once per assignment.
        if total * validator.nodes > limits.max_node_evaluations:
            raise BudgetExceeded("node-evaluation cap exceeded")
        for bits in range(total):
            assignment = {name: bool((bits >> slot) & 1) for slot, name in enumerate(names)}
            lv, rv = _pointwise_term(left, assignment), _pointwise_term(right, assignment)
            observation = TermObservation(bits, lv, rv)
            observations.append(observation)
            if lv != rv and counterexample is None:
                counterexample = observation
        return TermComparison("EQUIVALENT" if counterexample is None else "DIFFERENT",
                              names, tuple(observations), True, counterexample)
    except (ScopeRejected, BudgetExceeded, RecursionError) as exc:
        status = "REJECTED" if isinstance(exc, ScopeRejected) else "UNKNOWN"
        return TermComparison(status, names, tuple(observations), False, counterexample, str(exc))


def pilot_evidence() -> Dict[str, Any]:
    """Deterministic standalone evidence; no native Tau verdicts are asserted."""
    a, b, x = ("var", "a"), ("var", "b"), ("var", "x")
    proper_split = ("andF", ("eq0", ("and", b, ("not", a))),
                    ("andF", ("ne0", b), ("ne0", ("and", a, ("not", b)))))
    fixtures = {
        "atomless_proper_split": compare_formulas(("exists", "b", proper_split), ("ne0", a)),
        "two_valued_formula_negative": compare_formulas(
            ("orF", ("eq0", x), ("eq0", ("not", x))), ("T",)),
        "one_way_implication_negative": compare_formulas(("eq0", x), ("T",)),
        "term_absorption": compare_terms(("or", a, ("and", a, b)), a),
        "forced_unknown": compare_formulas(("T",), ("T",), limits=Limits(max_states=0)),
    }
    return {
        "oracle": "independent abstract-support enumerator",
        "scope": "explicit non-temporal AST in nontrivial atomless Boolean algebras",
        "proof_status": "bounded executable evidence and mathematical argument; no Lean proof",
        "native_tau_checked": False,
        "default_limits": asdict(Limits()),
        "support_counts": {str(n): support_count(n) for n in range(4)},
        "fixtures": {name: asdict(result) for name, result in fixtures.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true", help="emit deterministic pilot evidence")
    parser.add_argument("--output", type=Path, help="write evidence JSON to this file")
    args = parser.parse_args()
    if not args.self_check:
        parser.error("use --self-check to run the built-in fixtures")
    payload = json.dumps(pilot_evidence(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
