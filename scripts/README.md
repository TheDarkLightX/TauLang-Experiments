# Scripts

## Smooth table demo

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

This is the recommended public reproduction path.
It clones the official Tau Language repository into `external/tau-lang`, checks
out the tested commit, applies the experiment patch, regenerates Tau's parser,
builds the Tau binary, and runs the table demos.

The script writes local proof reports under:

```text
results/local/
```

Do not commit machine-local proof reports unless they have been reviewed for
machine-specific paths.

## Separate steps

```bash
./scripts/setup_tau.sh --accept-tau-license
./scripts/apply_patches.sh
./scripts/run_table_demos.sh
```

`setup_tau.sh` requires explicit license acknowledgement because this repository
does not redistribute Tau Language source or binaries.

`apply_patches.sh` applies patch files under `patches/` to the official Tau
checkout. It skips patches that are already applied and regenerates the parser
when the grammar is patched.

`run_table_demos.sh` is intentionally scoped. It checks the feature-gated safe
table fragment, not full unrestricted TABA tables.

The current suite includes:

- finite-carrier helper checks,
- Tau-native table syntax lowering checks,
- protocol firewall priority checks,
- collateral admission reason-router checks,
- incident-memory state-transformer checks,
- pointwise revision locality and idempotence checks,
- feature-flag rejection checks.

If the scripts are not executable after checkout, run:

```bash
chmod +x scripts/*.sh
```

## Qelim-backed table policy demo

To run the public demo suite in one command:

```bash
./scripts/run_public_demos.sh --accept-tau-license
```

That script runs `run_table_demos.sh` first, then reuses the patched checkout
for the qelim-backed policy-shape demo. Set `RUN_PUBLIC_BENCHMARKS=1` to append
the broader research benchmark suite.

To run only the qelim-backed policy demo:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

This wrapper runs qelim commands whose formulas are shaped like the safe table
demos, then validates the printed residual formulas with the scoped semantic
checker. It is intentionally separate from `run_table_demos.sh`.

Scope:

- `run_table_demos.sh` checks the patched Tau table syntax and solver behavior.
- `run_qelim_table_demos.sh` checks the qelim backend on table-shaped formulas
  with residual semantic validation.
- The qelim demo is not evidence that the current `solve --tau` table checks are
  faster.

The wrapper writes:

```text
results/local/qelim-table-demo-corpus.json
results/local/qelim-table-demo-summary.txt
```

The wrapper now uses the residual-formula validation pass directly. To run it
without setup or patch application, use:

```bash
python3 scripts/run_qelim_policy_semantic_corpus.py \
  --reps 5 \
  --out results/local/qelim-policy-semantic-corpus-reps5.json
```

This parser is intentionally scoped to the residual formula subset printed by
the qelim policy corpus. The current receipt shows semantic parity across nine
policy-shaped cases and a roughly `5.15x` internal qelim speedup for the
experimental auto route against default qelim. It does not show a KB rewrite
benefit on that corpus, because the guarded KB pass had zero rewrite steps.

## Table-demo solver telemetry

The smooth table demo runner now defaults to the compound equivalence path:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

To run the older one-check-at-a-time audit path:

```bash
TABLE_DEMO_EQUIV_MODE=individual ./scripts/run_table_demos.sh --accept-tau-license
```

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --reps 3 \
  --out results/local/table-demo-solve-telemetry-reps3.json
```

This measures the `solve --tau` path used by the table demos. It requires a Tau
binary built from the local experiment patch, because the telemetry hook is
behind `TAU_SOLVE_STATS=1`.

Current local receipt:

```text
cases:                 5
repetitions:           3
solve telemetry:       passed
dominant solve phase:  apply_rr_to_nso_rr_with_defs
```

Interpretation:

- inside `solve_cmd`, RR application dominates the measured command body,
- the solver core itself is a small fraction of the command-body time,
- the much larger end-to-end process time is outside `solve_cmd`, so public demo
  speed work should look at startup, parsing, source loading, and command
  batching before changing qelim.

For a deeper RR subphase probe, run:

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --rr-stats \
  --reps 1 \
  --out results/local/table-demo-rr-telemetry-reps1.json
```

Current local receipt:

```text
cases:                         5
repetitions:                   1
get_rr dominant cases:         5
fixed-point-not-dominant cases: 5
```

Interpretation: the next Tau-side optimization target is inside
`get_nso_rr_with_defs`, not `calculate_all_fixed_points`.

With the deeper `rr_get_defs` line enabled, the same run also shows:

```text
dominant get_nso_rr_with_defs phase: infer_ms in all 5 cases
branch: ref_value_rr in all 5 cases
minimum infer fraction: > 0.9
```

Interpretation: for these table-demo solver checks, the next optimization
target is type inference, not symbol-definition insertion or RR formula
application.

With internal `infer_ba_types` telemetry enabled, the same corpus shows:

```text
dominant infer_outer phase:     core_ms in all 5 cases
infer_core rows per case:       17
dominant infer_core phase:      visit_ms in all 5 cases
aggregate visit_ms:             71.598981 ms
aggregate final_update_ms:      23.240025 ms
aggregate outer core fraction:   0.959858
aggregate inner visit fraction:  0.604860
```

Interpretation: the next optimization target is repeated core type-inference
traversal over the expanded solver term. This is still telemetry, not a
semantics-preserving cache proof.

## Compound table-equivalence check

```bash
python3 scripts/run_table_demo_compound_check.py \
  --reps 1 \
  --out results/local/table-demo-compound-check.json
```

This wrapper compares the public table-vs-raw equivalence checks against one
compound mismatch query. The law is:

```text
unsat(diff_1 or ... or diff_n)
implies
unsat(diff_i) for every i.
```

Current local receipt:

```text
checks:              15
individual elapsed:  118544.824 ms
compound elapsed:     53147.339 ms
elapsed reduction:       55.167%
```

The smooth table-demo runner now calls the same wrapper in `compound-only`
mode. Latest fresh run:

```text
equivalence mode: compound
compound checks:  15
compound elapsed: 54939.340 ms
result:           passed
```

Interpretation: the compound query preserves the same equivalence claim for
this corpus while reducing repeated process startup, parsing, source loading,
and repeated command setup. It is a harness and obligation-shaping
optimization, not a new table semantic feature.

The default benchmark script keeps this opt-in because it is slower than the
standalone micro-benchmarks:

```bash
RUN_TABLE_COMPOUND_CHECK=1 ./scripts/run_benchmarks.sh
```

With visitor-shape telemetry enabled, the same corpus shows:

```text
infer_visit rows per case:  17
aggregate entered nodes:    4196
aggregate enter_default:    1886
aggregate enter_bf:         1203
aggregate enter_atomic:      593
default-dominant cases:        5
skipped-enter fraction:        0.111535
```

Interpretation: the next target is the generic/default branch inside the
inference visitor. That bucket must be split again before it is safe to design a
rewrite, skip, or cache.

With the default visitor bucket split, the same corpus shows:

```text
aggregate enter_default:             1886
aggregate enter_default_name_struct:  882
aggregate enter_default_variable:     577
aggregate enter_default_bf_logic:     302
name-struct-dominant cases:             5
```

Interpretation: the immediate target is structural/name-wrapper traversal
inside type inference, not Boolean logic traversal itself. This is still
telemetry, not a proof that wrapper bypassing or caching is safe.

## Restricted Tau rewrite normalizer

The c111 proof lane has an executable companion:

```bash
python3 scripts/tau_kb_normalizer.py normalize \
  'pointCompl(common(a, pointJoin(a, b)))' \
  --json
```

The script implements the seven checked rewrite rules from the restricted
Knuth-Bendix-style Tau expression system. It is intentionally narrow:

- it checks semantic parity over Boolean valuations,
- it checks that the c111 measure decreases at every emitted step,
- it does not orient commutativity, associativity, or distributivity,
- it is not a complete Boolean-algebra equivalence checker.

The benchmark wrapper records a deterministic corpus receipt:

```bash
./scripts/run_benchmarks.sh
```

That writes:

```text
results/local/kb-normalizer-benchmark.json
results/local/incremental-execution-demo.json
results/local/bitvector-modular-demo.json
results/local/bitvector-constant-folding-demo.json
results/local/var-name-cache-key-demo.json
results/local/equality-path-simplification-demo.json
```

If a patched Tau binary is available, the same wrapper also runs:

```bash
python3 scripts/run_qelim_kb_probe.py
```

That writes `results/local/qelim-kb-probe.json` and compares the BDD qelim
backend with and without the opt-in `TAU_QELIM_BDD_KB_REWRITE=1` pass. The
generated matrix also tests `TAU_QELIM_BDD_KB_REWRITE=guarded`, which runs the
rewrite pass only when a cheap scan detects an absorption opportunity.

For the larger generated matrix, run:

```bash
RUN_QELIM_KB_MATRIX=1 ./scripts/run_benchmarks.sh
```

or directly:

```bash
python3 scripts/run_qelim_kb_matrix.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/qelim-kb-matrix.json
```

The matrix compares `bdd`, `bdd+kb`, `bdd+kb_guarded`, `bdd+ac`,
`bdd+ac+kb`, and `bdd+ac+kb_guarded`.
It is intentionally opt-in because it runs many Tau subprocesses.

To test whether guarded KB helps the already-promoted `auto` qelim route, run:

```bash
python3 scripts/run_qelim_auto_kb_matrix.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/qelim-auto-kb-matrix.json
```

That matrix compares `default`, `auto`, `auto+kb_guarded`, and
`auto+kb_forced`. Exact output parity is checked against the unmodified `auto`
route. Exact default parity is recorded separately because default and `auto`
may print semantically equivalent residual formulas in different syntactic
forms.

## Incremental execution future-work demo

```bash
python3 scripts/run_incremental_execution_demo.py \
  --out results/local/incremental-execution-demo.json
```

This prototype does not call Tau. It models a Tau-like Boolean-algebra
expression language over the four-cell carrier and checks the future-work
contract suggested by the read-set, partial-evaluation, and derivative proof
lanes:

```text
if a changed key is outside a sub-expression's read set, reuse the cached value
```

Current local receipt:

```text
cases:                         6
full unique residual nodes:    193
incrementally recomputed:       31
runtime-delta recomputed:       31
aggregate recompute saving: 83.938%
runtime-delta saving:       83.938%
runtime dependency checks:   passed
runtime delta checks:        passed
all equality checks:         passed
```

Boundary: this is an executable design prototype for incremental Tau execution.
It is not a Tau runtime patch and not a whole-language speed theorem.

Proof status: the matching Lean packet closes the scoped semantic kernel for
read membership, partial evaluation, incremental cache invalidation, and
unread-key cache reuse. The proof is a runtime-design receipt, not a proof of
all Tau features.

Runtime-cache shape: the demo now builds child-before-parent node IDs, stores a
value table, selects dirty node IDs from the dependency index, recomputes only
those IDs in one forward pass, and checks the result against full reevaluation.

The native Tau runtime now also has a measurement hook and one opt-in rebuild
skip:

```bash
python3 scripts/run_tau_runtime_stats_demo.py \
  --out results/local/tau-runtime-stats-demo.json
```

The hook is enabled by:

```bash
TAU_RUN_STATS=1
```

The opt-in rebuild skip is:

```bash
TAU_SKIP_UNCHANGED_IO_REBUILD=1
```

Current local receipt:

```text
step count:              3
accepted update count:   3
total paths attempted:   6
total paths solved:      6
total revisions tried:   1
total added spec parts:  2
input rebuilds skipped:  3
output rebuilds skipped: 1
output parity:           passed
final memory size:       9
```

Boundary: this is a native IO-rebuild optimization, not an incremental
expression-cache optimization. Rebuild skipping is also stream-class gated:
file streams do not skip, because rebuilding them reopens the file.

For the slower stream-class regression, run:

```bash
python3 scripts/run_tau_io_rebuild_regression.py \
  --out results/local/tau-io-rebuild-regression.json
```

Current local receipt:

```text
vector input rebuilds skipped:  3
vector output rebuilds skipped: 1
file input rebuilds skipped:    0
file output rebuilds skipped:   0
vector output parity:           passed
file output parity:             passed
```

The full benchmark wrapper only runs this slower C++ harness when requested:

```bash
RUN_TAU_IO_REBUILD_REGRESSION=1 bash scripts/run_benchmarks.sh
```

## Tau derivative and finite-equivalence demo

```bash
python3 scripts/run_tau_derivative_equivalence_demo.py \
  --out results/local/tau-derivative-equivalence-demo.json
```

This standalone corpus is the executable companion to the c120 through c122
proof lane. It checks:

```text
eval(derivative(k,v,e)) = update(eval(e), k, evalConst(e,v))
```

and finite-carrier equivalence by comparing denotation tables.

Current local receipt:

```text
cases:                         80
derivative sound cases:        80
size-preserved cases:          80
equivalence classifications:   80
equivalent cases:              61
non-equivalent cases:          19
```

Boundary: this is a Tau-like kernel demo. It is not Tau parser support, not a
runtime delta engine, and not arbitrary infinite-carrier equivalence.

## Fixed-width modular arithmetic future-work demo

```bash
python3 scripts/run_bitvector_modular_demo.py \
  --max-width 6 \
  --out results/local/bitvector-modular-demo.json
```

This exhaustively checks small fixed widths, records modular rewrite laws that
survive overflow, and records counterexamples for tempting integer rewrites
that fail under modulo `2^w` semantics.

Acceptance is asymmetric: safe laws must pass at every tested width, while an
unsafe law only needs one counterexample in the tested range.

## Fixed-width bitvector constant-folding demo

```bash
python3 scripts/run_bitvector_constant_folding_demo.py \
  --width 4 \
  --count 80 \
  --out results/local/bitvector-constant-folding-demo.json
```

This checks a random generated corpus under all width-4 environments for three
variables. The Lean packets prove pure constant folding and the identity
rewrites for the small expression kernel. The executable corpus checks that the
implemented simplifier matches those laws on generated examples.

Current local receipt:

```text
original nodes:              1540
constant-folded nodes:       1366
identity-simplified nodes:    626
constant-fold reduction:   11.299%
identity reduction:        59.351%
all semantic checks:        passed
```

To test the epiplexity-style routing hypothesis, run:

```bash
python3 scripts/run_qelim_epiplexity_router.py \
  --max-generated-cases 34 \
  --reps 10 \
  --out results/local/qelim-epiplexity-router.json
```

This experiment checks whether a cheap source-structure metric predicts when
the guarded KB pass has work to do. It records semantic parity, detector
confusion matrices, and route regret against the locally fastest mode. The
write-up is `docs/qelim-epiplexity-routing.md`.

For the table-demo solver telemetry lane, the latest split records concrete
name-wrapper counters inside type inference. Run:

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --rr-stats \
  --reps 1 \
  --out results/local/table-demo-infer-name-telemetry-reps1.json
```

The corresponding Formal Philosophy cycle is v581. It identifies `var_name`
wrappers as the dominant structural-name target, but it is still telemetry, not
a semantics-preserving optimization.

The next cycle, v582, adds repeated-payload counters:

```text
enter_name_var_unique
enter_name_var_repeated
```

On the current five-case table-demo corpus, `577` variable-name visits collapse
to `83` unique variable-name IDs, leaving `494` repeated visits. This is the
first concrete cache-shaped target. It still needs a cache-key proof before it
can be treated as a safe optimization.

The first implemented candidate is smaller than a cache. It skips leave-phase
default reconstruction for `var_name` leaf nodes when:

```bash
TAU_INFER_FAST_VAR_NAME=1
```

Run the direct comparison wrapper with:

```bash
python3 scripts/run_infer_fast_var_name_demo.py \
  --reps 1 \
  --out results/local/infer-fast-var-name-demo-reps1.json
```

The latest one-repetition smoke receipt preserved the checked solver results
and hit the fast path `577` times, but did not improve timing on that run:
solve total was about `0.72%` worse and end-to-end elapsed time was about
`0.819%` worse. This stays an opt-in telemetry experiment, not a promoted
optimization.

## Scoped var-name cache-key demo

```bash
python3 scripts/run_var_name_cache_key_demo.py \
  --out results/local/var-name-cache-key-demo.json
```

This standalone model tests the next cache-key question after the failed
fast-path promotion. It compares baseline resolution, `(scope,name)` caching,
and name-only caching.

Current local receipt:

```text
baseline resolves:            25
scoped-cache resolves:        11
scoped-cache reduction:    56.0%
name-only cache:             refuted by shadowing counterexamples
```

Boundary: this is a cache-key model, not Tau's full scoped union-find resolver.

## Equality-aware path simplification demo

```bash
python3 scripts/run_equality_path_simplification_demo.py \
  --out results/local/equality-path-simplification-demo.json
```

This standalone model targets Tau's known issue that path simplification does
not use equalities between variables.

Current local receipt:

```text
cases:             3
original nodes:    29
optimized nodes:   10
node reduction: 65.517%
semantic checks: passed
```

Boundary: representative substitution is safe only under path equalities. The
demo records counterexamples showing that the rewrite is unsound outside those
assumptions.

To probe the current Tau normalizer recombination boundary directly, run:

```bash
python3 scripts/run_equality_split_tau_probe.py \
  --out results/local/equality-split-tau-probe.json
```

Current local receipt:

```text
cases:                         4
useful reduction cases:        4
matched target cases:          0
Tau-normalized characters:   152
target-normalized characters: 36
character reduction:      76.316%
equivalence checks:       passed
```

Boundary: this Tau-facing probe checks branch recombination after an equality
split. It proves candidate shorter targets equivalent using `solve --tau`, but
without the feature flag it does not make Tau's normalizer emit those targets
automatically.

To test the current scoped C++ pass:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --out results/local/equality-split-tau-probe-enabled.json
```

Current enabled receipt:

```text
cases:                         4
matched target cases:          3
target-sized cases:            4
Tau-normalized characters:    36
target-normalized characters: 36
MNF-matched target cases:      4
```

Boundary: the feature-gated pass closes this four-case size-reduction corpus,
but remains opt-in and narrow. One case still differs textually because Tau can
print equivalent Boolean terms in different orders.

For a wider alias-order smoke test:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --extended \
  --out results/local/equality-split-tau-probe-extended-enabled.json
```

Current extended receipt:

```text
cases:                         8
matched target cases:          3
target-sized cases:            8
Tau-normalized characters:   108
target-normalized characters: 108
MNF-matched target cases:      8
```

The standard benchmark script now regenerates both the baseline probe and this
enabled extended probe when a patched Tau binary is available:

```bash
./scripts/run_benchmarks.sh
```

The five extended cases that do not match the target text under `normalize`
still match under `mnf`. The feature-gated pass has closed the size-reduction
obligation on this corpus; the remaining issue is presentation canonicalization.

For a generated path-sensitive corpus:

```bash
python3 scripts/run_equality_split_tau_probe.py \
  --generated-path-corpus \
  --max-generated-cases 48 \
  --out results/local/equality-split-generated-path.json

TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --generated-path-corpus \
  --max-generated-cases 48 \
  --out results/local/equality-split-generated-path-enabled.json
```

Current generated-path receipt:

```text
baseline target-sized cases:   2 / 48
enabled target-sized cases:   48 / 48
baseline normalize chars:    2088
enabled normalize chars:     378
target normalize chars:      378
MNF-matched target cases:     48 / 48
```

This generated corpus is intentionally harder than the smoke test. It includes
cases where the residual is simplified differently under the equality branch
and its complement. The current feature flag now closes the generated corpus on
normalized size. Exact `normalize` text still matches only `24` of `48` cases,
because Tau prints some equivalent Boolean-algebra terms in different orders.
The remaining target is presentation canonicalization, not missed semantic
recombination on this corpus.

For a four-variable equality-chain stress corpus:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --stress-path-corpus \
  --out results/local/equality-split-stress-enabled.json
```

Current stress receipt:

```text
enabled target-sized cases:  105 / 105
enabled normalize chars:     847
target normalize chars:      847
MNF-matched target cases:    105 / 105
exact normalize matches:      84 / 105
```

The stress corpus adds cases where an equality-chain branch simplifies the
residual to another atom, or all the way to true. The current feature flag
closes those cases on normalized size. Exact textual presentation remains a
separate canonicalization problem.

For a five-variable wide corpus:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --wide-path-corpus \
  --out results/local/equality-split-wide-enabled.json
```

Current wide receipt:

```text
enabled target-sized cases:  200 / 200
enabled normalize chars:    1980
target normalize chars:     1980
MNF-matched target cases:    200 / 200
exact normalize matches:     130 / 200
```

Whole-command timing from the same 200-case corpus:

```text
baseline normalize time:     19958.521 ms
enabled normalize time:      19432.444 ms
baseline MNF time:           16847.849 ms
enabled MNF time:            16813.717 ms
```

These timings include Tau process startup for each command. They are a
regression screen, not an in-process microbenchmark. The wide corpus did not
expose a new size-failure class or a whole-command timing regression. The
remaining gap at that stage was textual presentation canonicalization.

To screen whether `normalize` has already reached a fixed point:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --wide-path-corpus \
  --check-idempotence \
  --out results/local/equality-split-wide-enabled-idempotence.json
```

Current idempotence receipt:

```text
baseline first-pass idempotent cases: 7 / 200
enabled first-pass idempotent cases:  140 / 200
enabled non-idempotent cases:         60 / 200
enabled second-pass growth cases:     30 / 200
guarded-presentation target-sized:    200 / 200
guarded-presentation exact matches:   160 / 200
guarded-presentation characters:      1980
guarded-MNF non-growing cases:        200 / 200
guarded-MNF shrinking cases:          40 / 200
guarded-MNF characters:               1480
```

With the native guarded-MNF mode enabled and the corrected one-character
parser mode for compact pretty-output replay:

```text
exact normalize-text matches:         200 / 200
target-sized cases:                   200 / 200
normalized characters:                1480
first-pass idempotent cases:          200 / 200
second-pass growth cases:             0 / 200
same-size second-pass changes:        0 / 200
whole-command normalize time:         18893.125 ms
```

The corrected idempotence screen uses Tau's one-character-variable parser mode
for compact pretty-output replay. That matters because Tau prints meets by
adjacency, so `wx` must be read as `w & x`, not as one multi-character
variable. With that parser mode, the native guarded-MNF pass is stable on the
full wide corpus.

The same probe now measures guarded DNF/MNF presentation candidates. Guarded
`mnf` is the stronger candidate and is now implemented as an experimental
Tau patch behind `TAU_NORMALIZE_GUARDED_MNF=1`. It is not a default Tau mode,
and the timing is a process-level regression screen rather than an in-process
optimizer benchmark.

The attempted print-and-reparse stabilizer is negative evidence. It did not
improve the corpus and increased whole-command time, so it is not part of the
patch.

## Variable-update cache telemetry

```bash
python3 scripts/run_infer_variable_update_cache_demo.py \
  --reps 1 \
  --out results/local/infer-variable-update-cache-demo-reps1.json
```

This wrapper compares baseline Tau type inference against the feature-gated
local variable-update cache:

```bash
TAU_INFER_VARIABLE_UPDATE_CACHE=1
```

Current local receipt:

```text
output parity:      passed
cache queries:      2635
cache hits:          432
hit rate:          16.3947%
solve-time delta:  -5.599%
```

Interpretation: the cache is conservative enough to preserve the checked
outputs, but too narrow to improve this corpus. It is negative optimization
evidence, not a promoted speedup.
