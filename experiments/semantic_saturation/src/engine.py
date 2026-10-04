"""Deterministic bounded e-graph; accepted semantic pairs are caller-checked.

This module implements Boolean algebra laws, not a Tau validity checker. Formula
equivalence (particularly quantifiers) must be checked by the external oracle.
Every e-node carries its sort and lexical binding scope. ASTs are immutable
tuples; the graph is private mutable machinery with a pure optimize interface.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Context:
    terms: tuple = ()
    T: str = "nontrivialABA"
    V: tuple | None = None
    K: tuple = ("0", "1")
    temporal: str = "none"

    def __post_init__(self):
        if not isinstance(self.terms, tuple) or any(not isinstance(p, tuple) or len(p) != 2 or
                not all(isinstance(x, str) for x in p) for p in self.terms):
            raise ValueError("context terms must be immutable (name, sort) pairs")
        if len({n for n, _ in self.terms}) != len(self.terms):
            raise ValueError("duplicate declared variable")
        if len({s for _, s in self.terms}) > 1:
            raise ValueError("this AST admits one BA descriptor per context; split mixed sorts")
        if self.V is not None and (not isinstance(self.V, tuple) or not set(self.V) <= {n for n, _ in self.terms}):
            raise ValueError("fixed interface must be a tuple of declared variables")
        if not isinstance(self.K, tuple): raise ValueError("constant context must be immutable")

    @property
    def key(self):
        return sha256(repr((self.terms, self.T, self.V, self.K, self.temporal)).encode()).hexdigest()

    @property
    def term_sort(self):
        return self.terms[0][1] if self.terms else "tau"

    @property
    def interface(self):
        return frozenset(n for n, _ in self.terms) if self.V is None else frozenset(self.V)


@dataclass(frozen=True)
class CheckedPair:
    left: tuple
    right: tuple
    scope_key: str


@dataclass(frozen=True)
class Report:
    iterations: int
    nodes: int
    classes: int
    rewrite_unions: int
    semantic_unions: int
    tree_cost: int
    source_bytes: int
    stop_reason: str
    rejected_pairs: tuple = ()


TERM_BINARY = ("and", "or", "xor")
FORM_BINARY = ("andF", "orF")
LEAVES = ("zero", "one", "T", "F")


def children(ast):
    op = ast[0]
    return ast[2:] if op == "exists" else (() if op in LEAVES or op == "var" else ast[1:])


def free_vars(ast, bound=frozenset()):
    if ast[0] == "var":
        return frozenset() if ast[1] in bound else frozenset((ast[1],))
    if ast[0] == "exists":
        return free_vars(ast[2], bound | {ast[1]})
    return frozenset().union(*(free_vars(c, bound) for c in children(ast)))


def sort_of(ast, context, bound=()):
    if not isinstance(ast, tuple) or not ast:
        raise ValueError("AST must be a nonempty immutable tuple")
    op, env = ast[0], dict(context.terms)
    env.update(bound)
    if op == "var" and len(ast) == 2 and ast[1] in env:
        return "term:" + env[ast[1]]
    if op in ("zero", "one") and len(ast) == 1:
        return "term:" + context.term_sort
    if op in ("T", "F") and len(ast) == 1:
        return "formula"
    if op == "exists" and len(ast) == 3 and isinstance(ast[1], str):
        if sort_of(ast[2], context, bound + ((ast[1], env.get(ast[1], context.term_sort)),)) != "formula":
            raise ValueError("exists body must be a formula")
        return "formula"
    arity = 2 if op in TERM_BINARY + FORM_BINARY else 1
    if op not in TERM_BINARY + FORM_BINARY + ("not", "notF", "eq0", "ne0") or len(ast) != arity + 1:
        raise ValueError("unknown tag or wrong arity: " + repr(ast))
    sorts = tuple(sort_of(c, context, bound) for c in children(ast))
    if op in FORM_BINARY + ("notF",):
        if any(s != "formula" for s in sorts):
            raise ValueError("formula operator received a term")
        return "formula"
    if any(not s.startswith("term:") for s in sorts) or len(set(sorts)) != 1:
        raise ValueError("term operator received incompatible sorts")
    return "formula" if op in ("eq0", "ne0") else sorts[0]


def tree_cost(ast):
    return 1 + sum(tree_cost(c) for c in children(ast))


def render(ast, context=None, exists_keyword="ex"):
    op = ast[0]
    if op == "var":
        return ast[1]
    if op in LEAVES:
        return {"zero": "0", "one": "1", "T": "T", "F": "F"}[op]
    if op == "exists":
        descriptor = dict(context.terms).get(ast[1], context.term_sort) if context else "tau"
        return f"{exists_keyword} {ast[1]} : {descriptor} ({render(ast[2], context, exists_keyword)})"
    args = [render(c, context, exists_keyword) for c in children(ast)]
    if op == "not":
        return f"({args[0]})'"
    if op == "notF":
        return f"!({args[0]})"
    if op in ("eq0", "ne0"):
        return f"({args[0]} {'=' if op == 'eq0' else '!='} 0)"
    symbol = {"and": "&", "or": "|", "xor": "^", "andF": "&&", "orF": "||"}[op]
    return f"({args[0]} {symbol} {args[1]})"


def source_cost(ast, context=None):
    return len(render(ast, context).encode("utf-8"))


def pure_term_signature(ast, variables):
    """Complete 0/1-corner signature for pure terms; never a formula oracle."""
    if ast[0] not in ("var", "zero", "one", "not") + TERM_BINARY:
        raise ValueError("signature only admits pure 0/1 Boolean algebra terms")
    if not free_vars(ast) <= set(variables) or len(set(variables)) != len(variables):
        raise ValueError("signature variables must be unique and include all free variables")
    def evaluate(a, values):
        op = a[0]
        if op == "var": return values[a[1]]
        if op in ("zero", "one"): return int(op == "one")
        if op == "not": return 1 - evaluate(a[1], values)
        if op not in TERM_BINARY: raise ValueError("signature contains a formula")
        x, y = evaluate(a[1], values), evaluate(a[2], values)
        return {"and": x & y, "or": x | y, "xor": x ^ y}[op]
    return tuple(evaluate(ast, dict(zip(variables, ((i >> j) & 1 for j in range(len(variables))))))
                 for i in range(1 << len(variables)))


@dataclass(frozen=True)
class Node:
    op: str
    payload: tuple
    args: tuple
    sort: str
    scope: tuple


class NodeLimit(RuntimeError):
    pass


class EGraph:
    def __init__(self, context, node_limit=1000):
        if node_limit < 1: raise ValueError("node_limit must be positive")
        self.context, self.node_limit = context, node_limit
        self.parent, self.meta, self.nodes, self.memo = [], [], [], {}
        self.rewrite_unions = self.semantic_unions = 0

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b, semantic=False):
        a, b = self.find(a), self.find(b)
        if self.meta[a] != self.meta[b]:
            raise ValueError("union changes sort or lexical binding scope")
        if a == b: return False
        a, b = sorted((a, b))
        self.parent[b] = a
        if semantic: self.semantic_unions += 1
        else: self.rewrite_unions += 1
        return True

    def canonical(self, node):
        args = tuple(self.find(c) for c in node.args)
        if node.op in TERM_BINARY + FORM_BINARY: args = tuple(sorted(args))
        return Node(node.op, node.payload, args, node.sort, node.scope)

    def intern(self, node):
        node = self.canonical(node)
        if node in self.memo: return self.find(self.memo[node])
        if len(self.nodes) >= self.node_limit: raise NodeLimit("node_limit")
        eid = len(self.parent)
        self.parent.append(eid)
        self.meta.append((node.sort, node.scope))
        self.nodes.append((eid, node))
        self.memo[node] = eid
        return eid

    def add_ast(self, ast, scope=()):
        s = sort_of(ast, self.context, scope)
        if not free_vars(ast, frozenset(n for n, _ in scope)) <= self.context.interface:
            raise ValueError("AST changes the fixed free-variable interface")
        op = ast[0]
        payload = (ast[1],) if op in ("var", "exists") else ()
        child_scope = scope
        if op == "exists":
            child_scope += ((ast[1], dict(self.context.terms).get(ast[1], self.context.term_sort)),)
        args = tuple(self.add_ast(c, child_scope) for c in children(ast))
        return self.intern(Node(op, payload, args, s, scope))

    def rebuild(self):
        while True:
            memo, changed = {}, False
            for eid, raw in self.nodes:
                node, owner = self.canonical(raw), self.find(eid)
                if node in memo: changed |= self.union(owner, memo[node])
                else: memo[node] = owner
            self.memo = {n: self.find(e) for n, e in memo.items()}
            if not changed: return

    def members(self):
        result = {}
        for node, eid in self.memo.items():
            result.setdefault(self.find(eid), []).append(node)
        return {e: sorted(ns, key=repr) for e, ns in result.items()}

    def rewrite_round(self):
        members = self.members()
        def variants(e, op):
            return [n for n in members.get(self.find(e), ()) if n.op == op]
        for eid in sorted(members):
            for node in members[eid]:
                op, args, s, scope = node.op, node.args, node.sort, node.scope
                def make(tag, *cs): return self.intern(Node(tag, (), cs, s, scope))
                def merge(e): self.union(eid, e)
                def has(e, tag): return bool(variants(e, tag))
                zero, one, neg = ("F", "T", "notF") if s == "formula" else ("zero", "one", "not")
                meet, join = ("andF", "orF") if s == "formula" else ("and", "or")
                if op == neg:
                    a = args[0]
                    if has(a, zero): merge(make(one))
                    if has(a, one): merge(make(zero))
                    for n in variants(a, neg): merge(n.args[0])
                    for other, dual in ((meet, join), (join, meet)):
                        for n in variants(a, other): merge(make(dual, *(make(neg, c) for c in n.args)))
                if op in (meet, join):
                    a, b = args
                    identity, annihilator, dual = (one, zero, join) if op == meet else (zero, one, meet)
                    if a == b: merge(a)
                    if has(a, identity): merge(b)
                    if has(b, identity): merge(a)
                    if has(a, annihilator) or has(b, annihilator): merge(make(annihilator))
                    if any(self.find(n.args[0]) == self.find(b) for n in variants(a, neg)) or any(
                            self.find(n.args[0]) == self.find(a) for n in variants(b, neg)):
                        merge(make(annihilator))
                    for x, y in ((a, b), (b, a)):
                        for n in variants(y, dual):
                            if self.find(x) in tuple(self.find(c) for c in n.args): merge(x)
                            merge(make(dual, *(make(op, x, c) for c in n.args)))
                        for n in variants(y, op):
                            u, v = n.args
                            merge(make(op, make(op, x, u), v))
                            merge(make(op, make(op, x, v), u))
                    for left in variants(a, dual):
                        for right in variants(b, dual):
                            for x, u in (left.args, left.args[::-1]):
                                for y, v in (right.args, right.args[::-1]):
                                    if self.find(x) == self.find(y): merge(make(dual, x, make(op, u, v)))
                if op == "xor":
                    a, b = args
                    if a == b: merge(make("zero"))
                    if has(a, "zero"): merge(b)
                    if has(b, "zero"): merge(a)
                    if has(a, "one"): merge(make("not", b))
                    if has(b, "one"): merge(make("not", a))
                if op in ("eq0", "ne0"):
                    a = args[0]
                    if has(a, "zero"): merge(make("T" if op == "eq0" else "F"))
                    if self.context.T.startswith("nontrivial") and has(a, "one"):
                        merge(make("F" if op == "eq0" else "T"))
                if op == "notF":
                    for atom, opposite in (("eq0", "ne0"), ("ne0", "eq0")):
                        for n in variants(args[0], atom): merge(make(opposite, n.args[0]))

    def extract(self, root):
        best = {}
        members = self.members()
        for _ in range(len(members) + 1):
            changed = False
            for eid in sorted(members):
                for n in members[eid]:
                    cs = [best.get(self.find(c)) for c in n.args]
                    if any(c is None for c in cs): continue
                    ast = (n.op,) + n.payload + tuple(c[3] for c in cs)
                    candidate = (1 + sum(c[0] for c in cs), source_cost(ast, self.context), repr(ast), ast)
                    if eid not in best or candidate[:3] < best[eid][:3]:
                        best[eid], changed = candidate, True
            if not changed: break
        if self.find(root) not in best: raise ValueError("root has no finite extractable representation")
        return best[self.find(root)][3]


def optimize(root, context, checked_pairs=(), iterations=3, node_limit=1000):
    if iterations < 0: raise ValueError("iterations must be nonnegative")
    graph, rejected, rounds, reason = EGraph(context, node_limit), [], 0, "iteration_limit"
    try:
        root_id = graph.add_ast(root)
    except NodeLimit:
        return root, Report(0, len(graph.nodes), len(graph.members()), 0, 0,
                            tree_cost(root), source_cost(root, context), "root_node_limit")
    try:
        for pair in sorted(checked_pairs, key=lambda p: repr((p.left, p.right, p.scope_key))):
            try:
                if pair.scope_key != context.key: raise ValueError("registry context key mismatch")
                if sort_of(pair.left, context) != sort_of(pair.right, context): raise ValueError("pair sort mismatch")
                graph.union(graph.add_ast(pair.left), graph.add_ast(pair.right), semantic=True)
            except ValueError as exc:
                rejected.append(str(exc))
        graph.rebuild()
        for rounds in range(1, iterations + 1):
            before = (len(graph.nodes), graph.rewrite_unions)
            graph.rewrite_round()
            graph.rebuild()
            if before == (len(graph.nodes), graph.rewrite_unions):
                reason = "saturated"
                break
    except NodeLimit:
        reason = "node_limit"
        graph.rebuild()
    result = graph.extract(root_id)
    report = Report(rounds, len(graph.nodes), len(graph.members()), graph.rewrite_unions,
                    graph.semantic_unions, tree_cost(result), source_cost(result, context), reason, tuple(rejected))
    return result, report


def local_simplify(ast, context, bound=()):
    """Only local identities; no saturation, factoring, or quantifier elimination."""
    op = ast[0]
    if not children(ast): return ast
    child_bound = bound
    if op == "exists": child_bound += ((ast[1], dict(context.terms).get(ast[1], context.term_sort)),)
    cs = tuple(local_simplify(c, context, child_bound) for c in children(ast))
    node = (op,) + ((ast[1],) if op == "exists" else ()) + cs
    z, o, neg = ("F", "T", "notF") if sort_of(ast, context, bound) == "formula" else ("zero", "one", "not")
    if op == neg:
        if cs[0] == (z,): return (o,)
        if cs[0] == (o,): return (z,)
        if cs[0][0] == neg: return cs[0][1]
    if op in ("and", "or", "andF", "orF"):
        identity, annihilator = ((o,), (z,)) if op in ("and", "andF") else ((z,), (o,))
        if cs[0] == cs[1]: return cs[0]
        if annihilator in cs: return annihilator
        if identity in cs: return cs[1] if cs[0] == identity else cs[0]
    return node
