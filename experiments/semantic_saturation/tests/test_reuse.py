"""Unit-level reuse contract checks. Mock receipts are never native evidence."""
import copy
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import engine as E
import checked_registry as R
import run_reuse as U
import support_oracle as S


class MockNative:
    def __init__(self, truth='T'):
        self.truth, self.records = truth, []

    def run(self, command, label):
        record = {'ordinal': len(self.records) + 1, 'label': label, 'command': command,
                  'binary_sha256': 'MOCK-NOT-NATIVE', 'elapsed_s': 0., 'truth': self.truth,
                  'stdout': '%1: ' + self.truth, 'stderr': '', 'returncode': 0,
                  'timed_out': False, 'evidence_kind': 'unit_test_mock',
                  'argv': ['/MOCK-UNIT-TEST-BINARY', *U.N.FLAGS, '-e', command],
                  'timeout_s': U.TIMEOUT, 'TAU_environment_removed': True}
        self.records.append(record)
        return record


class MockOracle:
    def __init__(self, truth='T', profile='MOCK-PROFILE'):
        self.native = MockNative(truth)
        self.profile_key = profile


def row(ast, ctx=None, index=1):
    return U.request_row(index, 'unit_test_only', ast, ctx or U.context_for())


class ReuseTests(unittest.TestCase):
    def test_streams_deterministic_exact_lengths_counts_and_roundtrip(self):
        streams = U.generate_streams()
        self.assertEqual(U.hashed(streams), U.hashed(U.generate_streams()))
        self.assertEqual(len(streams), 10)
        for stream in streams:
            self.assertEqual(len(stream['requests']), 64)
            if stream['kind'] == 'mixture':
                self.assertEqual([sum(r['category'] == label for r in stream['requests'])
                                  for label in ('exact', 'equivalent', 'fresh_syntax')],
                                 [64 * p // 100 for p in stream['mixture']])
                seen = set()
                for r in stream['requests']:
                    ast, ctx = U.tuples(r['ast']), U.make_context(r['context'])
                    self.assertEqual(U.P.parse_emitted(r['source_text'], ctx.V), ast)
                    self.assertEqual(E.free_vars(ast), frozenset('abc'))
                    if r['category'] != 'exact':
                        self.assertNotIn(ast, seen)
                    seen.add(ast)

    def test_variant_laws_hold_on_terms_and_non_two_valued_formulas(self):
        # Selected implementation fixtures, not execution of the frozen streams.
        for sort in ('term:tau', 'formula'):
            for index in (1, 17, 32, 63):
                root = U.anchor(sort)
                self.assertTrue(R.comparison(root, U.equivalent_variant(root, index, sort), U.context_for()).equivalent)

    def test_exact_queries_cache_final_certificates_only_in_cached_arms(self):
        for name in U.ARMS:
            oracle = MockOracle()
            arm = U.ReuseArm(name, oracle)
            first = arm.request(row(U.anchor('term:tau')))
            second = arm.request(row(U.anchor('term:tau'), index=2))
            self.assertEqual(first['native_processes'], 2)
            self.assertEqual(second['native_processes'], 2 if name == 'no_cache' else 0)
            self.assertEqual(second['final_certificate_hit'], name != 'no_cache')
            self.assertEqual(second['exact_query_hit'], name != 'no_cache')
            self.assertEqual(first['output'], second['output'])
            self.assertTrue(all(r['evidence_kind'] == 'unit_test_mock' for r in oracle.native.records))

    def test_new_equivalent_syntax_always_requires_two_new_native_processes(self):
        for name in U.ARMS:
            arm = U.ReuseArm(name, MockOracle())
            root = U.anchor('term:tau')
            arm.request(row(root))
            result = arm.request(row(U.equivalent_variant(root, 5, 'term:tau'), index=2))
            self.assertEqual(result['native_processes'], 2)
            self.assertFalse(result['final_certificate_hit'])
            self.assertFalse(result['exact_query_hit'])
            if name == 'semantic_registry':
                self.assertEqual(result['work']['semantic_class_hits'], 1)

    def test_unknown_native_is_not_a_certificate(self):
        for name in U.ARMS:
            arm = U.ReuseArm(name, MockOracle('UNKNOWN'))
            first = arm.request(row(U.anchor('term:tau')))
            second = arm.request(row(U.anchor('term:tau'), index=2))
            self.assertEqual(first['status'], 'UNKNOWN')
            self.assertEqual(second['native_processes'], 2)
            self.assertFalse(second['final_certificate_hit'])
            self.assertEqual(second['output'], U.anchor('term:tau'))
            self.assertEqual(getattr(arm.oracle, 'emission_cache', {}), {})

    def test_unknown_support_and_signatures_are_not_cached(self):
        unknown = S.TermComparison('UNKNOWN', tuple('abc'), (), False, reason='test cap')
        arm = U.ReuseArm('exact_syntax', MockOracle())
        with patch.object(R, 'comparison', return_value=unknown):
            for _ in range(2):
                arm.pair_support(('var', 'a'), ('var', 'b'), U.context_for(), [])
        self.assertEqual(arm.support_pairs, {})
        self.assertEqual(arm.work.support_calls, 2)
        arm = U.ReuseArm('semantic_registry', MockOracle())
        with patch.object(R, 'signature', return_value=(None, {'status': 'UNKNOWN'})):
            for _ in range(2):
                self.assertIsNone(arm.get_signature(('var', 'a'), U.context_for(), [], 'test'))
        self.assertEqual(arm.signatures, {})
        self.assertEqual(arm.work.signature_calls, 2)

    def test_same_ast_new_order_declarations_profile_cannot_reuse_cert(self):
        arm = U.ReuseArm('semantic_registry', MockOracle())
        root = U.anchor('term:tau')
        contexts = [U.context_for(), U.context_for(V=tuple('cba')),
                    U.context_for(terms=tuple((n, 'tau') for n in 'cba'))]
        self.assertEqual(len({c.key for c in contexts}), 3)
        for ctx in contexts:
            result = arm.request(row(root, ctx))
            self.assertEqual(result['native_processes'], 2)
            self.assertFalse(result['final_certificate_hit'])
        arm.oracle.profile_key = 'MOCK-PROFILE-CHANGED'
        result = arm.request(row(root))
        self.assertEqual(result['native_processes'], 2)
        self.assertFalse(result['exact_query_hit'])

    def test_alpha_renamed_context_needs_new_cert(self):
        arm = U.ReuseArm('semantic_registry', MockOracle())
        root = U.anchor('term:tau')
        arm.request(row(root))
        result = arm.request(row(U.rename(root, dict(zip('abc', 'def'))), U.context_for('def')))
        self.assertEqual(result['native_processes'], 2)
        self.assertFalse(result['final_certificate_hit'])

    def test_invalid_context_never_calls_native_or_populates_caches(self):
        for change in ({'T': 'trivial'}, {'temporal': 'one-step'}, {'K': ('0', '1', 'x')},
                       {'terms': tuple((x, 'sbf') for x in 'abc')}):
            arm = U.ReuseArm('semantic_registry', MockOracle())
            result = arm.request(row(U.anchor('term:tau'), U.context_for(**change)))
            self.assertEqual(result['status'], 'REJECTED_CONTEXT')
            self.assertEqual(result['native_processes'], 0)
            self.assertFalse(arm.banks)
            self.assertFalse(arm.query_results)

    def test_fixed_index_and_semantic_memo_choose_identical_fixed_bank_member(self):
        fixture = [('var', 'a'), U.anchor('term:tau'),
                   U.equivalent_variant(U.anchor('term:tau'), 7, 'term:tau'),
                   ('xor', ('var', 'a'), ('xor', ('var', 'b'), ('var', 'c')))]
        arms = [U.ReuseArm(name, MockOracle()) for name in U.ARMS]
        for ast in fixture:
            results = [arm.request(row(ast)) for arm in arms]
            self.assertEqual(len({r['candidate'] for r in results}), 1)

    def test_class_memo_precedes_per_query_original_guard(self):
        arm = U.ReuseArm('semantic_registry', MockOracle())
        a = ('var', 'a')
        first = arm.request(row(a))
        longer = ('or', a, ('zero',))
        second = arm.request(row(longer))
        self.assertEqual(first['output'], a)
        self.assertEqual(second['output'], a)
        self.assertEqual(second['work']['semantic_class_hits'], 1)
        # An unrepresented class cannot smuggle a prior retained original into the bank.
        outside = ('xor', a, ('xor', ('var', 'b'), ('var', 'c')))
        r1 = arm.request(row(outside))
        r2 = arm.request(row(('or', outside, ('zero',))))
        self.assertEqual(r1['output'], outside)
        self.assertEqual(r2['output'], ('or', outside, ('zero',)))

    def test_no_cache_native_identity_is_checked_and_labeled(self):
        arm = U.ReuseArm('no_cache', MockOracle())
        result = arm.request(row(('var', 'a')))
        self.assertEqual(result['status'], 'ACCEPTED_IDENTITY')
        self.assertEqual(result['native_processes'], 2)
        self.assertTrue(result['gate']['structural_identity'])

    def test_both_directions_present_in_mock_gate_commands(self):
        arm = U.ReuseArm('exact_syntax', MockOracle())
        result = arm.request(row(U.anchor('formula')))
        records = arm.oracle.native.records
        self.assertEqual(len(records), 2)
        self.assertIn(':emitted-forward', records[0]['label'])
        self.assertIn(':emitted-reverse', records[1]['label'])
        self.assertIn('all a : tau, b : tau, c : tau', records[0]['command'])
        self.assertNotEqual(records[0]['command'], records[1]['command'])
        self.assertTrue(result['gate']['roundtrip_ast_equal'])

    def test_freeze_is_byte_hashed_and_refuses_overwrite_without_executing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'frozen.json'
            result = U.freeze(target)
            payload = json.loads(target.read_text())
            self.assertEqual(result['freeze_sha256'], U.file_digest(target))
            self.assertFalse(payload['results_known'])
            self.assertEqual(payload['stream_sha256'], {s['name']: U.hashed(s) for s in payload['streams']})
            with self.assertRaises(FileExistsError):
                U.freeze(target)

    def test_validator_binds_both_commands_argv_and_cache_provenance(self):
        arm = U.ReuseArm('exact_syntax', MockOracle())
        request = row(U.anchor('formula'))
        first = arm.request(request)
        warm = arm.request(request)
        with tempfile.TemporaryDirectory() as tmp, patch.object(U, 'BINARY_SHA256', 'MOCK-NOT-NATIVE'):
            for receipt in arm.oracle.native.records:
                U.write_json(Path(tmp) / f"{receipt['ordinal']:04d}.json", receipt)
            certificates = {}
            self.assertEqual(U.validate_gate_record(first, request, arm.oracle.profile_key, tmp, certificates), [1, 2])
            self.assertEqual(U.validate_gate_record(warm, request, arm.oracle.profile_key, tmp, certificates), [])
            mutations = []
            reverse_command = copy.deepcopy(first)
            reverse_command['gate']['native']['reverse']['command'] = reverse_command['gate']['native']['forward']['command']
            mutations.append(reverse_command)
            reverse_argv = copy.deepcopy(first)
            reverse_argv['gate']['native']['reverse']['argv'][-1] = 'normalize T'
            mutations.append(reverse_argv)
            forward_argv = copy.deepcopy(first)
            forward_argv['gate']['native']['forward']['argv'][-1] = 'normalize T'
            mutations.append(forward_argv)
            bad_stdout = copy.deepcopy(first)
            bad_stdout['gate']['native']['reverse']['stdout'] = '%1: F'
            mutations.append(bad_stdout)
            duplicate_charge = copy.deepcopy(warm)
            duplicate_charge['native_processes'] = 2
            duplicate_charge['native_ordinals'] = [1, 2]
            mutations.append(duplicate_charge)
            for mutation in mutations:
                with self.assertRaises(ValueError):
                    U.validate_gate_record(mutation, request, arm.oracle.profile_key, tmp, certificates)
            with self.assertRaises(ValueError):
                U.validate_gate_record(warm, request, 'MOCK-CHANGED-PROFILE', tmp, certificates)

    def test_validator_rejects_timing_zeroing_nan_and_warm_native_cost(self):
        arm = U.ReuseArm('exact_syntax', MockOracle())
        request = row(U.anchor('formula'))
        first = arm.request(request)
        warm = arm.request(request)
        for field, value in (('elapsed_s', 0.), ('elapsed_s', float('nan')),
                             ('final_gate_s', -1.), ('final_gate_non_native_s', 42.)):
            altered = copy.deepcopy(first)
            altered[field] = value
            with self.assertRaises(ValueError):
                U.validate_timing(altered)
        altered = copy.deepcopy(warm)
        altered['native_wall_s'] = 1e-12
        with self.assertRaises(ValueError):
            U.validate_timing(altered)
        # Construct explicitly mocked positive receipt durations, then zero every
        # reported request/component clock consistently. The receipt binding must
        # still reject the falsified zero-cost report.
        zeroed = copy.deepcopy(first)
        for receipt in zeroed['gate']['native'].values():
            receipt['elapsed_s'] = .01
        for field in ('elapsed_s', 'native_wall_s', 'final_gate_s', 'final_gate_non_native_s'):
            zeroed[field] = 0.
        zeroed['gate']['elapsed_s'] = 0.
        for field in ('bank_s', 'signature_s', 'support_s'):
            zeroed['work'][field] = 0.
        for operation in zeroed['operations']:
            operation['elapsed_s'] = 0.
        with tempfile.TemporaryDirectory() as tmp, patch.object(U, 'BINARY_SHA256', 'MOCK-NOT-NATIVE'):
            for receipt in zeroed['gate']['native'].values():
                U.write_json(Path(tmp) / f"{receipt['ordinal']:04d}.json", receipt)
            with self.assertRaises(ValueError):
                U.validate_gate_record(zeroed, request, arm.oracle.profile_key, tmp, {})

    def test_independent_expected_selection_uses_fixed_menu_and_exact_context(self):
        memo = {}
        root = U.anchor('term:tau')
        selected, complete = U.expected_selection(root, U.context_for(), memo)
        self.assertTrue(complete)
        self.assertEqual(selected, ('and', ('var', 'a'), ('var', 'b')))
        self.assertNotEqual(selected, root)
        reordered = U.context_for(V=tuple('cba'))
        self.assertEqual(U.expected_selection(root, reordered, memo),
                         (('and', ('var', 'b'), ('var', 'a')), True))
        self.assertEqual(len(memo), 2)
        expected = U.frozen_profile(U.source_manifest())
        self.assertEqual(expected['reuse_schema'], U.SCHEMA)
        self.assertEqual(expected['term_limits'], asdict(R.TERM_LIMITS))
        self.assertEqual(expected['formula_limits'], asdict(R.FORM_LIMITS))

    def test_proposal_raw_support_serializes_after_request_clock(self):
        arm = U.ReuseArm('exact_syntax', MockOracle())
        result = arm.request(row(U.anchor('term:tau')))
        details = [op['detail'] for op in result['operations'] if op['kind'] == 'support_pair']
        self.assertTrue(details)
        self.assertTrue(all(U.is_dataclass(detail) for detail in details))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'unit-test-mock.json'
            U.write_json(path, result)
            saved = json.loads(path.read_text())
            self.assertTrue(any(op.get('detail', {}).get('observations') for op in saved['operations']))

    def test_rotation_retains_three_reps_and_balances_within_stream(self):
        self.assertEqual(U.REPETITIONS, 3)
        for rep in range(3):
            for position in range(4):
                observed = [U.rotation(rep, 0, i)[position] for i in range(64)]
                self.assertEqual({name: observed.count(name) for name in U.ARMS}, {name: 16 for name in U.ARMS})


if __name__ == '__main__':
    unittest.main()
