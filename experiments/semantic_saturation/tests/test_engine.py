"""Mechanical engine checks; these are not native Tau validity evidence."""
import itertools
import random
import unittest
from dataclasses import replace

from engine import (CheckedPair, Context, EGraph, free_vars, local_simplify,
                    optimize, pure_term_signature, render, sort_of, tree_cost)


def model(ast, values, top=3):
    """Independent finite BA of subsets of two atoms (values 0,1,2,3)."""
    tag = ast[0]
    if tag == "var": return values[ast[1]]
    if tag in ("zero", "one", "T", "F"):
        return {"zero": 0, "one": top, "T": True, "F": False}[tag]
    if tag == "exists":
        return any(model(ast[2], {**values, ast[1]: b}, top) for b in range(top + 1))
    left = model(ast[1], values, top)
    if tag == "not": return top ^ left
    if tag == "notF": return not left
    if tag == "eq0": return left == 0
    if tag == "ne0": return left != 0
    right = model(ast[2], values, top)
    if tag == "and": return left & right
    if tag == "or": return left | right
    if tag == "xor": return left ^ right
    if tag == "andF": return left and right
    if tag == "orF": return left or right
    raise ValueError(tag)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.context = Context(terms=tuple((n, "tau") for n in ("a", "b", "c")))
        self.a, self.b, self.c = (("var", n) for n in ("a", "b", "c"))

    def test_factoring_cost_and_truth(self):
        original = ("or", ("and", self.a, self.c), ("and", self.b, self.c))
        result, report = optimize(original, self.context)
        self.assertEqual(tree_cost(result), 5)
        self.assertEqual(report.tree_cost, 5)
        for a, b, c in itertools.product(range(4), repeat=3):
            self.assertEqual(model(result, dict(a=a, b=b, c=c)), (a & c) | (b & c))
        self.assertEqual(pure_term_signature(original, ("a", "b", "c")),
                         pure_term_signature(result, ("a", "b", "c")))

    def test_congruence_rebuild(self):
        graph = EGraph(self.context)
        left = graph.add_ast(("eq0", ("and", self.a, self.b)))
        right = graph.add_ast(("eq0", ("and", self.c, self.b)))
        self.assertNotEqual(graph.find(left), graph.find(right))
        # Artificial class identification tests congruence, not semantic validity.
        graph.union(graph.add_ast(self.a), graph.add_ast(self.c))
        graph.rebuild()
        self.assertEqual(graph.find(left), graph.find(right))

    def test_cycle_has_finite_minimum_extraction(self):
        graph = EGraph(self.context)
        a = graph.add_ast(self.a)
        cycle = graph.add_ast(("and", self.a, ("one",)))
        graph.union(a, cycle)
        graph.rebuild()
        self.assertEqual(graph.extract(cycle), self.a)

    def test_scope_barrier_prevents_variable_capture(self):
        graph = EGraph(self.context)
        free = graph.add_ast(self.b)
        bound = graph.add_ast(self.b, (("b", "tau"),))
        with self.assertRaisesRegex(ValueError, "scope"):
            graph.union(free, bound, semantic=True)

    def test_quantifier_elimination_needs_external_checked_pair(self):
        context = replace(self.context, V=("a",))
        original = ("exists", "b", ("andF", ("ne0", self.b), ("andF",
                    ("eq0", ("and", self.b, ("not", self.a))),
                    ("ne0", ("and", self.a, ("not", self.b))))))
        cheaper = ("ne0", self.a)
        baseline, _ = optimize(original, context)
        # No built-in atomless-algebra/quantifier elimination rule is present.
        self.assertEqual(baseline[0], "exists")
        hybrid, report = optimize(original, context,
                                  [CheckedPair(original, cheaper, context.key)])
        self.assertEqual(hybrid, cheaper)
        self.assertEqual(report.semantic_unions, 1)
        # The finite model is deliberately insufficient for this atomless claim.
        self.assertFalse(model(original, {"a": 1}))
        self.assertTrue(model(cheaper, {"a": 1}))

    def test_bad_context_and_sort_pairs_are_rejected(self):
        original = ("eq0", self.a)
        foreign = replace(self.context, T="different-theory")
        pairs = [CheckedPair(original, ("T",), foreign.key),
                 CheckedPair(original, self.a, self.context.key)]
        result, report = optimize(original, self.context, pairs)
        self.assertEqual(result, original)
        self.assertEqual(report.semantic_unions, 0)
        self.assertEqual(len(report.rejected_pairs), 2)
        with self.assertRaisesRegex(ValueError, "one BA descriptor"):
            Context(terms=(("a", "tau"), ("b", "bv[8]")))

    def test_declared_resource_limits_match_both_arms(self):
        original = ("or", ("and", self.a, self.c), ("and", self.b, self.c))
        pair = CheckedPair(original, ("and", self.c, ("or", self.a, self.b)), self.context.key)
        for pairs in ((), (pair,)):
            first = optimize(original, self.context, pairs, iterations=3, node_limit=30)
            second = optimize(original, self.context, pairs, iterations=3, node_limit=30)
            self.assertEqual(first, second)
            self.assertLessEqual(first[1].nodes, 30)
            self.assertLessEqual(first[1].iterations, 3)
        result, report = optimize(original, self.context, node_limit=2)
        self.assertEqual(result, original)
        self.assertEqual(report.stop_reason, "root_node_limit")

    def test_fixed_interface_and_typed_native_rendering(self):
        context = Context(terms=(("a", "tau"),), V=("a",))
        ast = ("exists", "b", ("eq0", ("xor", self.a, self.b)))
        self.assertEqual(free_vars(ast), {"a"})
        self.assertEqual(render(ast, context), "ex b : tau (((a ^ b) = 0))")
        self.assertEqual(sort_of(ast, context), "formula")
        self.assertEqual(local_simplify(ast, context), ast)
        self.assertEqual(optimize(ast, context)[0], ast)
        with self.assertRaisesRegex(ValueError, "interface"):
            optimize(("eq0", self.b), replace(self.context, V=("a",)))
        with self.assertRaisesRegex(ValueError, "pure"):
            pure_term_signature(("eq0", self.a), ("a",))

    def test_seeded_model_soundness_with_shadowing(self):
        rng = random.Random(20261004)
        def term(depth):
            if depth == 0: return rng.choice((self.a, self.b, self.c, ("zero",), ("one",)))
            if rng.randrange(4) == 0: return ("not", term(depth - 1))
            return (rng.choice(("and", "or", "xor")), term(depth - 1), term(depth - 1))
        def formula(depth):
            if depth == 0: return (rng.choice(("eq0", "ne0")), term(1))
            op = rng.choice(("notF", "andF", "orF", "exists"))
            if op == "notF": return (op, formula(depth - 1))
            if op == "exists": return (op, rng.choice(("a", "b")), formula(depth - 1))
            return (op, formula(depth - 1), formula(depth - 1))
        fixtures = [term(2) for _ in range(24)] + [formula(2) for _ in range(24)]
        for ast in fixtures:
            result, _ = optimize(ast, self.context, node_limit=250)
            local = local_simplify(ast, self.context)
            self.assertEqual(sort_of(result, self.context), sort_of(ast, self.context))
            for vals in itertools.product(range(4), repeat=3):
                env = dict(zip(("a", "b", "c"), vals))
                self.assertEqual(model(result, env), model(ast, env), (ast, result, env))
                self.assertEqual(model(local, env), model(ast, env), (ast, local, env))


if __name__ == "__main__":
    unittest.main()
