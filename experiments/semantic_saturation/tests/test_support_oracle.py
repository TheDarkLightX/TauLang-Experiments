"""Semantic and fail-closed controls for the independent atomless-BA oracle."""

from dataclasses import FrozenInstanceError
import unittest

from support_oracle import (Limits, ScopeRejected, active_patterns, compare_formulas,
                            compare_terms, describe_support, evaluate_formula,
                            refinement_supports, support_count)


def forall(name, body):
    return ("notF", ("exists", name, ("notF", body)))


def equal(left, right):
    return ("eq0", ("xor", left, right))


class SupportOracleTests(unittest.TestCase):
    def test_support_counts_exclude_trivial_algebra(self):
        self.assertEqual([support_count(n) for n in range(4)], [1, 3, 15, 255])
        self.assertEqual([item.support_mask for item in evaluate_formula(("T",)).observations], [1])
        with self.assertRaises(ScopeRejected):
            active_patterns(0)

    def test_refinements_are_unique_preserve_projection_and_cover_three_choices(self):
        # Cells 0 and 2 of a two-parameter partition are active.
        supports = tuple(refinement_supports(5, 2))
        self.assertEqual(len(supports), 9)
        self.assertEqual(len(set(supports)), 9)
        for support in supports:
            projection = 0
            for pattern in active_patterns(support):
                projection |= 1 << (pattern & 3)
            self.assertEqual(projection, 5)
        self.assertEqual(tuple(refinement_supports(1, 0)), (1, 2, 3))

    def test_atomless_proper_split_iff_nonzero_with_unused_parameters(self):
        a, b = ("var", "a"), ("var", "b")
        proper = ("andF", ("eq0", ("and", b, ("not", a))),
                  ("andF", ("ne0", b), ("ne0", ("and", a, ("not", b)))))
        formula = ("exists", "b", proper)
        for names, expected_true in [(('a',), 2), (('a', 'c'), 12), (('a', 'c', 'd'), 240)]:
            with self.subTest(names=names):
                result = compare_formulas(formula, ("ne0", a), free_variables=names)
                self.assertTrue(result.equivalent, result.reason)
                self.assertEqual(len(result.observations), support_count(len(names)))
                self.assertEqual(sum(item.left for item in result.observations), expected_true)
                self.assertGreater(result.stats.existential_refinements, 0)

    def test_two_valued_formula_is_false_on_proper_element(self):
        x = ("var", "x")
        formula = ("orF", ("eq0", x), ("eq0", ("not", x)))
        result = compare_formulas(formula, ("T",))
        self.assertEqual(result.status, "DIFFERENT")
        self.assertTrue(result.complete)
        self.assertEqual(sum(item.left for item in result.observations), 2)
        self.assertEqual(result.counterexample.support_mask, 3)
        self.assertEqual(describe_support(result.free_variables, 3), ((0,), (1,)))
        self.assertFalse(result.counterexample.left)
        self.assertTrue(result.counterexample.right)

    def test_pure_terms_have_independent_full_pointwise_signatures(self):
        a, b = ("var", "a"), ("var", "b")
        absorption = compare_terms(("or", a, ("and", a, b)), a)
        self.assertTrue(absorption.equivalent)
        self.assertEqual(absorption.left_signature, (False, True, False, True))
        self.assertEqual(absorption.right_signature, absorption.left_signature)
        de_morgan = compare_terms(("not", ("and", a, b)), ("or", ("not", a), ("not", b)))
        self.assertTrue(de_morgan.equivalent)
        self.assertTrue(compare_terms(("xor", a, a), ("zero",)).equivalent)
        self.assertTrue(compare_terms(("or", a, ("not", a)), ("one",)).equivalent)
        self.assertTrue(compare_formulas(equal(("or", a, ("and", a, b)), a), ("T",)).equivalent)

    def test_complement_is_relative_to_active_support(self):
        x = ("var", "x")
        result = evaluate_formula(("eq0", ("not", x)))
        self.assertEqual(tuple(item.value for item in result.observations), (False, True, False))

    def test_shadowed_binders_do_not_capture_free_or_outer_variables(self):
        x = ("var", "x")
        body = ("andF", ("ne0", x), ("exists", "x", ("eq0", x)))
        self.assertTrue(compare_formulas(body, ("ne0", x)).equivalent)
        nested = ("exists", "x", ("andF", ("eq0", x), ("exists", "x", ("ne0", x))))
        self.assertTrue(compare_formulas(nested, ("T",)).equivalent)

    def test_separate_witnesses_and_shared_witness_are_distinguished(self):
        x = ("var", "x")
        separate = ("andF", ("exists", "x", ("eq0", x)), ("exists", "x", ("ne0", x)))
        shared = ("exists", "x", ("andF", ("eq0", x), ("ne0", x)))
        self.assertTrue(compare_formulas(separate, ("T",)).equivalent)
        self.assertTrue(compare_formulas(shared, ("F",)).equivalent)

    def test_quantifier_order_and_alternation(self):
        a, b = ("var", "a"), ("var", "b")
        self.assertTrue(compare_formulas(forall("a", ("exists", "b", equal(a, b))), ("T",)).equivalent)
        self.assertTrue(compare_formulas(("exists", "b", forall("a", equal(a, b))), ("F",)).equivalent)

    def test_one_way_implication_does_not_establish_equivalence(self):
        x = ("var", "x")
        eq_zero = ("eq0", x)
        forward = ("orF", ("notF", eq_zero), ("T",))
        reverse = ("orF", ("notF", ("T",)), eq_zero)
        self.assertTrue(compare_formulas(forward, ("T",)).equivalent)
        self.assertEqual(compare_formulas(reverse, ("T",)).status, "DIFFERENT")
        self.assertEqual(compare_formulas(eq_zero, ("T",)).status, "DIFFERENT")

    def test_common_interface_prevents_variable_rename_signature_collision(self):
        x, y = ("var", "x"), ("var", "y")
        result = compare_formulas(("eq0", x), ("eq0", y))
        self.assertEqual(result.free_variables, ('x', 'y'))
        self.assertEqual(len(result.observations), 15)
        self.assertEqual(result.status, "DIFFERENT")
        self.assertEqual(compare_formulas(("eq0", x), ("eq0", y), free_variables=('x',)).status, "REJECTED")
        self.assertEqual(compare_formulas(("T",), ("T",), free_variables=('x', 'x')).status, "REJECTED")

    def test_explicit_variable_order_is_recorded_and_interpreted(self):
        x, y = ("var", "x"), ("var", "y")
        result = compare_terms(x, y, free_variables=('y', 'x'))
        self.assertEqual(result.free_variables, ('y', 'x'))
        self.assertEqual(result.left_signature, (False, False, True, True))
        self.assertEqual(result.right_signature, (False, True, False, True))

    def test_caps_fail_closed_preserve_partial_observations(self):
        x = ("var", "x")
        partial = compare_formulas(("eq0", x), ("eq0", x), limits=Limits(max_states=1))
        self.assertEqual(partial.status, "UNKNOWN")
        self.assertFalse(partial.complete)
        self.assertFalse(partial.equivalent)
        self.assertEqual(len(partial.observations), 1)
        self.assertEqual(partial.stats.support_patterns_evaluated, 1)
        nodes = compare_formulas(("T",), ("T",), limits=Limits(max_node_evaluations=0))
        self.assertEqual(nodes.status, "UNKNOWN")
        quantified = ("exists", "x", ("F",))
        self.assertEqual(compare_formulas(quantified, ("F",), limits=Limits(max_states=2)).status, "UNKNOWN")
        slots = compare_formulas(quantified, ("F",), limits=Limits(max_variable_slots=0))
        self.assertEqual(slots.status, "REJECTED")
        self.assertEqual(compare_formulas(quantified, ("F",), limits=Limits(max_quantifier_depth=0)).status, "REJECTED")
        self.assertEqual(compare_formulas(("T",), ("T",), free_variables=('x',),
                                          limits=Limits(max_initial_supports=2)).status, "REJECTED")
        self.assertEqual(compare_terms(x, x, limits=Limits(max_states=1)).status, "UNKNOWN")

    def test_exhaustive_false_exists_enumerates_all_three_variable_refinements(self):
        result = evaluate_formula(('exists', 'b', ('F',)), free_variables=('a', 'c', 'd'))
        self.assertEqual(result.status, 'COMPLETE')
        self.assertEqual(len(result.observations), 255)
        self.assertFalse(any(item.value for item in result.observations))
        # Sum over nonempty masks of 3**active_cells = (1+3)**8 - 1.
        self.assertEqual(result.stats.existential_refinements, 4 ** 8 - 1)
        self.assertEqual(result.stats.states_evaluated, 255 + 4 ** 8 - 1)

    def test_invalid_asts_types_and_scopes_are_rejected(self):
        for bad in [('bv', 8, 1), ('forall', 'x', ('T',)), ('eq0', ('T',)),
                    ('exists', '', ('T',)), ('T', ('F',)), ['T'], ('var', 'x')]:
            with self.subTest(ast=bad):
                result = compare_formulas(bad, ('T',))
                self.assertEqual(result.status, "REJECTED")
                self.assertFalse(result.equivalent)
        for bad in [('var', ''), ('and', ('var', 'x')), ('eq0', ('zero',))]:
            self.assertEqual(compare_terms(bad, ('zero',)).status, "REJECTED")
        self.assertEqual(compare_formulas(('T',), ('T',), limits=Limits(max_states=-1)).status, "REJECTED")
        self.assertEqual(compare_formulas(('T',), ('T',), free_variables='x').status, "REJECTED")
        self.assertEqual(compare_formulas(('T',), ('T',), free_variables=42).status, "REJECTED")
        self.assertEqual(compare_formulas(('T',), ('T',), free_variables={'x'}).status, "REJECTED")
        self.assertEqual(compare_formulas(('T',), ('T',), free_variables=('a', 'b', 'c', 'd')).status, "REJECTED")
        deep = ('T',)
        for _ in range(1200):
            deep = ('notF', deep)
        self.assertEqual(compare_formulas(deep, ('T',), limits=Limits(max_ast_depth=2000)).status, 'REJECTED')

    def test_results_are_immutable_and_replay_is_deterministic(self):
        formula = ('exists', 'x', ('ne0', ('var', 'x')))
        first, second = compare_formulas(formula, ('T',)), compare_formulas(formula, ('T',))
        self.assertEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.status = 'DIFFERENT'


if __name__ == '__main__':
    unittest.main()
