"""Unit/development checks only; these are not held-out study cases."""
from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
import random
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import baselines as B
from engine import Context, children, pure_term_signature, tree_cost
from native_oracle import typed_render
import study_core


def _hang_worker(connection, ast, context, mode, propositions):
    connection.send(("started", "cnf"))
    time.sleep(10)


def _partial_worker(connection, ast, context, mode, propositions):
    connection.send(("started", "cnf"))
    connection.send(("candidate", B.CandidateReceipt("cnf", "ok", ast,
        B.measure_ast(ast, context), propositional_check={"status": "equivalent", "complete": True})))
    connection.send(("started", "dnf"))
    time.sleep(10)


def _error_worker(connection, ast, context, mode, propositions):
    connection.send(("error", "deliberate development failure"))
    connection.close()


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.x, self.y, self.z = ("var", "x"), ("var", "y"), ("var", "z")
        self.context = Context((("x", "tau"), ("y", "tau"), ("z", "tau")))

    def run_baseline(self, ast, **kwargs):
        result = B.run_sympy_baseline(ast, self.context, **kwargs)
        self.assertLessEqual(result.metrics.emitted_utf8_bytes,
                             result.input_metrics.emitted_utf8_bytes)
        self.assertEqual(result.metrics.emitted, typed_render(result.output, self.context))
        json.dumps(result.to_dict())
        return result

    def test_metrics_match_authoritative_serializer_and_main_metrics(self):
        shared = ("and", self.x, self.y)
        ast = ("or", shared, shared)
        got = B.measure_ast(ast, self.context)
        expected = study_core.metrics(ast, self.context)
        self.assertEqual(got.emitted, "(((x : tau) & (y : tau)) | ((x : tau) & (y : tau)))")
        self.assertEqual(got.tree_nodes, 7)
        self.assertEqual(got.dag_nodes, 4)
        self.assertEqual(got.tree_depth, 3)
        self.assertEqual(got.emitted_utf8_bytes, expected["expression_bytes"])
        self.assertEqual(got.file_bytes, expected["file_bytes"])
        for key in ("tree_nodes", "dag_nodes", "tree_depth"):
            self.assertEqual(getattr(got, key), expected[key])
        self.assertEqual(got.tree_nodes, tree_cost(ast))

    def test_utf8_bytes_are_not_character_count(self):
        context = Context((("α", "tau"),))
        metrics = B.measure_ast(("var", "α"), context)
        self.assertGreater(metrics.emitted_utf8_bytes, len(metrics.emitted))
        self.assertEqual(metrics.emitted_utf8_bytes, len(metrics.emitted.encode("utf-8")))

    def test_factoring(self):
        ast = ("or", ("and", self.x, self.y), ("and", self.x, ("not", self.y)))
        result = self.run_baseline(ast)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.output, self.x)
        self.assertEqual(result.selected, "cnf")
        self.assertEqual([r.form for r in result.candidates], ["original", "cnf", "dnf"])
        self.assertTrue(all(r.propositional_check["complete"] for r in result.candidates))
        self.assertEqual(result.candidates[1].propositional_check["assignments_checked"], 4)
        self.assertEqual(result.environment["sympy_version"], "1.14.0")
        self.assertIsNone(result.environment["dontcare"])
        self.assertTrue(result.environment["constructor_auto_simplification"])
        self.assertGreaterEqual(result.wall_seconds, result.preparation_seconds)
        self.assertGreaterEqual(result.wall_seconds, result.worker_phase_seconds["import_seconds"])

    def test_term_xor_keeps_smaller_original(self):
        ast = ("xor", self.x, self.y)
        result = self.run_baseline(ast)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.output, ast)
        self.assertEqual(result.selected, "original")
        for candidate in result.candidates[1:]:
            self.assertGreater(candidate.metrics.emitted_utf8_bytes, result.metrics.emitted_utf8_bytes)

    def test_cnf_and_dnf_are_both_considered(self):
        ast = ("or", ("and", self.x, self.y), ("and", self.x, self.z))
        result = self.run_baseline(ast)
        forms = {r.form: r for r in result.candidates}
        self.assertLess(forms["cnf"].metrics.emitted_utf8_bytes, forms["dnf"].metrics.emitted_utf8_bytes)
        self.assertEqual(result.selected, "cnf")

    def test_constants_have_zero_propositions(self):
        for ast in (("zero",), ("one",), ("T",), ("F",)):
            with self.subTest(ast=ast):
                result = self.run_baseline(ast)
                self.assertEqual(result.output, ast)
                self.assertEqual(result.selected, "original")
                self.assertEqual(result.proposition_order, ())
                self.assertEqual(result.candidates[1].propositional_check["assignments_checked"], 1)

    def test_formula_atoms_restore_whole_terms(self):
        atom = ("eq0", ("xor", self.x, self.y))
        other = ("ne0", ("and", self.x, self.z))
        ast = ("orF", ("andF", atom, other), ("andF", atom, ("notF", other)))
        result = self.run_baseline(ast)
        self.assertEqual(result.mode, "formula_skeleton")
        self.assertEqual(result.output, atom)
        self.assertEqual({p["ast"] for p in result.proposition_order}, {atom, other})
        self.assertEqual(result.candidates[1].propositional_check["semantics"],
                         "formula_skeleton_propositional_assignments")

    def test_equality_and_inequality_remain_distinct_opaque_atoms(self):
        ast = ("orF", ("eq0", self.x), ("ne0", self.x))
        result = self.run_baseline(ast)
        self.assertEqual(result.output, ast)
        self.assertEqual(len(result.proposition_order), 2)
        # Although this is a BA tautology, the conservative skeleton lane must
        # not discover that by incorrectly treating the BA variable as Boolean.
        self.assertNotEqual(result.output, ("T",))

    def test_quantified_proper_split_is_opaque(self):
        a = ("var", "a")
        split = ("exists", "a", ("andF", ("ne0", a), ("ne0", ("not", a))))
        result = self.run_baseline(split)
        self.assertEqual(result.output, split)
        self.assertEqual([p["ast"] for p in result.proposition_order], [split])
        repeated = self.run_baseline(("andF", split, split))
        self.assertEqual(repeated.output, split)

    def test_quantifiers_keep_exact_binder_identity(self):
        a, b = ("var", "a"), ("var", "b")
        qa, qb = ("exists", "a", ("eq0", a)), ("exists", "b", ("eq0", b))
        result = self.run_baseline(("orF", qa, qb))
        self.assertEqual(len(result.proposition_order), 2)
        self.assertEqual({p["ast"] for p in result.proposition_order}, {qa, qb})

    def test_deterministic_explicit_symbol_order(self):
        ast = ("and", self.z, ("or", self.x, self.y))
        first, second = self.run_baseline(ast), self.run_baseline(ast)
        self.assertEqual(first.proposition_order, second.proposition_order)
        self.assertEqual(first.output, second.output)
        self.assertEqual([p["ast"] for p in first.proposition_order], [self.x, self.y, self.z])
        self.assertEqual(first.environment["active_sympy_symbol_order"],
                         ["p000000", "p000001", "p000002"])

    def test_explicit_cap_counts_input_before_constructor_simplification(self):
        ast = ("and", ("zero",), ("or", self.x, self.y))
        result = self.run_baseline(ast, max_propositions=1)
        self.assertEqual(result.status, "capped")
        self.assertEqual(result.output, ast)
        self.assertEqual([r.status for r in result.candidates], ["retained", "capped", "capped"])
        self.assertNotIn("process_inclusive_seconds", result.worker_phase_seconds)

    def test_timeout_kills_and_reaps_worker(self):
        before = {p.pid for p in multiprocessing.active_children()}
        with mock.patch.object(B, "_worker_portfolio", _hang_worker):
            result = self.run_baseline(self.x, timeout_seconds=0.05)
        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.output, self.x)
        self.assertEqual([r.status for r in result.candidates],
                         ["retained", "timeout", "deadline_exhausted"])
        self.assertNotEqual(result.environment["worker_exitcode"], 0)
        self.assertLess(result.wall_seconds, 1.0)
        self.assertEqual({p.pid for p in multiprocessing.active_children()}, before)

    def test_valid_cnf_is_retained_when_dnf_times_out(self):
        with mock.patch.object(B, "_worker_portfolio", _partial_worker):
            result = self.run_baseline(self.x, timeout_seconds=0.05)
        self.assertEqual(result.status, "partial")
        self.assertEqual([r.status for r in result.candidates], ["retained", "ok", "timeout"])
        self.assertEqual(result.output, self.x)

    def test_worker_error_has_receipts_and_original_fallback(self):
        with mock.patch.object(B, "_worker_portfolio", _error_worker):
            result = self.run_baseline(self.x)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.output, self.x)
        self.assertTrue(all(r.status == "error" for r in result.candidates[1:]))
        self.assertIn("deliberate development failure", result.candidates[1].reason)

    def test_roundtrip_negative_control(self):
        result = B.check_propositional_roundtrip(self.x, ("not", self.x), "pure_term", (self.x,))
        self.assertEqual(result["status"], "inequivalent")
        self.assertFalse(result["complete"])
        self.assertEqual(result["counterexample_assignment"], 0)

    def test_reject_malformed_sort_and_context(self):
        invalid = [("unknown",), ("and", self.x), ("and", self.x, ("T",)),
                   ("var", "undeclared"), ["zero"], ("not", ["zero"]),
                   ("exists", "a", ("var", "a"))]
        for ast in invalid:
            with self.subTest(ast=ast), self.assertRaises(ValueError):
                B.run_sympy_baseline(ast, self.context)
        for context in (Context(self.context.terms, temporal="eventually"),
                        Context(self.context.terms, V=("y",)),
                        Context(self.context.terms, K=("0", "1", "opaque")),
                        Context(self.context.terms, T="other")):
            with self.subTest(context=context), self.assertRaises(ValueError):
                B.run_sympy_baseline(self.x, context)

    def test_reject_invalid_limits_and_ast_size(self):
        for kwargs in ({"timeout_seconds": 0}, {"timeout_seconds": float("nan")},
                       {"max_propositions": -1}, {"max_ast_nodes": 0},
                       {"max_ast_depth": 201}, {"max_propositions": True},
                       {"max_ast_nodes": 1}, {"max_ast_depth": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                B.run_sympy_baseline(("not", self.x), self.context, **kwargs)

    def test_seeded_development_terms_independently_match_corner_signatures(self):
        rng = random.Random(73011)  # Unit-test namespace; never a holdout seed.
        def term(depth):
            if depth == 0 or rng.random() < .25:
                return rng.choice((self.x, self.y, self.z, ("zero",), ("one",)))
            if rng.random() < .2:
                return ("not", term(depth - 1))
            return (rng.choice(("and", "or", "xor")), term(depth - 1), term(depth - 1))
        for _ in range(16):
            ast = term(4)
            result = self.run_baseline(ast)
            self.assertEqual(result.status, "ok")
            self.assertEqual(pure_term_signature(ast, ("x", "y", "z")),
                             pure_term_signature(result.output, ("x", "y", "z")))
            self.assertEqual(result.metrics.tree_nodes, tree_cost(result.output))


if __name__ == "__main__":
    unittest.main()
