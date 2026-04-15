# Qelim Epiplexity Routing Experiment

This note records a bounded experiment, not a production optimization claim.

Question:

```text
Can a cheap structure metric predict when the restricted KB qelim prepass is
worth running?
```

The experiment treats epiplexity as a routing signal. It asks where exploitable
structure is visible:

- in the source syntax,
- in the compiled qelim carrier,
- or not clearly enough to route.

## Command

```bash
python3 scripts/run_qelim_epiplexity_router.py \
  --max-generated-cases 34 \
  --reps 10 \
  --out results/local/qelim-epiplexity-router.json
```

The script runs four modes:

```text
auto
auto+kb_guarded
bdd
bdd+kb_guarded
```

It checks exact output parity against `auto`.

## Metric

The source metric parses the Boolean formula and looks for restricted KB
rewrite structure. Two detectors are recorded:

- `raw_syntax_detector`: any restricted source rewrite appears useful,
- `guard_aligned_detector`: the rewrite is aligned with the current Tau guarded
  KB implementation.

The important correction from this experiment is that raw source structure is
not always still available at the qelim prepass. For example, a double-negation
shape may be visible in the input text but already collapsed by the time the KB
guard sees the compiled expression.

## Current Receipt

Current local receipt:

```text
cases: 40
repetitions: 10
semantic parity: passed
```

Detector result for the implementation-aligned metric:

```text
true positives: 24
true negatives: 16
false positives: 0
false negatives: 0
```

Raw source detector result:

```text
true positives: 24
true negatives: 15
false positives: 1
false negatives: 0
```

The one raw false positive is the `double_neg` case. That is useful negative
knowledge: structure visible in source syntax can disappear before the current
guarded KB pass.

Fresh local rerun, April 15 2026:

```text
implementation-aligned detector: 24 true positives, 16 true negatives, 0 false positives, 0 false negatives
raw source detector:             24 true positives, 15 true negatives, 1 false positive, 0 false negatives
semantic parity:                 passed
```

The classifier result is stable on the current corpus. Timing numbers below are
empirical measurements, not semantic facts.

## Timing Result

Median-based routing regret on this corpus:

```text
auto lane regret: 0.854718 ms
bdd lane regret:  0.284027 ms
```

Fresh local rerun, April 15 2026:

```text
auto median-regret sum: 1.405884 ms
bdd median-regret sum:  0.314494 ms
```

Sum-of-case-medians comparison:

```text
auto route: 16.055879 ms
auto base:  16.016488 ms
auto+KB:    15.945601 ms
oracle:     15.201161 ms

bdd route: 16.702219 ms
bdd base:  17.235192 ms
bdd+KB:    17.085916 ms
oracle:    16.418192 ms
```

Interpretation:

- The implementation-aligned metric is good at predicting whether the current
  guarded KB pass has structural work to do.
- The same metric is not yet strong enough to pick the fastest route in the
  already-composed `auto` lane.
- In the BDD sublane, the route improved against plain `bdd` on this corpus,
  but still had regret against the oracle that picks the locally fastest mode
  case by case.
- This supports keeping guarded KB opt-in and improving the selector before
  promoting it.

## Boundary

This is not a theorem that epiplexity optimizes qelim.

The checked part is semantic parity of the tested routes on the generated
corpus. The timing result is empirical. A stronger claim would need a formal
cost model, a larger corpus, and separate thresholds for syntax-visible
structure versus carrier-visible structure.

## Auto Guard Modes

The experimental Tau patch now accepts explicit auto-guard modes:

```text
TAU_QELIM_AUTO_GUARD=raw
TAU_QELIM_AUTO_GUARD=dup
TAU_QELIM_AUTO_GUARD=both
```

`raw` is the older source-shape guard. It rejects some high-quantifier,
low-free-variable shapes before compiling into the BDD experiment.

`dup` is a compiled-carrier duplication guard. It computes cheap preflight
metrics after compiling the formula into the Boolean-expression carrier:

```text
tree_nodes
unique_nodes
support
quantified
free
max_occurrence
```

It rejects only when the compiled expression has enough quantified variables,
few free variables, high repeated occurrence, and a large tree-to-unique-node
ratio.

The current local receipt is negative for the old broad guard on the generated
wide corpus:

```text
no guard, auto qelim total:   45.620071 ms
raw guard, auto qelim total:  209.973470 ms
dup guard, auto qelim total:  44.859902 ms
both guards, auto qelim total: 211.652646 ms
```

Interpretation:

- `raw` and `both` are not default candidates on this corpus.
- `dup` is safe to keep as an opt-in experiment, but its benefit is not yet
  large enough to promote.
- The useful lesson is architectural: guard modes must be separable, because a
  broad fallback guard can erase the speed advantage of the `auto` backend.

## Route Telemetry

The matrix runner now records route histograms:

```text
route_counts = { route_name: run_count }
```

The first wide telemetry run used `34` generated cases and `3` repetitions.
It found:

```text
auto route_counts: { pure: 102 }
auto non-pure runs: 0
```

This changes the benchmark interpretation. The current wide matrix tests
pure-backend behavior and KB rewrite overhead. It does not test BDD-fallback
guard profitability, because the fallback lane was never exercised.

Next benchmark requirement:

- build a fallback-heavy qelim corpus with non-`pure` auto routes,
- rerun `raw`, `dup`, and `both` on that corpus,
- only then decide whether a fallback guard is an optimization rather than a
  correct but irrelevant branch-selection mechanism.

## Compile-Reject Corpus

A separate fallback corpus now targets relational atoms that the current BDD
experiment does not compile, for example:

```text
qelim ex x (x = a)
qelim ex x ((x = a) && (x = b))
qelim ex x ex y ((x = y) && (y = a))
```

The patched backend emits an explicit route before falling back:

```text
route=compile_reject
```

Receipt:

```text
cases:                 7
repetitions:           5
auto route_counts:     { compile_reject: 35 }
default qelim total:   61.057971 ms
auto qelim total:      69.211975 ms
auto overhead:          8.154004 ms
```

Interpretation:

- Compile rejection is now observable rather than hidden as missing BDD stats.
- Diagnostic-normalized output parity holds on the fallback corpus.
- This is not a BDD optimization. It is a support-boundary and fallback-quality
  receipt.
- The only obvious optimization from this corpus is a source-level
  relational-shape guard that skips the failed BDD compile attempt, and the
  likely gain is modest on these cases.

## Relational-Shape Guard

The experimental patch now has two additional opt-in modes:

```text
TAU_QELIM_AUTO_GUARD=rel
TAU_QELIM_AUTO_GUARD=all
```

`rel` catches equality or inequality atoms where neither side is `0`, such as
`(x = a)` or `(x = y)`. The current BDD compiler rejects those atoms, so this
guard skips the doomed compile attempt and falls back immediately.

Receipt on the fallback corpus:

```text
auto route_counts:       { compile_reject: 35 }
auto+rel route_counts:   { auto_rel_guard: 35 }
auto qelim total:        71.764624 ms
auto+rel qelim total:    66.990378 ms
rel saving vs auto:       4.774246 ms
rel overhead vs default:  4.768047 ms
```

Interpretation:

- `rel` is a useful support-boundary cleanup.
- It improves the experimental `auto` fallback path on this corpus.
- It still does not beat direct default qelim, so it is not a major speed
  breakthrough.
- The higher-value search is still a compile-supported non-`pure` BDD corpus
  and a selector for real Tau workloads.

## Non-Pure BDD Corpus

The main qelim optimization benchmark is now the non-pure BDD corpus:

```text
python3 scripts/run_qelim_nonpure_bdd_corpus.py \
  --reps 10 \
  --out results/local/qelim-nonpure-bdd-corpus-reps10.json
```

The corpus uses only compiler-supported atoms such as `(x = 0)`, but arranges
quantified variables in both positive and negative positions so they survive
pure-variable elimination. This exercises the compiled-carrier lanes that the
wide matrix missed.

Receipt:

```text
auto route_counts:          { components: 20, dp: 30, monolithic: 20 }
default qelim total:        211.520230 ms
auto qelim total:            29.173886 ms
auto+KB guarded total:       28.955846 ms
auto speedup vs default:      7.250328 x
auto root nodes:            240
direct BDD root nodes:      550
```

Interpretation:

- This is the current strongest qelim optimization evidence.
- The speedup comes from the experimental `auto` BDD/DP/component route, not
  from KB rewriting.
- `auto+KB guarded` is close to `auto`, but `kb_steps_sum = 0`, so this corpus
  does not prove a KB rewrite benefit.
- Component decomposition reduces BDD work compared with forcing direct
  monolithic BDD.

Boundary:

- This is still a generated corpus.
- The next credibility step is to find real Tau specs with the same route mix.

## Policy-Shaped Non-Pure Corpus

The next corpus uses formulas shaped like the safe table demos, not only generic
route stress tests:

```bash
python3 scripts/run_qelim_policy_shape_corpus.py \
  --reps 10 \
  --out results/local/qelim-policy-shape-corpus-reps10.json
```

The cases include guarded choice, priority-table ladders, collateral-reason
selection, incident-memory update shapes, pointwise revision, independent table
shards, and DP-style guard constraints. They are still `qelim -e` commands, not
full `.tau` programs.

Receipt:

```text
auto route_counts:          { components: 20, dp: 10, monolithic: 50 }
default qelim total:        357.955140 ms
auto qelim total:            42.984396 ms
auto+KB guarded total:       46.882048 ms
auto speedup vs default:      8.327562 x
```

Interpretation:

- The auto BDD route survived on demo-shaped policy formulas.
- The route mix includes monolithic, component, and DP paths.
- This is stronger tutorial evidence than the generic non-pure corpus, because
  the formulas mirror the table-demo domain.
- KB rewriting still did not help here: `kb_steps_sum = 0`.

Boundary:

- This is not yet a full Tau-program benchmark.
- The next credibility step is to route actual `.tau` demo checks through the
  same qelim telemetry and measure whether the speedup survives inside the demo
  runner.

## Table-Demo Solver Telemetry Boundary

The representative table-demo checks were also run with qelim telemetry enabled:

```bash
python3 scripts/run_table_demo_qelim_telemetry.py \
  --out results/local/table-demo-qelim-telemetry.json
```

Receipt:

```text
case_count:             5
total_runs:            10
total_qelim_stat_count: 0
```

Interpretation:

- The checked public table demos returned `no solution` in both default and
  `TAU_QELIM_BACKEND=auto` modes.
- They did not emit `[qelim_cmd]` or `[qelim_bdd]` telemetry.
- Therefore the current table demos do not exercise the qelim command backend
  measured above.

Boundary:

- v571 is demo-shaped qelim-kernel evidence.
- v571 is not table-demo runtime acceleration evidence.
- To turn the qelim optimization into a visible demo acceleration, either add
  qelim-backed demo checks or separately instrument and optimize the `solve
  --tau` path.

## Table-Demo Solver Command Telemetry

The `solve --tau` path now has an opt-in command-body telemetry hook:

```text
TAU_SOLVE_STATS=1
```

The representative table checks can be measured with:

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --reps 3 \
  --out results/local/table-demo-solve-telemetry-reps3.json
```

Receipt:

```text
case_count:             5
total_runs:            15
solve telemetry:        passed
dominant phase counts: { apply_ms: 5 }
```

Interpretation:

- Each representative table-equivalence check reached `solve_cmd` and returned
  `no solution`.
- Inside the measured command body, `apply_rr_to_nso_rr_with_defs` dominates.
- The solver core is a small fraction of the measured command-body time on this
  corpus.
- The subprocess elapsed time is far larger than the command-body timing, so a
  second optimization surface is startup, parsing, source loading, and batching.

Boundary:

- This is solver-path observability, not an optimization yet.
- It explains why qelim wins did not automatically speed up the ordinary table
  demo path.
- The next candidate optimization is reducing repeated RR application and
  command loading in table-demo equivalence checks.

## Compound Table-Equivalence Check

The first successful overhead reduction does not change Tau's solver. It changes
the public demo obligation from many separate mismatch queries to one compound
mismatch query:

```text
diff_1 or ... or diff_n
```

The correctness law is:

```text
unsat(diff_1 or ... or diff_n)
implies
unsat(diff_i) for every i.
```

Run:

```bash
python3 scripts/run_table_demo_compound_check.py \
  --reps 1 \
  --out results/local/table-demo-compound-check.json
```

Receipt:

```text
checks:              15
individual elapsed:  118544.824 ms
compound elapsed:     53147.339 ms
elapsed reduction:       55.167%
```

Interpretation:

- All fifteen table-vs-raw mismatch formulas remain unsatisfiable.
- One compound query is faster than fifteen separate Tau processes on this
  corpus.
- This is a proof-obligation and harness optimization, not a qelim backend
  speedup and not a new table semantic feature.

Proof receipt: the Lean packet `tau_compound_table_check_2026_04_15` proves
the finite-list law behind this harness transformation. It does not prove
anything about Tau's solver internals.

## RR Subphase Telemetry

The `apply_ms` result was refined with:

```text
TAU_RR_STATS=1
```

Command:

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --rr-stats \
  --reps 1 \
  --out results/local/table-demo-rr-telemetry-reps1.json
```

Receipt:

```text
case_count:                       5
total_runs:                       5
get_rr dominant cases:            5
fixed-point-not-dominant cases:   5
minimum get_rr fraction:          0.727
maximum fixed-point fraction:     0.101
```

Interpretation:

- `get_nso_rr_with_defs` dominates the RR-with-definitions phase in every
  representative table check.
- `calculate_all_fixed_points` is not the dominant subphase inside
  `apply_rr_to_formula` on this corpus.
- The next optimization target is definition/RR extraction and type inference,
  not the fixed-point calculator.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- It does not yet identify which subroutine inside `get_nso_rr_with_defs`
  dominates.

## Type-Inference Frontier

The `get_nso_rr_with_defs` bucket was then split into:

```text
ensure_ms
type_arg_ms
setup_ms
extract_ms
defs_ms
infer_ms
result_ms
```

Receipt:

```text
case_count:                5
total_runs:                5
dominant phase counts:    { infer_ms: 5 }
branch counts:             { ref_value_rr: 5 }
minimum infer fraction:    > 0.9
```

Interpretation:

- The representative table checks all go through the `ref_value_rr` branch.
- `infer_ba_types` dominates `get_nso_rr_with_defs` in every checked case.
- Symbol-definition insertion and final RR extraction are not the first
  optimization targets.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- It does not yet explain which internal part of `infer_ba_types` dominates.

Next target:

- test whether repeated table equivalence checks can safely reuse stable type
  information,
- instrument `infer_ba_types` internally before trying a type-inference skip,
- look for repeated `build_spec` and definition-head work.

## Inference-Core Frontier

The `infer_ba_types` bucket was then split into outer and core telemetry.

Outer phases:

```text
global_scope_ms
function_symbols_ms
core_ms
```

Core phases:

```text
setup_ms
visit_ms
defaulting_ms
final_update_ms
remove_processed_ms
scope_ms
```

Receipt:

```text
case_count:                         5
total_runs:                         5
core inference calls per case:      17
aggregate outer core fraction:       0.959858
aggregate inner visit fraction:      0.604860
visit-dominant cases:                5
```

Interpretation:

- Every representative table check made 17 core inference calls.
- The outer type-inference cost is mostly the core pass, not global-scope or
  function-symbol setup.
- Inside the core pass, aggregate traversal time dominates the checked corpus.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- It does not yet identify which visitor cases dominate traversal cost.
- It does not prove that a type-inference cache or skip is
  semantics-preserving.

Next target:

- count `infer_ba_types` visitor cases by syntax node family,
- separate repeated inference invocation count from per-invocation traversal
  cost,
- test any cache with an explicit correctness key over tree identity and
  type-scope inputs.

## Inference Visitor-Shape Frontier

The core traversal was then split by visitor-shape counters:

```text
enter_bf
enter_bf_top
enter_bf_skipped
enter_rec_relation
enter_ref
enter_atomic
enter_default
enter_skipped
```

Receipt:

```text
case_count:                    5
total_runs:                    5
infer_visit rows per case:     17
aggregate entered nodes:       4196
aggregate enter_default:       1886
aggregate enter_bf:            1203
aggregate enter_atomic:         593
default-dominant cases:           5
aggregate skipped fraction:       0.111535
```

Interpretation:

- The largest counted family is not `bf`, `ref`, recurrence, or atomic formulas.
- It is the generic/default visitor branch.
- Non-top `bf` skipping is real, but it is not large enough to explain the
  full traversal cost.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- The `enter_default` bucket is still too broad to optimize directly.
- It does not prove that skipping or caching any visitor path is
  semantics-preserving.

Next target:

- split `enter_default` into concrete node families,
- measure whether repeated expanded subtrees explain the default branch,
- turn any cache hypothesis into a key-soundness proof or bounded oracle check
  before implementing it.

## Default Visitor Structural Frontier

The generic `enter_default` bucket was split again:

```text
enter_default_variable
enter_default_constant
enter_default_bf_logic
enter_default_bv_logic
enter_default_bf_quantifier
enter_default_wff_logic
enter_default_wff_temporal
enter_default_name_struct
enter_default_table_struct
enter_default_other
```

Receipt:

```text
case_count:                         5
total_runs:                         5
infer_visit rows per case:          17
aggregate enter_default:          1886
aggregate enter_default_name_struct: 882
aggregate enter_default_variable:    577
aggregate enter_default_bf_logic:    302
name-struct-dominant cases:            5
```

Interpretation:

- The largest default subfamily is structural/name-wrapper traversal.
- Boolean-function logic wrappers are present, but they are not dominant.
- The next optimization target is tree-shape, naming, or resolver-key work
  before Boolean-logic rewrites.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- The `name_struct` bucket is still combined.
- It does not prove that bypassing wrappers is semantics-preserving.

Next target:

- split `name_struct` into `sym`, `ref_args`, variable-name, offset, and type
  wrappers,
- measure repeated expanded subtree identity across the 17 inference calls,
- formalize a type-inference cache key before implementing a cache.

## Name-Wrapper Split

The combined `enter_default_name_struct` bucket was split into concrete
wrapper counters:

```text
enter_name_sym
enter_name_ref_args
enter_name_var
enter_name_io
enter_name_uconst
enter_name_offset
enter_name_typed
enter_name_fallback
enter_name_other
```

Receipt:

```text
case_count:                         5
total_runs:                         5
infer_visit rows per case:          17
aggregate enter_default_name_struct: 882
aggregate name-subcounter total:     882
aggregate enter_name_var:            577
aggregate enter_name_sym:            150
aggregate enter_name_ref_args:       150
aggregate enter_name_typed:            5
```

Interpretation:

- The name-wrapper split exactly accounts for the structural-name bucket.
- `var_name` is the dominant concrete wrapper family in this corpus.
- `sym` and `ref_args` appear as a paired secondary path.
- Type wrappers are present, but small in this bounded corpus.

Boundary:

- This is one repetition per case.
- It is telemetry, not a speedup.
- It does not prove that `var_name` bypassing, interning, or memoization is
  semantics-preserving.

Next target:

- instrument repeated `var_name` payload identity across the 17 inference
  calls,
- test a local `var_name` normalization or cache behind telemetry gates,
- measure wrapper-count reduction and wall-clock improvement separately.

## Variable-Name Repetition Split

The dominant `var_name` wrapper family was split into unique variable-name
payload IDs and repeated visits:

```text
enter_name_var
enter_name_var_unique
enter_name_var_repeated
```

Receipt:

```text
case_count:                    5
total_runs:                    5
infer_visit rows per case:     17
aggregate enter_name_var:      577
aggregate unique var_name IDs: 83
aggregate repeated var_name:   494
repeated fraction:             0.856153
repeat-dominant cases:         5
```

Interpretation:

- Most variable-name wrapper traversal repeats an already-seen payload.
- This turns the next optimization from a broad cache idea into a specific
  `var_name` cache-key problem.
- The safe cache key cannot be only the variable-name ID unless the relevant
  type-scope inputs are also fixed or included.

Boundary:

- This is still telemetry, not a cache.
- It does not prove speedup.
- It does not prove that any particular cache key preserves Tau semantics.

Next target:

- define the smallest sound `var_name` type-resolution cache key,
- test the cache behind a feature flag or telemetry flag,
- compare count reduction and wall-clock improvement separately.

## Opt-In Variable-Name Leaf Fast-Path

The first implementation candidate is not a cache. It is smaller: when
`TAU_INFER_FAST_VAR_NAME=1` is set, Tau skips leave-phase default
reconstruction for `var_name` leaf nodes.

Earlier v583 receipt:

```text
case_count:                         5
repetitions per mode:               3
baseline runs:                      15
fast-path runs:                     15
fast-path hits:                     1731
aggregate baseline apply time:      77.414433 ms
aggregate fast-path apply time:     75.910033 ms
apply-time delta:                  -1.943307%
aggregate baseline total time:      77.892033 ms
aggregate fast-path total time:     76.430732 ms
total-time delta:                  -1.876060%
```

Interpretation:

- The fast path has full coverage over observed `var_name` leaf visits.
- It preserves the checked table-demo solver results.
- The timing gain is small and mixed by case, so this is an opt-in experiment,
  not a default promotion.

Latest direct-wrapper smoke receipt:

```text
baseline solve total: 72.999700 ms
fast solve total:     73.525500 ms
solve delta:          -0.720%
baseline elapsed:     34866.789 ms
fast elapsed:         35152.460 ms
elapsed delta:        -0.819%
fast-path hits:       577
```

Interpretation:

- The latest run still preserved the checked table-demo solver results.
- It did not reproduce the earlier small timing win.
- The correct conclusion is weaker: the fast path is a measurable, opt-in
  experiment, not a promoted speedup.

Boundary:

- This is a small corpus.
- The result is about the table-demo `solve --tau` path, not the standalone
  qelim command.
- The optimization should not become default until a broader corpus and a
  code-level proof or review establish that `var_name` leaves have no
  leave-phase reconstruction obligation.

## Smooth Qelim-Backed Demo Wrapper

The public qelim-backed policy-shape demo can now be run with:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

The wrapper uses the same license-aware setup path as the table demos, applies
the local patch to the official Tau checkout, builds Tau, runs the policy-shaped
qelim corpus, and writes:

```text
results/local/qelim-table-demo-corpus.json
results/local/qelim-table-demo-summary.txt
```

Small-demo receipt:

```text
cases:                  8
repetitions:            3
semantic parity:         passed
auto route counts:       { components: 6, dp: 3, monolithic: 15 }
default qelim total:     105.065210 ms
auto qelim total:         13.314298 ms
auto speedup:              7.891157 x
```

This wrapper is the correct public demo for the qelim optimization. The ordinary
table demo wrapper remains the correct public demo for parser-level safe table
syntax and solver equivalence checks.

## Residual Semantic Validator

The first policy-shaped corpus used a syntactic/canonicalized output comparison.
That was intentionally conservative, but it rejected one useful nested case
where the BDD backend printed a semantically equivalent residual in a different
shape.

The semantic validation harness is:

```bash
python3 scripts/run_qelim_policy_semantic_corpus.py \
  --reps 3 \
  --out results/local/qelim-policy-semantic-corpus-reps3.json
```

It parses the printed residual formula subset and compares truth tables over
the residual atoms.

Receipt:

```text
case_count:                         9
semantic parity:                    passed
syntactic-fail semantic-pass count: 2
auto route counts:                  { components: 6, dp: 3, monolithic: 18 }
default qelim total:                118.946030 ms
auto qelim total:                    17.039850 ms
auto speedup:                         6.980462 x
```

Interpretation:

- The previously quarantined nested DP-child policy case is semantically valid
  under the residual truth-table checker.
- Syntactic parity alone is too strict for qelim backend regression tests.
- The validator is still narrow: it covers the printed residual subset used by
  this corpus, not arbitrary Tau formulas.
