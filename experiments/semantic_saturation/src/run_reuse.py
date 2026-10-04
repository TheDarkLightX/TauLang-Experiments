"""Frozen online fixed-bank reuse study; all new emitted pairs require native gates.

This runner has no mock/native switch. Unit tests inject explicitly named mock
oracles into ReuseArm; the command-line campaign always pins the native binary.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
from pathlib import Path
import argparse
import collections
import json
import math
import random
import time

import engine as E
import checked_registry as R
import native_oracle as N
import support_oracle as S
import study_core as C
import typed_parser as P

SCHEMA = 'tau-online-reuse/v1'
GENERATOR = 'tau-online-reuse-2026-10-04-v1'
BINARY_SHA256 = '874511bf414d0bfbaca224d6fde1cc2514419ad15c912d24dd334f6792909726'
ARMS = ('no_cache', 'exact_syntax', 'fixed_bank_signature', 'semantic_registry')
MIXTURES = ((100, 0, 0), (50, 50, 0), (25, 25, 50), (0, 0, 100))
REPETITIONS = 3
REQUESTS = 64
TIMEOUT = 5.0


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def hashed(value):
    return sha256(canonical(value)).hexdigest()


def file_digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def json_default(value):
    if is_dataclass(value):
        return asdict(value)
    raise TypeError('unsupported JSON value: ' + type(value).__name__)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, default=json_default) + '\n')


def tuples(value):
    return tuple(tuples(x) for x in value) if isinstance(value, list) else value


def make_context(data):
    return E.Context(terms=tuples(data['terms']), T=data['T'], V=tuples(data['V']),
                     K=tuples(data['K']), temporal=data['temporal'])


def context_for(names='abc', **changes):
    data = {'terms': tuple((n, 'tau') for n in names), 'V': tuple(names)}
    data.update(changes)
    return E.Context(**data)


def source_manifest():
    modules = (E, R, N, S, C, P)
    result = {Path(m.__file__).name: file_digest(m.__file__) for m in modules}
    result[Path(__file__).name] = file_digest(__file__)
    protocol = Path(__file__).resolve().parent.parent / 'docs' / 'REUSE_PROTOCOL.md'
    if protocol.exists():
        result['REUSE_PROTOCOL.md'] = file_digest(protocol)
    return result


def protocol():
    return {'schema': SCHEMA, 'generator': GENERATOR, 'requests_per_stream': REQUESTS,
            'repetitions': REPETITIONS, 'arms': ARMS, 'mixtures_exact_equivalent_fresh_syntax': MIXTURES,
            'native_binary_sha256': BINARY_SHA256, 'native_timeout_s': TIMEOUT,
            'native_flags': N.FLAGS, 'term_limits': asdict(R.TERM_LIMITS),
            'formula_limits': asdict(R.FORM_LIMITS), 'interface_size': 3,
            'sorts': ['term:tau', 'formula'], 'warmup_requests': 0,
            'selection': 'minimum objective among original and complete-support-equivalent fixed-bank ASTs',
            'certificates': 'exact ordered emitted pair, full context and checker profile only',
            'timing': 'cold start plus request wall time, per-request rotated interleaving, all three reps',
            'fresh_definition': 'new exact AST, with no assertion of new semantic class',
            'first_exact_request': 'compulsory cold seed, included in nominal exact category and measured misses',
            'semantic_registry_note': 'class-decision memo is redundant with an indexed fixed bank; no free native transfer'}


def rng_for(label):
    return random.Random(int.from_bytes(sha256((GENERATOR + '/' + label).encode()).digest()[:8], 'big'))


def anchor(sort):
    a, b, c = [('var', n) for n in 'abc']
    term = ('xor', ('and', a, b), ('xor', c, c))
    return ('eq0', term) if sort == 'formula' else term


def equivalent_variant(root, index, sort):
    """Injective fixed-length encoding using seven neutral wrapper choices."""
    result = root
    for bit in range(7):
        if sort == 'formula':
            result = ('andF', result, ('T',)) if (index >> bit) & 1 else ('orF', result, ('F',))
        else:
            result = ('and', result, ('one',)) if (index >> bit) & 1 else ('or', result, ('zero',))
    return result


def random_term(rng, budget):
    if budget <= 1:
        return rng.choice([('var', x) for x in 'abc'] + [('zero',), ('one',)])
    if budget == 2 or rng.random() < .2:
        return ('not', random_term(rng, budget - 1))
    left = rng.randrange(1, budget - 1)
    return (rng.choice(('and', 'or', 'xor')), random_term(rng, left), random_term(rng, budget - left - 1))


def fresh_ast(rng, sort, used):
    for _ in range(10000):
        term = random_term(rng, rng.choice((15, 23, 31)))
        ast = (rng.choice(('eq0', 'ne0')), term) if sort == 'formula' else term
        if E.free_vars(ast) == frozenset('abc') and ast not in used:
            return ast
    raise RuntimeError('fresh syntax generator exhausted')


def request_row(index, category, ast, ctx, expected_context='SUPPORTED'):
    return {'index': index, 'category': category, 'ast': ast, 'context': asdict(ctx),
            'context_key': ctx.key, 'source_text': N.typed_render(ast, ctx),
            'expected_context': expected_context}


def rename(ast, mapping):
    if ast[0] == 'var':
        return ('var', mapping[ast[1]])
    if ast[0] == 'exists':
        return ('exists', mapping.get(ast[1], ast[1]), rename(ast[2], mapping))
    return (ast[0],) + tuple(rename(c, mapping) for c in E.children(ast))


def generate_streams():
    """No oracle, signature, optimizer, native call, or result is used here."""
    streams = []
    for sort in ('term:tau', 'formula'):
        root, ctx = anchor(sort), context_for()
        for mixture in MIXTURES:
            name = sort.replace(':', '_') + '-' + '-'.join(map(str, mixture))
            rng = rng_for(name)
            labels = [label for label, percent in zip(('exact', 'equivalent', 'fresh_syntax'), mixture)
                      for _ in range(REQUESTS * percent // 100)]
            if 'exact' in labels:
                labels.remove('exact')
                rng.shuffle(labels)
                labels.insert(0, 'exact')
            else:
                rng.shuffle(labels)
            rows, used, variant = [], {root}, 0
            for i, category in enumerate(labels):
                if category == 'exact':
                    ast = root
                elif category == 'equivalent':
                    variant += 1
                    ast = equivalent_variant(root, variant, sort)
                else:
                    ast = fresh_ast(rng, sort, used)
                if category != 'exact' and ast in used:
                    raise AssertionError('a declared new syntax is repeated')
                used.add(ast)
                rows.append(request_row(i + 1, category, ast, ctx))
            streams.append({'name': name, 'kind': 'mixture', 'sort': sort,
                            'mixture': mixture, 'anchor': root, 'requests': rows})
        contexts = [
            ('base', ctx, root, 'SUPPORTED'),
            ('interface_order', context_for(V=tuple('cba')), root, 'SUPPORTED'),
            ('declaration_order', context_for(terms=tuple((n, 'tau') for n in 'cba')), root, 'SUPPORTED'),
            ('alpha_renamed', context_for('def'), rename(root, dict(zip('abc', 'def'))), 'SUPPORTED'),
            ('theory_mutated', context_for(T='trivialBA'), root, 'REJECTED'),
            ('constants_mutated', context_for(K=('0', '1', 'c')), root, 'REJECTED'),
            ('temporal_mutated', context_for(temporal='one-step'), root, 'REJECTED'),
            ('descriptor_mutated', context_for(terms=tuple((n, 'sbf') for n in 'abc')), root, 'REJECTED')]
        rows = []
        for i in range(REQUESTS):
            category, context, ast, expected = contexts[i % len(contexts)]
            rows.append(request_row(i + 1, category, ast, context, expected))
        streams.append({'name': sort.replace(':', '_') + '-context-safety', 'kind': 'context_safety',
                        'sort': sort, 'requests': rows})
    return streams


def freeze(path):
    path = Path(path)
    if path.exists():
        raise FileExistsError('freeze is immutable; choose a new path')
    streams = generate_streams()
    payload = {'protocol': protocol(), 'source_manifest': source_manifest(), 'streams': streams,
               'stream_sha256': {s['name']: hashed(s) for s in streams},
               'status': 'FROZEN_BEFORE_EXECUTION', 'results_known': False}
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)
    return {'freeze_path': str(path), 'freeze_sha256': file_digest(path),
            'streams': len(streams), 'requests': sum(len(s['requests']) for s in streams)}


@dataclass
class Work:
    bank_builds: int = 0
    bank_s: float = 0.
    signature_calls: int = 0
    signature_s: float = 0.
    support_calls: int = 0
    support_s: float = 0.
    support_observations: int = 0
    support_pair_cache_hits: int = 0
    signature_exact_cache_hits: int = 0
    semantic_class_hits: int = 0


def observation_count(detail):
    observations = detail.get('observations', 0)
    return len(observations) if isinstance(observations, (tuple, list)) else observations or detail.get('stats', {}).get('support_patterns_evaluated', 0)


class ReuseArm:
    def __init__(self, name, oracle):
        if name not in ARMS:
            raise ValueError('unknown arm')
        self.name, self.oracle = name, oracle
        self.banks, self.indices, self.signatures = {}, {}, {}
        self.support_pairs, self.query_results, self.class_decisions = {}, {}, {}
        self.work = Work()

    @property
    def cached(self):
        return self.name != 'no_cache'

    def key(self, ctx, *parts):
        return (self.oracle.profile_key, ctx.key) + parts

    def get_bank(self, ctx, sort, operations):
        key = self.key(ctx, sort)
        if self.cached and key in self.banks:
            return self.banks[key]
        start = time.perf_counter()
        bank = R.candidate_bank(ctx, sort)
        elapsed = time.perf_counter() - start
        self.work.bank_builds += 1
        self.work.bank_s += elapsed
        operations.append({'kind': 'bank', 'context_key': ctx.key, 'sort': sort,
                           'candidates': len(bank), 'elapsed_s': elapsed, 'bank_sha256': hashed(bank)})
        if self.cached:
            self.banks[key] = bank
        return bank

    def get_signature(self, ast, ctx, operations, purpose):
        key = self.key(ctx, R.sort_checked(ast, ctx), ast)
        if key in self.signatures:
            self.work.signature_exact_cache_hits += 1
            return self.signatures[key]
        start = time.perf_counter()
        sig, detail = R.signature(ast, ctx)
        elapsed = time.perf_counter() - start
        self.work.signature_calls += 1
        self.work.signature_s += elapsed
        self.work.support_observations += observation_count(detail)
        operations.append({'kind': 'signature', 'purpose': purpose, 'ast': ast,
                           'context_key': ctx.key, 'elapsed_s': elapsed,
                           'signature_sha256': hashed(sig) if sig is not None else None, 'detail': detail})
        if sig is not None:
            self.signatures[key] = sig
        return sig

    def pair_support(self, ast, candidate, ctx, operations):
        key = self.key(ctx, ast, candidate)
        if self.cached and key in self.support_pairs:
            self.work.support_pair_cache_hits += 1
            return self.support_pairs[key], True
        start = time.perf_counter()
        result = R.comparison(ast, candidate, ctx)
        elapsed = time.perf_counter() - start
        # Keep the immutable raw result; JSON expansion happens outside request timing.
        detail = result
        self.work.support_calls += 1
        self.work.support_s += elapsed
        self.work.support_observations += len(result.observations)
        operations.append({'kind': 'support_pair', 'left': ast, 'right': candidate,
                           'context_key': ctx.key, 'elapsed_s': elapsed, 'detail': detail})
        if self.cached and result.complete and result.status in ('EQUIVALENT', 'DIFFERENT'):
            self.support_pairs[key] = (result.equivalent, True)
        return (result.equivalent, result.complete), False

    def select(self, ast, ctx, sort, operations):
        key = self.key(ctx, ast)
        if self.cached and key in self.query_results:
            return self.query_results[key], {'exact_query_hit': True, 'selection_complete': True}
        bank = self.get_bank(ctx, sort, operations)
        complete = True
        if self.name in ('no_cache', 'exact_syntax'):
            selected = ast
            for candidate in bank:
                if C.objective(candidate, ctx) >= C.objective(ast, ctx):
                    break
                (equivalent, pair_complete), _ = self.pair_support(ast, candidate, ctx, operations)
                complete &= pair_complete
                if equivalent:
                    selected = candidate
                    break
        else:
            bankkey = self.key(ctx, sort)
            if bankkey not in self.indices:
                index, bank_complete = {}, True
                for candidate in bank:
                    sig = self.get_signature(candidate, ctx, operations, 'cold_bank')
                    if sig is None:
                        bank_complete = False
                    else:
                        index.setdefault(sig, candidate)  # Bank is objective sorted.
                if bank_complete:
                    self.indices[bankkey] = index
                complete &= bank_complete
            else:
                index = self.indices[bankkey]
            sig = self.get_signature(ast, ctx, operations, 'query')
            complete &= sig is not None
            classkey = self.key(ctx, sort, sig)
            if self.name == 'semantic_registry' and sig is not None and classkey in self.class_decisions:
                self.work.semantic_class_hits += 1
                candidate = self.class_decisions[classkey]
            else:
                candidate = index.get(sig) if sig is not None else None
                if self.name == 'semantic_registry' and sig is not None and complete:
                    self.class_decisions[classkey] = candidate
            selected = min((ast, candidate), key=lambda a: C.objective(a, ctx)) if candidate is not None else ast
        if self.cached and complete:
            self.query_results[key] = selected
        return selected, {'exact_query_hit': False, 'selection_complete': complete}

    def request(self, row):
        start = time.perf_counter()
        prior = asdict(self.work)
        native_before = len(self.oracle.native.records)
        operations, ctx, ast = [], make_context(row['context']), tuples(row['ast'])
        try:
            sort = R.sort_checked(ast, ctx)
            if len(ctx.V) != 3:
                raise ValueError('reuse study requires an explicit three-variable interface')
            if P.parse_emitted(N.typed_render(ast, ctx), ctx.V) != ast:
                raise ValueError('input typed roundtrip mismatch')
        except (ValueError, RecursionError) as exc:
            return {'request_index': row['index'], 'category': row['category'], 'context_key': ctx.key,
                    'status': 'REJECTED_CONTEXT', 'reason': str(exc), 'native_processes': 0,
                    'native_wall_s': 0., 'native_ordinals': [], 'operations': operations,
                    'work': {k: 0 for k in prior}, 'elapsed_s': time.perf_counter() - start,
                    'final_gate_s': 0., 'final_support_calls': 0, 'final_support_observations': 0,
                    'final_gate_non_native_s': 0., 'exact_query_hit': False, 'final_certificate_hit': False}
        selected, selection = self.select(ast, ctx, sort, operations)
        if not self.cached:
            self.oracle.emission_cache = {}
        gate = R.check_emission(self.oracle, ast, selected, ctx, self.name + ':' + str(row['index']))
        accepted = gate['status'].startswith('ACCEPTED')
        output = selected if accepted else ast
        records = self.oracle.native.records[native_before:]
        after = asdict(self.work)
        work = {k: after[k] - prior[k] for k in prior}
        output_record = {'request_index': row['index'], 'category': row['category'], 'context_key': ctx.key,
                        'status': gate['status'], 'input': ast, 'candidate': selected, 'output': output,
                        'output_text': N.typed_render(output, ctx), 'candidate_changed': selected != ast,
                        'input_bytes': C.emitted_cost(ast, ctx), 'output_bytes': C.emitted_cost(output, ctx),
                        'gate': gate, 'final_gate_s': gate.get('elapsed_s', 0.),
                        'final_support_calls': int(gate.get('support') is not None and not gate.get('cache_hit', False)),
                        'final_support_observations': (observation_count(gate['support'])
                            if gate.get('support') is not None and not gate.get('cache_hit', False) else 0),
                        'final_gate_non_native_s': max(0., gate.get('elapsed_s', 0.) - sum(r['elapsed_s'] for r in records)),
                        'final_certificate_hit': gate.get('cache_hit', False), **selection,
                        'native_processes': len(records), 'native_wall_s': sum(r['elapsed_s'] for r in records),
                        'native_ordinals': [r['ordinal'] for r in records],
                        'operations': operations, 'work': work}
        output_record['elapsed_s'] = time.perf_counter() - start
        return output_record


def new_native_arm(name, binary, directory, manifest):
    oracle = R.CheckedOracle(binary, directory, TIMEOUT)
    if oracle.native.binary_sha256 != BINARY_SHA256:
        raise ValueError('native binary digest is not the primary frozen binary')
    oracle.profile.update(reuse_schema=SCHEMA, checker_sources=manifest)
    oracle.profile_key = hashed(oracle.profile)
    return ReuseArm(name, oracle)


def audit_stream(stream):
    """Untimed independent semantic-label accounting; never feeds an arm cache."""
    started = time.perf_counter()
    seen_syntax, seen_semantics, rows = set(), set(), []
    root = tuples(stream.get('anchor'))
    expected = None
    if root:
        expected, _ = R.signature(root, context_for())
    for row in stream['requests']:
        ctx, ast = make_context(row['context']), tuples(row['ast'])
        try:
            sig, detail = R.signature(ast, ctx)
            syntaxkey, sigkey = (ctx.key, ast), (ctx.key, sig)
            result = {'index': row['index'], 'category': row['category'], 'status': detail.get('status'),
                      'complete': sig is not None, 'exact_syntax_seen': syntaxkey in seen_syntax,
                      'semantic_class_seen_in_exact_context': sig is not None and sigkey in seen_semantics,
                      'signature_sha256': hashed(sig) if sig is not None else None}
            if row['expected_context'] != 'SUPPORTED':
                raise AssertionError('invalid context passed independent stream audit')
            if row['category'] == 'equivalent' and (sig is None or sig != expected):
                raise AssertionError('equivalent workload label was not verified')
            if row['category'] in ('equivalent', 'fresh_syntax') and syntaxkey in seen_syntax:
                raise AssertionError('new syntax label was repeated')
            seen_syntax.add(syntaxkey)
            if sig is not None:
                seen_semantics.add(sigkey)
        except ValueError as exc:
            if row['expected_context'] != 'REJECTED':
                raise
            result = {'index': row['index'], 'category': row['category'], 'status': 'EXPECTED_CONTEXT_REJECTION', 'reason': str(exc)}
        rows.append(result)
    return {'stream': stream['name'], 'native_checked': False, 'rows': rows,
            'elapsed_s': time.perf_counter() - started,
            'accounting': 'separate validation overhead; no result or cache supplied to timed arms'}


def rotation(rep, stream_index, request_index):
    offset = (rep + stream_index + request_index) % len(ARMS)
    return ARMS[offset:] + ARMS[:offset]


def build_summary(all_runs, freeze_hash):
    summaries = []
    for run in all_runs:
        arm_summaries = {}
        curves = {}
        for name in ARMS:
            data = run['arms'][name]
            rows = data['requests']
            total, native, curve = data['startup_s'], 0, []
            for row in rows:
                total += row['elapsed_s']
                native += row['native_processes']
                curve.append({'requests': row['request_index'], 'cumulative_wall_s': total,
                              'cumulative_native_processes': native})
            curves[name] = curve
            arm_summaries[name] = {'startup_s': data['startup_s'], 'total_wall_s': total,
                'request_wall_s': sum(r['elapsed_s'] for r in rows),
                'final_gate_s': sum(r['final_gate_s'] for r in rows),
                'final_support_calls': sum(r['final_support_calls'] for r in rows),
                'final_support_observations': sum(r['final_support_observations'] for r in rows),
                'final_gate_non_native_s': sum(r['final_gate_non_native_s'] for r in rows),
                'native_processes': native, 'native_wall_s': sum(r['native_wall_s'] for r in rows),
                'gate_statuses': dict(collections.Counter(r['status'] for r in rows)),
                'exact_query_hits': sum(r['exact_query_hit'] for r in rows),
                'final_certificate_hits': sum(r['final_certificate_hit'] for r in rows),
                'candidate_changes': sum(r.get('candidate_changed', False) for r in rows),
                'output_bytes': sum(r.get('output_bytes', 0) for r in rows),
                'work': {field: sum(r['work'][field] for r in rows) for field in asdict(Work())}}
        comparisons = {}
        for baseline in ARMS[:-1]:
            difference = [a['cumulative_wall_s'] - b['cumulative_wall_s']
                          for a, b in zip(curves['semantic_registry'], curves[baseline])]
            sustained = next((i + 1 for i, d in enumerate(difference)
                              if d < 0 and all(x < 0 for x in difference[i:])), None)
            mismatch = [i + 1 for i, (a, b) in enumerate(zip(run['arms']['semantic_registry']['requests'],
                                                            run['arms'][baseline]['requests']))
                        if a.get('output') != b.get('output') or a['status'] != b['status']]
            comparisons[baseline] = {'total_wall_difference_s': difference[-1],
                'first_observed_advantage_request': next((i + 1 for i, d in enumerate(difference) if d < 0), None),
                'sustained_advantage_through_64_request': sustained,
                'no_observed_sustained_break_even': sustained is None,
                'native_process_difference': arm_summaries['semantic_registry']['native_processes'] - arm_summaries[baseline]['native_processes'],
                'output_or_status_mismatch_indices': mismatch}
        summaries.append({'stream': run['stream'], 'repetition': run['repetition'],
                          'arms': arm_summaries, 'curves': curves, 'semantic_registry_vs': comparisons})
    return {'schema': SCHEMA, 'freeze_sha256': freeze_hash, 'status': 'COMPLETE', 'runs': summaries,
            'replicates_retained': REPETITIONS,
            'inference_boundary': 'finite synthetic fixed-bank workload; signature-bank indexing is not independent evidence of semantic-class reuse',
            'native_transfer_boundary': 'new exact emitted syntax always requires a new native pair certificate'}


def run_campaign(frozen, freeze_hash, binary, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    campaign_start = time.perf_counter()
    start_manifest = source_manifest()
    write_json(out / 'freeze.json', frozen)
    write_json(out / 'manifest-start.json', start_manifest)
    runs = []
    try:
        audits = [audit_stream(s) for s in frozen['streams']]
        write_json(out / 'stream-audits.json', audits)
        for rep in range(REPETITIONS):
            for si, stream in enumerate(frozen['streams']):
                directory = out / ('rep-' + str(rep + 1)) / stream['name']
                directory.mkdir(parents=True)
                run = {'stream': stream['name'], 'stream_sha256': frozen['stream_sha256'][stream['name']],
                       'repetition': rep + 1, 'request_orders': [], 'arms': {}}
                states = {}
                for name in rotation(rep, si, 0):
                    start = time.perf_counter()
                    states[name] = new_native_arm(name, binary, directory / name / 'native', start_manifest)
                    run['arms'][name] = {'startup_s': time.perf_counter() - start, 'requests': [],
                                          'profile_key': states[name].oracle.profile_key,
                                          'profile': states[name].oracle.profile}
                for i, row in enumerate(stream['requests']):
                    order = rotation(rep, si, i)
                    run['request_orders'].append(order)
                    for name in order:
                        record = states[name].request(row)
                        raw_name = 'request-' + f'{i + 1:03}' + '.json'
                        write_json(directory / name / raw_name, record)
                        compact = {k: v for k, v in record.items() if k not in ('operations', 'gate')}
                        compact['raw_receipt'] = name + '/' + raw_name
                        compact['raw_receipt_sha256'] = file_digest(directory / name / raw_name)
                        run['arms'][name]['requests'].append(compact)
                        if row['expected_context'] == 'REJECTED' and record['status'] != 'REJECTED_CONTEXT':
                            raise RuntimeError('context isolation failure')
                        if record['status'] in ('DIFFERENT', 'REJECTED_SUPPORT_DIFFERENT'):
                            raise RuntimeError('support/native contradiction; stop and investigate')
                    outputs = [run['arms'][name]['requests'][-1].get('candidate') for name in ARMS]
                    if any(value != outputs[0] for value in outputs[1:]):
                        incomplete = any(not run['arms'][name]['requests'][-1].get('selection_complete', True) for name in ARMS)
                        reason = 'inconclusive support selection' if incomplete else 'matched-menu candidate disagreement'
                        raise RuntimeError(reason + '; stop and investigate')
                for name in ARMS:
                    run['arms'][name]['native_summary'] = states[name].oracle.native.finish()
                # Raw request files contain details; retain a run-level index as well.
                write_json(directory / 'run.json', run)
                runs.append(run)
                write_json(out / 'progress.json', {'completed_runs': len(runs), 'total_runs': REPETITIONS * len(frozen['streams']),
                                                  'last_stream': stream['name'], 'last_repetition': rep + 1})
        end_manifest = source_manifest()
        write_json(out / 'manifest-end.json', end_manifest)
        if end_manifest != start_manifest:
            raise RuntimeError('source identity changed during reuse campaign')
        summary = build_summary(runs, freeze_hash)
        summary['campaign_wall_s_before_final_serialization'] = time.perf_counter() - campaign_start
        summary['validation_overhead_s'] = sum(a['elapsed_s'] for a in audits)
        summary['timing_excludes'] = 'stream label audit and orchestration JSON serialization; native receipt persistence inside request is included'
        write_json(out / 'summary.json', summary)
        return summary
    except BaseException as exc:
        write_json(out / 'FAILED.json', {'status': 'FAILED', 'error': str(exc), 'completed_runs': len(runs),
                                       'preserved_raw_receipts': True, 'manifest_end': source_manifest()})
        raise


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonnegative_finite(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0, 'invalid nonnegative finite measure: ' + label)


def validate_timing(record):
    tolerance = 1e-7
    for field in ('elapsed_s', 'native_wall_s', 'final_gate_s', 'final_gate_non_native_s'):
        nonnegative_finite(record[field], field)
    for field, value in record['work'].items():
        nonnegative_finite(value, 'work.' + field)
    for operation in record['operations']:
        nonnegative_finite(operation['elapsed_s'], 'operation elapsed_s')
    selection_s = sum(record['work'][field] for field in ('bank_s', 'signature_s', 'support_s'))
    require(record['elapsed_s'] + tolerance >= selection_s + record['final_gate_s'], 'request clock is below nonoverlapping selection plus final gate')
    require(record['final_gate_s'] + tolerance >= record['native_wall_s'], 'gate clock is below fresh native time')
    require(abs(record['final_gate_non_native_s'] - max(0., record['final_gate_s'] - record['native_wall_s'])) <= tolerance,
            'final-gate residual mismatch')
    for kind, field in (('bank', 'bank_s'), ('signature', 'signature_s'), ('support_pair', 'support_s')):
        measured = sum(op['elapsed_s'] for op in record['operations'] if op['kind'] == kind)
        require(abs(record['work'][field] - measured) <= tolerance, 'selection component/operations mismatch: ' + field)
    if 'gate' in record:
        nonnegative_finite(record['gate']['elapsed_s'], 'gate.elapsed_s')
        require(abs(record['final_gate_s'] - record['gate']['elapsed_s']) <= tolerance, 'raw gate/request time mismatch')
    if record['final_certificate_hit']:
        require(record['native_wall_s'] == 0., 'warm certificate has nonzero fresh native wall time')


def frozen_profile(manifest):
    return {'theory': 'nontrivialABA', 'descriptor': 'tau', 'constants': ['0', '1'],
            'temporal': 'none', 'binary_sha256': BINARY_SHA256, 'flags': N.FLAGS,
            'timeout_s': TIMEOUT, 'term_limits': asdict(R.TERM_LIMITS),
            'formula_limits': asdict(R.FORM_LIMITS),
            'support_source_sha256': file_digest(S.__file__),
            'reuse_schema': SCHEMA, 'checker_sources': manifest}


def expected_selection(ast, ctx, memo):
    key = (ctx.key, ast)
    if key in memo:
        return memo[key]
    selected, complete = ast, True
    for candidate in R.candidate_bank(ctx, R.sort_checked(ast, ctx)):
        if C.objective(candidate, ctx) >= C.objective(ast, ctx):
            break
        result = R.comparison(ast, candidate, ctx)
        complete &= result.complete
        if result.equivalent:
            selected = candidate
            break
    memo[key] = selected, complete
    return selected, complete


def validate_gate_record(record, row, profile_key, native_directory, certificates):
    """Bind each accepted/unknown gate to both exact emitted commands and argv."""
    validate_timing(record)
    require(record['context_key'] == make_context(row['context']).key, 'request context identity mismatch')
    if record['status'] == 'REJECTED_CONTEXT':
        require(row['expected_context'] == 'REJECTED', 'unexpected context rejection')
        require(record['native_processes'] == 0 and not record['native_ordinals'], 'rejected context used native')
        return []
    ctx, source = make_context(row['context']), tuples(row['ast'])
    candidate, output = tuples(record['candidate']), tuples(record['output'])
    require(tuples(record['input']) == source and record['context_key'] == ctx.key, 'request/context mismatch')
    require(record['input_bytes'] == C.emitted_cost(source, ctx), 'input-byte mismatch')
    require(record['output_bytes'] == C.emitted_cost(output, ctx), 'output-byte mismatch')
    require(record['output_text'] == N.typed_render(output, ctx), 'output text/AST mismatch')
    gate = record['gate']
    require(gate['status'] == record['status'], 'gate status mismatch')
    require(record['final_certificate_hit'] == gate.get('cache_hit', False), 'cache-hit label mismatch')
    accepted = gate['status'].startswith('ACCEPTED')
    require(output == (candidate if accepted else source), 'emitted output does not follow gate')
    require(C.objective(candidate, ctx) <= C.objective(source, ctx), 'candidate regressed')
    for ast in (source, candidate):
        text = N.typed_render(ast, ctx)
        require(P.parse_emitted(text, ctx.V) == ast, 'typed serialization failed roundtrip')
    if 'native' not in gate:
        require(not accepted and gate['status'].startswith('REJECTED_SUPPORT_'), 'missing native gate evidence')
        require(record['native_processes'] == 0 and not record['native_ordinals'], 'ungated record charged native')
        return []
    left, right = N.typed_render(source, ctx), N.typed_render(candidate, ctx)
    exact_pair_key = (profile_key, ctx.key, left, right)
    if R.sort_checked(source, ctx) != 'formula':
        left, right = f'(({left}) ^ ({right})) = 0', 'T'
    prefix = 'all ' + ', '.join(f'{n} : tau' for n in ctx.V) + ' '
    commands = [f'normalize {prefix}(({left}) -> ({right}))',
                f'normalize {prefix}(({right}) -> ({left}))']
    receipts = [gate['native'][direction] for direction in ('forward', 'reverse')]
    ordinals = []
    for direction, receipt, command in zip(('forward', 'reverse'), receipts, commands):
        nonnegative_finite(receipt['elapsed_s'], 'native elapsed_s')
        require(receipt['command'] == command, direction + ' command does not bind exact emitted pair')
        require(receipt['argv'][1:] == list(N.FLAGS) + ['-e', command], direction + ' argv mismatch')
        require(Path(receipt['argv'][0]).is_absolute(), 'native binary path is not absolute')
        require(receipt['binary_sha256'] == BINARY_SHA256, 'native binary identity mismatch')
        require(receipt['timeout_s'] == TIMEOUT, 'native timeout mismatch')
        require(receipt['truth'] == N.exact_truth(receipt), 'native truth classification mismatch')
        require(receipt.get('TAU_environment_removed') is True, 'native environment not sanitized')
        ordinal = receipt['ordinal']
        require(isinstance(ordinal, int) and ordinal > 0, 'invalid native ordinal')
        persisted = json.loads((Path(native_directory) / f'{ordinal:04d}.json').read_text())
        require(canonical(persisted) == canonical(receipt), 'native receipt file mismatch')
        ordinals.append(ordinal)
    require(ordinals[0] != ordinals[1], 'two native directions share an ordinal')
    truth = [r['truth'] for r in receipts]
    expected = ('ACCEPTED_IDENTITY' if source == candidate else 'ACCEPTED') if truth == ['T', 'T'] else ('DIFFERENT' if 'F' in truth else 'UNKNOWN')
    require(gate['status'] == expected, 'native/gate verdict mismatch')
    require(gate.get('structural_identity') == (source == candidate), 'identity label mismatch')
    if gate.get('cache_hit'):
        require(accepted and exact_pair_key in certificates, 'unissued or cross-context certificate hit')
        require(certificates[exact_pair_key] == ordinals, 'certificate provenance mismatch')
        require(record['native_processes'] == 0 and record['native_ordinals'] == [], 'cache hit charged fresh processes')
        return []
    require(record['native_processes'] == 2 and record['native_ordinals'] == ordinals, 'cold gate must charge both directions')
    require(abs(record['native_wall_s'] - sum(r['elapsed_s'] for r in receipts)) < 1e-9, 'native wall-time mismatch')
    if accepted:
        certificates[exact_pair_key] = ordinals
    return ordinals


def validate_campaign(out, expected_freeze_hash):
    out = Path(out)
    require(not (out / 'FAILED.json').exists(), 'campaign contains a failure marker')
    require(file_digest(out / 'freeze.json') == expected_freeze_hash, 'frozen bytes mismatch')
    frozen = json.loads((out / 'freeze.json').read_text())
    require(canonical(frozen['protocol']) == canonical(protocol()), 'frozen protocol mismatch')
    require(frozen['source_manifest'] == source_manifest(), 'checker source identity mismatch')
    require(json.loads((out / 'manifest-start.json').read_text()) == frozen['source_manifest'], 'start manifest mismatch')
    require(json.loads((out / 'manifest-end.json').read_text()) == frozen['source_manifest'], 'end manifest mismatch')
    require(frozen['stream_sha256'] == {s['name']: hashed(s) for s in frozen['streams']}, 'stream hash mismatch')
    runs, processes, requests, selections = [], 0, 0, {}
    for rep in range(REPETITIONS):
        for si, stream in enumerate(frozen['streams']):
            directory = out / ('rep-' + str(rep + 1)) / stream['name']
            run = json.loads((directory / 'run.json').read_text())
            require(run['stream_sha256'] == frozen['stream_sha256'][stream['name']], 'run stream identity mismatch')
            require(run['stream'] == stream['name'] and run['repetition'] == rep + 1, 'run identity mismatch')
            require(canonical(run['request_orders']) == canonical([rotation(rep, si, i) for i in range(REQUESTS)]), 'interleaving order mismatch')
            for name in ARMS:
                data, seen_ordinals, certificates = run['arms'][name], set(), {}
                nonnegative_finite(data['startup_s'], 'startup_s')
                require(canonical(data['profile']) == canonical(frozen_profile(frozen['source_manifest'])), 'exact frozen checker profile mismatch')
                require(data['profile_key'] == hashed(data['profile']), 'profile key mismatch')
                require(data['profile']['checker_sources'] == frozen['source_manifest'], 'profile source mismatch')
                require(data['profile']['binary_sha256'] == BINARY_SHA256, 'profile binary mismatch')
                require(len(data['requests']) == REQUESTS, 'wrong request count')
                for compact, row in zip(data['requests'], stream['requests']):
                    expected_path = name + '/request-' + f"{row['index']:03d}" + '.json'
                    require(compact['raw_receipt'] == expected_path, 'raw receipt path mismatch')
                    path = directory / expected_path
                    require(file_digest(path) == compact['raw_receipt_sha256'], 'raw request receipt digest mismatch')
                    record = json.loads(path.read_text())
                    require(record['request_index'] == row['index'] and record['category'] == row['category'], 'request ordinal/category mismatch')
                    if name == 'no_cache':
                        require(not record['final_certificate_hit'] and not record['exact_query_hit'], 'no-cache arm reused a certificate or result')
                    projected = {k: v for k, v in record.items() if k not in ('operations', 'gate')}
                    expected_projection = {k: v for k, v in compact.items() if k not in ('raw_receipt', 'raw_receipt_sha256')}
                    require(canonical(projected) == canonical(expected_projection), 'raw/compact record mismatch')
                    if row['expected_context'] == 'SUPPORTED' and record.get('selection_complete'):
                        expected, complete = expected_selection(tuples(row['ast']), make_context(row['context']), selections)
                        require(complete and tuples(record['candidate']) == expected, 'candidate does not match independently recomputed fixed-bank menu')
                    newly_charged = validate_gate_record(record, row, data['profile_key'], directory / name / 'native', certificates)
                    require(not seen_ordinals.intersection(newly_charged), 'native process charged twice')
                    seen_ordinals.update(newly_charged)
                    requests += 1
                require(seen_ordinals == set(range(1, len(seen_ordinals) + 1)), 'native ordinal gaps')
                require(len(seen_ordinals) == data['native_summary']['processes'], 'native total mismatch')
                native_files = list((directory / name / 'native').glob('[0-9][0-9][0-9][0-9].json'))
                require(len(native_files) == len(seen_ordinals), 'unaccounted native receipt files')
                processes += len(seen_ordinals)
            runs.append(run)
    recomputed = build_summary(runs, expected_freeze_hash)
    summary = json.loads((out / 'summary.json').read_text())
    for key, value in recomputed.items():
        require(canonical(summary[key]) == canonical(value), 'summary mismatch: ' + key)
    return {'status': 'VERIFIED', 'freeze_sha256': expected_freeze_hash,
            'runs': len(runs), 'requests': requests, 'native_processes': processes,
            'checks': 'exact stream/profile/source identity; both emitted commands and argv; strict native verdicts; cache provenance; raw hashes; timing bounds; recomputed fixed-bank selection and cumulative summaries'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--freeze-out')
    p.add_argument('--verify-out')
    p.add_argument('--freeze')
    p.add_argument('--expect-freeze-sha256')
    p.add_argument('--binary')
    p.add_argument('--out')
    args = p.parse_args()
    if not __debug__:
        p.error('optimized Python is not an admitted execution mode')
    if args.verify_out:
        if not args.expect_freeze_sha256 or any((args.freeze_out, args.freeze, args.binary, args.out)):
            p.error('--verify-out requires only --expect-freeze-sha256')
        print(json.dumps(validate_campaign(args.verify_out, args.expect_freeze_sha256), sort_keys=True))
        return
    if args.freeze_out:
        if any((args.freeze, args.expect_freeze_sha256, args.binary, args.out)):
            p.error('--freeze-out cannot be combined with execution flags')
        print(json.dumps(freeze(args.freeze_out), sort_keys=True))
        return
    if not all((args.freeze, args.expect_freeze_sha256, args.binary, args.out)):
        p.error('run requires --freeze, --expect-freeze-sha256, --binary and --out')
    freeze_hash = file_digest(args.freeze)
    if freeze_hash != args.expect_freeze_sha256:
        p.error('freeze digest mismatch')
    frozen = json.loads(Path(args.freeze).read_text())
    if canonical(frozen['protocol']) != canonical(protocol()):
        p.error('protocol differs from frozen protocol')
    if frozen['source_manifest'] != source_manifest():
        p.error('source files differ from frozen manifest')
    if frozen['stream_sha256'] != {s['name']: hashed(s) for s in frozen['streams']}:
        p.error('frozen stream hash mismatch')
    if canonical(frozen['streams']) != canonical(generate_streams()):
        p.error('stream bytes differ from frozen generator')
    if file_digest(args.binary) != BINARY_SHA256:
        p.error('native binary digest mismatch')
    summary = run_campaign(frozen, freeze_hash, args.binary, args.out)
    print(json.dumps({'status': summary['status'], 'runs': len(summary['runs']), 'out': args.out}, sort_keys=True))


if __name__ == '__main__':
    main()
