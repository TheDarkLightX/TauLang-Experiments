"""Bounded SymPy CNF/DNF portfolio over pure terms or opaque formula skeletons.

This adapter is not a Tau or atomless-BA oracle.  The caller must run and charge
its final native/BA gates.  The emitted-byte metric uses native_oracle.typed_render verbatim.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import importlib.metadata
import math
import multiprocessing
import sys
import time
from typing import Any

try:
    from .engine import Context, children, free_vars, sort_of
    from .native_oracle import typed_render
except ImportError:
    from engine import Context, children, free_vars, sort_of
    from native_oracle import typed_render

AST = tuple
FORMS = ("cnf", "dnf")
OPAQUE_OPS = frozenset(("eq0", "ne0", "exists"))
ARITIES = {"zero": 0, "one": 0, "T": 0, "F": 0, "var": 0,
           "not": 1, "notF": 1, "eq0": 1, "ne0": 1, "exists": 1,
           "and": 2, "or": 2, "xor": 2, "andF": 2, "orF": 2}


@dataclass(frozen=True)
class AstMetrics:
    emitted: str
    emitted_utf8_bytes: int
    file_bytes: int
    tree_nodes: int
    dag_nodes: int
    tree_depth: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateReceipt:
    form: str
    status: str
    output: AST | None = None
    metrics: AstMetrics | None = None
    wall_seconds: float = 0.0
    phase_seconds: dict[str, float] = field(default_factory=dict)
    propositional_check: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None


@dataclass(frozen=True)
class BaselineResult:
    output: AST
    selected: str
    mode: str
    status: str
    input_metrics: AstMetrics
    metrics: AstMetrics
    proposition_order: tuple[dict[str, Any], ...]
    candidates: tuple[CandidateReceipt, ...]
    wall_seconds: float
    preparation_seconds: float
    worker_phase_seconds: dict[str, float]
    limits: dict[str, Any]
    environment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe except that json.dumps naturally converts AST tuples to lists."""
        return asdict(self)


def _scan_ast(ast: AST, max_nodes: int | None = None,
              max_depth: int | None = None) -> tuple[int, int, int]:
    """Iterative shape check and independent occurrence/structural-DAG counts."""
    stack, count, depth, unique = [(ast, 1)], 0, 0, set()
    while stack:
        node, level = stack.pop()
        if not isinstance(node, tuple) or not node or not isinstance(node[0], str):
            raise ValueError("AST nodes must be nonempty immutable tuples with string tags")
        op = node[0]
        if op not in ARITIES:
            raise ValueError("unsupported AST tag: " + repr(op))
        payload = 1 if op in ("var", "exists") else 0
        if len(node) != 1 + payload + ARITIES[op]:
            raise ValueError("wrong AST arity: " + repr(op))
        if payload and (not isinstance(node[1], str) or not node[1]):
            raise ValueError("variable and binder names must be nonempty strings")
        count += 1
        depth = max(depth, level)
        if max_nodes is not None and count > max_nodes:
            raise ValueError("max_ast_nodes exceeded")
        if max_depth is not None and level > max_depth:
            raise ValueError("max_ast_depth exceeded")
        # Hash only after validating every child: a mutable descendant otherwise
        # raises an unhelpful TypeError. Structural identity includes binders.
        stack.extend((child, level + 1) for child in children(node))
    stack = [ast]
    while stack:
        node = stack.pop()
        unique.add(node)
        stack.extend(children(node))
    return count, len(unique), depth


def measure_ast(ast: AST, context: Context) -> AstMetrics:
    """Same serializer for every candidate; root/leaves each count as one node.

    dag_nodes is the number of distinct immutable subtree tuples, not a claim
    that variables can be shared across lexical scopes in emitted code.
    """
    nodes, dag, depth = _scan_ast(ast)
    emitted = typed_render(ast, context)
    return AstMetrics(emitted, len(emitted.encode("utf-8")),
                      len((emitted + ".\n").encode("utf-8")), nodes, dag, depth)


def _propositions(ast: AST, mode: str, context: Context) -> tuple[AST, ...]:
    found, stack = set(), [ast]
    while stack:
        node = stack.pop()
        if (mode == "pure_term" and node[0] == "var") or (
                mode == "formula_skeleton" and node[0] in OPAQUE_OPS):
            found.add(node)
        else:
            stack.extend(children(node))
    # No alpha-renaming or semantic merging. UTF-8 rendered bytes and then full
    # tuple representation make the public ordering explicit and deterministic.
    return tuple(sorted(found, key=lambda a: (typed_render(a, context).encode("utf-8"), repr(a))))


def _eval_propositional(ast: AST, mode: str, values: dict[AST, bool]) -> bool:
    """Independent evaluator: no SymPy calls and no descent into opaque atoms."""
    op = ast[0]
    if mode == "formula_skeleton" and op in OPAQUE_OPS:
        return values[ast]
    if mode == "pure_term" and op == "var":
        return values[ast]
    if op in ("zero", "one", "T", "F"):
        return op in ("one", "T")
    if op in ("not", "notF"):
        return not _eval_propositional(ast[1], mode, values)
    left = _eval_propositional(ast[1], mode, values)
    right = _eval_propositional(ast[2], mode, values)
    if op in ("and", "andF"):
        return left and right
    if op in ("or", "orF"):
        return left or right
    if mode == "pure_term" and op == "xor":
        return left != right
    raise ValueError("unsupported propositional operator: " + repr(op))


def check_propositional_roundtrip(left: AST, right: AST, mode: str,
                                  propositions: tuple[AST, ...]) -> dict[str, Any]:
    """Exhaust all abstract assignments; caller must bound proposition count.

    For formula_skeleton this is explicitly NOT an atomless-BA interpretation.
    Bit j in the integer assignment supplies propositions[j].
    """
    if mode not in ("pure_term", "formula_skeleton"):
        raise ValueError("unsupported baseline mode")
    if len(set(propositions)) != len(propositions):
        raise ValueError("duplicate propositions")
    for assignment in range(1 << len(propositions)):
        values = {p: bool((assignment >> j) & 1) for j, p in enumerate(propositions)}
        if _eval_propositional(left, mode, values) != _eval_propositional(right, mode, values):
            return {"status": "inequivalent", "complete": False,
                    "assignments_checked": assignment + 1,
                    "counterexample_assignment": assignment,
                    "semantics": mode + "_propositional_assignments"}
    return {"status": "equivalent", "complete": True,
            "assignments_checked": 1 << len(propositions),
            "counterexample_assignment": None,
            "semantics": mode + "_propositional_assignments"}


def _to_sympy(ast: AST, mode: str, symbols: dict[AST, Any], sp: Any) -> Any:
    if ast in symbols:
        return symbols[ast]
    op = ast[0]
    if op in ("zero", "F"):
        return sp.false
    if op in ("one", "T"):
        return sp.true
    args = [_to_sympy(child, mode, symbols, sp) for child in children(ast)]
    constructor = {"not": sp.Not, "notF": sp.Not, "and": sp.And,
                   "andF": sp.And, "or": sp.Or, "orF": sp.Or, "xor": sp.Xor}[op]
    # Constructor auto-simplification is intentionally included in this baseline
    # and charged to mapping_seconds; evaluate=False would not disable all of it.
    return constructor(*args)


def _from_sympy(expr: Any, mode: str, reverse: dict[Any, AST], sp: Any) -> AST:
    if expr in reverse:
        return reverse[expr]
    formula = mode == "formula_skeleton"
    if expr is sp.true:
        return ("T" if formula else "one",)
    if expr is sp.false:
        return ("F" if formula else "zero",)
    if expr.func is sp.Not:
        return ("notF" if formula else "not", _from_sympy(expr.args[0], mode, reverse, sp))
    ops = {sp.And: "andF" if formula else "and", sp.Or: "orF" if formula else "or"}
    if not formula:
        ops[sp.Xor] = "xor"
    if expr.func not in ops or len(expr.args) < 2:
        raise ValueError("unexpected SymPy output: " + repr(expr))
    # SymPy's deterministic argument order, left-associated binary AST. No
    # uncharged tree-shape search; every normal-form candidate uses this policy.
    args = [_from_sympy(arg, mode, reverse, sp) for arg in expr.args]
    result = args[0]
    for arg in args[1:]:
        result = (ops[expr.func], result, arg)
    return result


def _worker_portfolio(connection: Any, ast: AST, context: Context, mode: str,
                      propositions: tuple[AST, ...]) -> None:
    """One isolated process, shared CNF-then-DNF budget enforced by the parent."""
    try:
        initially_loaded = "sympy" in sys.modules
        tick = time.perf_counter()
        import sympy as sp
        import_seconds = time.perf_counter() - tick
        tick = time.perf_counter()
        symbols = {p: sp.Symbol("p%06d" % j) for j, p in enumerate(propositions)}
        reverse = {symbol: p for p, symbol in symbols.items()}
        expression = _to_sympy(ast, mode, symbols, sp)
        mapping_seconds = time.perf_counter() - tick
        connection.send(("environment", {
            "sympy_version": sp.__version__, "sympy_initially_loaded_in_worker": initially_loaded,
            "active_sympy_symbol_order": [str(p) for p in sorted(expression.free_symbols,
                                                                     key=sp.default_sort_key)],
            "import_seconds": import_seconds, "mapping_seconds": mapping_seconds,
        }))
        for form in FORMS:
            connection.send(("started", form))
            started = time.perf_counter()
            phases = {}
            try:
                tick = time.perf_counter()
                simplified = sp.simplify_logic(expression, form=form, deep=False,
                                               force=True, dontcare=None)
                phases["simplify_seconds"] = time.perf_counter() - tick
                tick = time.perf_counter()
                output = _from_sympy(simplified, mode, reverse, sp)
                if sort_of(output, context) != sort_of(ast, context):
                    raise ValueError("round-trip changed sort")
                if not free_vars(output) <= context.interface:
                    raise ValueError("round-trip changed interface")
                phases["reverse_mapping_seconds"] = time.perf_counter() - tick
                tick = time.perf_counter()
                check = check_propositional_roundtrip(ast, output, mode, propositions)
                phases["propositional_check_seconds"] = time.perf_counter() - tick
                tick = time.perf_counter()
                metrics = measure_ast(output, context)
                phases["emission_metrics_seconds"] = time.perf_counter() - tick
                status = "ok" if check["complete"] and check["status"] == "equivalent" else "invalid"
                receipt = CandidateReceipt(form, status, output, metrics,
                                           time.perf_counter() - started, phases, check)
            except Exception as exc:
                receipt = CandidateReceipt(form, "error", wall_seconds=time.perf_counter() - started,
                                           phase_seconds=phases,
                                           reason=type(exc).__name__ + ": " + str(exc))
            connection.send(("candidate", receipt))
        connection.send(("done", None))
    except Exception as exc:
        try:
            connection.send(("error", type(exc).__name__ + ": " + str(exc)))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


def run_sympy_baseline(ast: AST, context: Context, *, max_propositions: int = 8,
                       timeout_seconds: float = 5.0, max_ast_nodes: int = 10_000,
                       max_ast_depth: int = 100) -> BaselineResult:
    """Select best(original, CNF, DNF) by bytes, tree nodes, repr, then source priority.

    A single shared deadline starts at function entry. Parent-side validation and
    accounting are bounded but not asynchronously interrupted; worker timeout
    kills and reaps the process. Final accounting/cleanup can exceed the cap and
    remains in wall_seconds. Invalid input raises ValueError instead of producing
    an apparently valid fallback. This implementation targets POSIX/fork.
    """
    started = time.perf_counter()
    for name, value in (("max_propositions", max_propositions), ("max_ast_nodes", max_ast_nodes),
                        ("max_ast_depth", max_ast_depth)):
        if type(value) is not int or value < (0 if name == "max_propositions" else 1):
            raise ValueError(name + " has an invalid integer limit")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not (
            math.isfinite(timeout_seconds) and timeout_seconds > 0):
        raise ValueError("timeout_seconds must be finite and positive")
    if max_ast_depth > 200:
        raise ValueError("max_ast_depth must not exceed 200")
    _scan_ast(ast, max_ast_nodes, max_ast_depth)
    sort = sort_of(ast, context)
    if context.temporal != "none" or context.T != "nontrivialABA" or context.K != ("0", "1"):
        raise ValueError("baseline requires the declared non-temporal pure 0/1 BA context")
    if not free_vars(ast) <= context.interface:
        raise ValueError("input exceeds the fixed free-variable interface")
    mode = "formula_skeleton" if sort == "formula" else "pure_term"
    metrics = measure_ast(ast, context)
    propositions = _propositions(ast, mode, context)
    order = tuple({"symbol": "p%06d" % j, "ast": p, "emitted": typed_render(p, context)}
                  for j, p in enumerate(propositions))
    candidates = [CandidateReceipt("original", "retained", ast, metrics,
                                  propositional_check={"status": "identity", "complete": True})]
    limits = {"max_propositions": max_propositions, "timeout_seconds": timeout_seconds,
              "max_ast_nodes": max_ast_nodes, "max_ast_depth": max_ast_depth,
              "deadline_scope": "shared_entire_portfolio", "form_order": list(FORMS)}
    environment = {"python_version": sys.version, "sympy_version": None,
                   "start_method": "fork", "constructor_auto_simplification": True,
                   "context": asdict(context), "context_key": context.key,
                   "deep": False, "force": True, "dontcare": None,
                   "serializer": "native_oracle.typed_render",
                   "file_wrapper": "expression + dot + LF",
                   "tie_break": "emitted_utf8_bytes_tree_nodes_repr_then_original_cnf_dnf_priority",
                   "input_proposition_count": len(propositions),
                   "scope": "adapter_propositional_only; final_native_and_BA_gate_required"}
    try:
        environment["sympy_version"] = importlib.metadata.version("sympy")
    except importlib.metadata.PackageNotFoundError:
        pass
    preparation_seconds = time.perf_counter() - started
    worker_phases = {}
    status = "ok"
    if len(propositions) > max_propositions:
        status = "capped"
        candidates.extend(CandidateReceipt(form, "capped", reason="max_propositions exceeded")
                          for form in FORMS)
    elif preparation_seconds >= timeout_seconds:
        status = "timeout"
        candidates.extend(CandidateReceipt(form, "deadline_exhausted",
                                           reason="shared deadline exhausted during preparation")
                          for form in FORMS)
    elif "fork" not in multiprocessing.get_all_start_methods():
        status = "error"
        candidates.extend(CandidateReceipt(form, "error", reason="POSIX fork is unavailable")
                          for form in FORMS)
    else:
        ctx = multiprocessing.get_context("fork")
        receiver, sender = ctx.Pipe(duplex=False)
        process = ctx.Process(target=_worker_portfolio,
                              args=(sender, ast, context, mode, propositions))
        process.daemon = True
        active_form, active_started, done, worker_error, timed_out = None, None, False, None, False
        process_start = time.perf_counter()
        try:
            process.start()
            sender.close()
            while not done:
                remaining = timeout_seconds - (time.perf_counter() - started)
                if remaining <= 0:
                    timed_out = True
                    break
                if not receiver.poll(remaining):
                    timed_out = True
                    break
                try:
                    event, payload = receiver.recv()
                except EOFError:
                    break
                if event == "environment":
                    environment.update({k: v for k, v in payload.items() if not k.endswith("seconds")})
                    worker_phases.update({k: v for k, v in payload.items() if k.endswith("seconds")})
                elif event == "started":
                    active_form, active_started = payload, time.perf_counter()
                elif event == "candidate":
                    candidates.append(payload)
                    active_form, active_started = None, None
                elif event == "done":
                    done = True
                elif event == "error":
                    worker_error = payload
                    break
        except Exception as exc:
            worker_error = type(exc).__name__ + ": " + str(exc)
        finally:
            tick = time.perf_counter()
            if process.pid is not None:
                # No abandoned work may contaminate later timings. Even after
                # done, reap within the remaining budget then terminate if needed.
                process.join(max(0.0, timeout_seconds - (tick - started)))
                if process.is_alive():
                    process.terminate()
                    process.join(1.0)
                if process.is_alive():
                    process.kill()
                    process.join()
                environment["worker_exitcode"] = process.exitcode
            receiver.close()
            sender.close()
            worker_phases["cleanup_seconds"] = time.perf_counter() - tick
            worker_phases["process_inclusive_seconds"] = time.perf_counter() - process_start
        completed = {receipt.form for receipt in candidates}
        for form in FORMS:
            if form not in completed:
                form_status = "timeout" if timed_out and form == active_form else (
                    "deadline_exhausted" if timed_out else "error")
                elapsed = time.perf_counter() - active_started if form == active_form and active_started else 0.0
                candidates.append(CandidateReceipt(form, form_status, wall_seconds=elapsed,
                                                   reason=worker_error or ("shared deadline exhausted" if timed_out
                                                                          else "worker exited without receipt")))
        successful = sum(r.status == "ok" for r in candidates if r.form in FORMS)
        status = "ok" if successful == 2 else ("partial" if successful else ("timeout" if timed_out else "error"))
    eligible = [r for r in candidates if r.status in ("retained", "ok")]
    priority = {"original": 0, "cnf": 1, "dnf": 2}
    selected = min(eligible, key=lambda r: (r.metrics.emitted_utf8_bytes, r.metrics.tree_nodes,
                                               repr(r.output), priority[r.form]))
    return BaselineResult(selected.output, selected.form, mode, status, metrics, selected.metrics,
                          order, tuple(candidates), time.perf_counter() - started,
                          preparation_seconds, worker_phases, limits, environment)
