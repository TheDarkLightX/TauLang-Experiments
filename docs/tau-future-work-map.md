# Tau Future-Work Experiment Map

This page maps the public Tau future-work themes to the community experiments in
this repository. It is a research status page, not an upstream roadmap.

## Scope Rule

Each row separates three claims:

- what the official future-work theme asks for,
- what this repository currently demonstrates,
- what remains before it would count as a Tau Language feature.

The experiments are intentionally feature-gated or standalone. They should be
read as proof-guided prototypes, not as claims about official IDNI plans.

## Current Map

| Future-work theme | Current experiment | Evidence now available | Missing before upstream-style feature |
| --- | --- | --- | --- |
| Fixed-width modular arithmetic | `run_bitvector_modular_demo.py` and the bitvector Lean packets | Exhaustive small-width rewrite triage, Lean-proved safe modular laws, Aristotle-audited identity rewrites, and a proof-backed constant-folder for a small expression kernel | Parser/runtime bitvector syntax, solver integration, broader rewrite basis, and large-corpus benchmarks |
| Boolean-function storage and manipulation | Safe tables, pointwise revision, finite CBF lowering, and symbolic helper forms | Tau patch demos for feature-gated tables, Lean proof artifacts for finite and safe-recursive kernels | Official table syntax, chosen runtime carrier, full lowering, and unrestricted TABA coverage if that is intended |
| Normalization and satisfiability performance | Restricted rewrite normalizer, qelim backend routing, table-demo solver telemetry, compound table-equivalence checks, equality-aware path simplification, incremental execution prototype, derivative-style perturbation analysis, and scoped var-name cache-key model | Confluent seven-rule normalizer proof, qelim parity checks, internal telemetry, compound-query demo speedup, equality-substitution proof, read-set soundness, derivative soundness, proof-backed incremental-cache kernel, partial-evaluation soundness, and scoped cache-key counterexample discipline | Integration into Tau's typed IR, default-on profit selector, equality-aware path pass in Tau's normalizer, read-set storage for real nodes, derivative or delta runtime support, cache-key proof for real nodes, and full runtime benchmarks |
| Redefinitions of functions or predicates | Guarded pointwise revision as a safe redefinition model | Aristotle-checked guarded revision laws, compatibility-needed counterexample, and satisfiability-preservation theorem under compatibility | Tau syntax for redefinition, compatibility checker, diagnostic output, and rollback behavior |
| Arbitrary stream names | Stream-key rename semantic kernel | Lean proof that renaming preserves denotation when the renamed environment agrees with the original | Parser/runtime support, canonical naming policy, collision handling, and source-map diagnostics |
| Boolean-function normalization performance | KB normalizer, BDD/qelim probes, and future BDD carrier candidates | Proof-backed normalizer for a restricted expression fragment and generated-corpus node reductions | General Boolean-function normal form, BDD or AIG carrier choice, equivalence/minimization strategy, and Tau integration |

## Most Mature Lanes

The strongest lanes are the ones with all three pieces: a theorem, an executable
prototype, and a benchmark or corpus receipt.

```text
proof artifact + executable corpus + scoped boundary
```

Those lanes are:

- restricted rewrite normalization,
- table-shaped qelim policy corpus,
- compound table-equivalence checking,
- equality-aware path simplification,
- incremental execution over the Tau-like helper IR,
- derivative-style single-key perturbation analysis,
- fixed-width bitvector constant folding for the small kernel.

The `TAU_INFER_FAST_VAR_NAME=1` type-inference shortcut is not in this mature
set. It preserves the checked table-demo solver results on the local corpus, but
the latest direct wrapper did not show a stable speedup.

The follow-up cache-key model is documented in `docs/var-name-cache-key.md`.
It proves and tests the narrower lesson: name-only caching is unsafe under
shadowing, while `(scope,name)` caching is sound in the small resolver model
when cache hits agree with the resolver.

The implementation-shaped cache plan is `docs/type-inference-cache-plan.md`.
It moves the target from raw `var_name` leaves to typed variable/update
resolution with a conservative resolver epoch.

The first Tau-side variable-update cache attempt is documented in
`docs/infer-variable-update-cache.md`. It preserved output parity but was slower
on the current safe-table solver corpus, so it is negative optimization
evidence, not a promoted speedup.

The compound table-equivalence check is documented in
`docs/demo-gallery.md`. The compound mode uses this law:

```text
unsat(diff_1 or ... or diff_n)
implies
unsat(diff_i) for every i.
```

Current receipt:

```text
checks:              15
individual elapsed:  118544.824 ms
compound elapsed:     53147.339 ms
elapsed reduction:       55.167%
```

This is the first successful table-demo overhead reduction. It changes the
shape of the proof obligation and harness, not Tau's table semantics.

The audit-friendly batching mode keeps the obligations separate but runs them
inside one Tau CLI input using the prefix-dot command shape:

```text
cmd_1 . cmd_2 . ... . cmd_n
```

Current receipt:

```text
checks:                15
individual processes:  15
batched processes:      1
individual elapsed:  117482.283 ms
batched elapsed:      58561.321 ms
elapsed reduction:       50.153%
```

This is the second table-demo overhead reduction. It is weaker than the
compound logical law as a proof compression, but stronger as an audit trail
because Tau still returns one `no solution` result for each obligation.

The equality-aware path simplification experiment is documented in
`docs/equality-aware-path-simplification.md`. It targets a known Tau README
issue: path simplification currently does not use equalities between variables.

Core law:

```text
env(rep(x)) = env(x) for every x
implies
eval(env, subst(rep, e)) = eval(env, e)
```

Current receipt:

```text
cases:             3
original nodes:    29
optimized nodes:   10
node reduction: 65.517%
semantic checks: passed
```

Related Tau branch-recombination probe receipt:

```text
cases:                         4
useful reduction cases:        4
matched target cases:          0
Tau-normalized characters:   152
target-normalized characters: 36
character reduction:      76.316%
equivalence checks:       passed
```

Feature-gated C++ pass receipt with `TAU_EQUALITY_SPLIT_RECOMBINE=1`:

```text
cases:                         4
matched target cases:          3
target-sized cases:            4
Tau-normalized characters:    36
target-normalized characters: 36
MNF-matched target cases:      4
```

The Lean packet proves the substitution law and the no-premise counterexample.
The related Tau-facing probe shows that, after equality-split branches are
formed, the current Tau binary can prove shorter recombined targets equivalent,
but does not yet normalize all of them without the feature flag. The
feature-gated C++ pass reduces all four checked cases to target-sized forms.
Three match the target text exactly under `normalize`; the remaining case
matches under `mnf`, so the gap is presentation-level canonical ordering rather
than semantic failure. The scoped recombination patch is now implemented behind
`TAU_EQUALITY_SPLIT_RECOMBINE=1`. The remaining normalizer candidates are the
broader path-scoped equality simplifier and a final presentation-canonicalization
step.

The extended alias-order smoke test strengthens the evidence:

```text
cases:                         8
matched target cases:          3
target-sized cases:            8
Tau-normalized characters:   108
target-normalized characters: 108
MNF-matched target cases:      8
```

The remaining mismatch class is presentation-level canonical ordering of
equivalent Boolean terms, not a missed reduction on the checked corpus.

The generated path-sensitive corpus moves the frontier again:

```text
baseline target-sized cases:   2 / 48
enabled target-sized cases:   48 / 48
baseline normalize chars:    2088
enabled normalize chars:     378
target normalize chars:      378
MNF-matched target cases:     48 / 48
```

This shows that the scoped recombination pass now closes the generated
path-sensitive corpus on normalized size. Exact `normalize` text still matches
only `24` of `48` generated cases, because Tau can print equivalent
Boolean-algebra terms in different orders.

The four-variable equality-chain stress corpus adds cases where the equality
branch simplifies the residual to a different atom, or all the way to true:

```text
enabled target-sized cases:  105 / 105
enabled normalize chars:     847
target normalize chars:      847
MNF-matched target cases:    105 / 105
exact normalize matches:      84 / 105
```

The five-variable wide corpus extends this again:

```text
enabled target-sized cases:  200 / 200
enabled normalize chars:    1980
target normalize chars:     1980
MNF-matched target cases:    200 / 200
exact normalize matches:     130 / 200
baseline normalize time:     19958.521 ms
enabled normalize time:      19432.444 ms
baseline MNF time:           16847.849 ms
enabled MNF time:            16813.717 ms
```

This stress corpus forced two additional graph checks: a failed-guard
disjunction may complement an alias component by connecting all terms in that
component, and an alias-only branch may be recombined when the aliases entail
the residual. The wide corpus has not exposed a new size-failure class. The
timing fields are whole-command timings with Tau process startup included, not
in-process microbenchmarks. The next proof and implementation target is still
fixed-point presentation canonicalization:

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

Native opt-in guarded-MNF receipt with
`TAU_NORMALIZE_GUARDED_MNF=1`:

```text
exact normalize-text matches:         200 / 200
target-sized cases:                   200 / 200
normalized characters:                1480
first-pass idempotent cases:          200 / 200
second-pass growth cases:             0 / 200
same-size second-pass changes:        0 / 200
whole-command normalize time:         18893.125 ms
```

The corrected idempotence screen reparses compact pretty output in Tau's
one-character-variable mode. That matters because Tau prints meets by
adjacency, so `wx` must be read back as `w & x`, not as one multi-character
variable. With that parser mode, the native guarded-MNF pass is fixed-point
stable on the wide corpus. A direct AST-level second-normalize hook was tested
and did not improve the corpus, so the useful implementation path is guarded
presentation selection, not another call to `normalize` on the same tree.

Guarded `mnf` is the current strongest presentation candidate. It preserves
the size boundary on all wide-corpus cases and shrinks `40 / 200` cases, but it
is now implemented only as an experimental opt-in mode behind
`TAU_NORMALIZE_GUARDED_MNF=1`, not as a default replacement for `normalize`.
The timing receipt is a process-level regression screen rather than an
in-process speedup proof.

The attempted follow-up `print -> reparse -> MNF` stabilization did not improve
the corpus and increased whole-command time. This removes the reparse shortcut
from the candidate list.

The final size failures were closed by equality-graph implication checks:
alias branches that imply the residual can be recombined when the residual plus
the failed guard-disjunction reconstructs the alias branch. A separate
conjunction cleanup removes redundant path-failure disjunctions when an
endpoint inequality already implies that one edge on the equality path must
fail. The stress corpus adds the alias-component complement and
alias-entails-residual cases.

```text
branch premise G entails x = rep(x)
implies substitute_rep(term) is equivalent to term on that branch
```

That law is the bridge from the standalone equality-path simplification model
to a Tau-native normalizer pass.

The newest proof lane adds a structural execution model for Tau-shaped
expressions. The audited packets are:

```text
c117 optimization-lifting coherence
c118 reads/effect analysis
c119 incremental evaluation bound
c120 Tau-Brzozowski derivative
c121 extended bisimulation completeness
c122 complete equivalence check by evaluation wrapping
c123 partial evaluation
c124 table Reader-monad laws
```

The key operational split is:

```text
qelim routing decides how to eliminate quantifiers
effect analysis decides what must run again
derivatives describe one-key perturbations
partial evaluation removes known inputs
finite-carrier equivalence decides restricted expression equality
```

Boundary: these packets are proof kernels over Tau-like expression languages.
They are not yet a Tau C++ runtime patch. c121's strongest theorem is algebraic:
the extended relation is complete once semantic equality is available. It gives
an executable decision procedure on finite carriers, where table equality is
decidable. It does not make arbitrary infinite-carrier equivalence automatically
decidable.

The executable companion is documented in
`docs/tau-derivative-and-finite-equivalence.md`. Current receipt:

```text
cases:                         80
derivative sound cases:        80
size-preserved cases:          80
equivalence classifications:   80
equivalent cases:              61
non-equivalent cases:          19
result:                        passed
```

## Incremental Execution Contract

The runtime-shaped law is:

```text
k notin Reads(e)
and env and env' agree on Reads(e)
implies eval(env,e) = eval(env',e).
```

Standard reading: if the changed key is not read by expression `e`, and the old
and new environments agree on every key that `e` does read, then the denotation
of `e` is unchanged.

Implementation reading: a runtime cache may reuse a node when its read set does
not contain the changed key. If the read set is unavailable, the safe fallback
is full reevaluation.

The derivative-shaped law is:

```text
eval(derivative(k,v,e)) = update(eval(e), k, evalConst(e,v)).
```

Standard reading: the derivative expression has the same denotation as the
original expression table updated at key `k` by the constant-leaf evaluation of
`e` at value `v`.

Implementation reading: a future runtime can treat a single-key input change as
a symbolic delta, then propagate only the affected expression parts.

The current incremental runtime-cache prototype now checks the concrete cache
shape as well:

```text
full unique residual nodes:    193
runtime-delta recomputed:       31
runtime-delta saving:       83.938%
runtime delta checks:        passed
```

Boundary: the cache shape is still a standalone Tau-like kernel. It is not
plugged into Tau's C++ runtime.

The first native Tau runtime hook measures the existing interpreter:

```bash
TAU_RUN_STATS=1
```

The first opt-in native runtime optimization skips IO stream rebuilds when an
accepted update does not change the IO stream set and the active stream class
declares unchanged rebuild skipping safe:

```bash
TAU_SKIP_UNCHANGED_IO_REBUILD=1
```

Current local receipt on the update-stream pointwise-revision smoke case:

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

Additional stream-class regression receipt:

```text
vector input rebuilds skipped:  3
vector output rebuilds skipped: 1
file input rebuilds skipped:    0
file output rebuilds skipped:   0
vector output parity:           passed
file output parity:             passed
```

Boundary: this is a feature-gated IO-rebuild optimization. It does not
implement incremental delta evaluation or skip solver work. The file-stream
zero-skip result is intentional, because rebuilding file streams changes their
state by reopening files.

## Bitvector Contract

The fixed-width model is:

```text
bv_w(x) = x mod 2^w.
```

All arithmetic rewrite claims must be interpreted under that model. An identity
that is valid over unbounded integers may be invalid after overflow is made
observable.

The checked simplifier law for the small expression kernel is:

```text
eval_w(simplify_w(e)) = eval_w(e).
```

Standard reading: simplifying a fixed-width expression preserves its value under
every environment.

Implementation reading: constant folding and the proved identity rules may be
used before evaluation for this small kernel.

Current proof status: the `foldAdd` and `foldMul` identity-rewrite theorems were
closed by Aristotle project `dc1acd60-175d-45a3-be53-dd037b6d94f2`, rebuilt
locally, and scanned clean in the returned Lean file. This strengthens the
bitvector optimization lane, but it is still a small-kernel result rather than
Tau parser or solver support.

## Safe Redefinition Contract

The guarded redefinition model is:

```text
revise(g, old, new) = (g and new) or ((not g) and old).
```

Standard reading: inside the guard, use the new definition; outside the guard,
keep the old definition.

The satisfiability-preservation claim needs a compatibility premise:

```text
Compatible(g, old, new)
and Sat(old)
implies Sat(revise(g, old, new)).
```

Standard reading: if every old satisfying witness that lands inside the guard
also satisfies the new definition, then revising the old definition by the new
one preserves satisfiability.

Boundary: without compatibility, Aristotle produced the expected counterexample:
old is true, new is false, and the guard is true.

## Stream Rename Contract

Let `rename_f(e)` replace each stream key `k` by `f(k)`.

```text
env'(f(k)) = env(k) for every key k
implies
eval(env', rename_f(e)) = eval(env, e).
```

Standard reading: renaming stream keys preserves denotation when the renamed
environment maps each renamed key to the old value of the original key.

Boundary: this is a semantic invariant, not parser support.

## Next Build Target

The next highest-value Tau-native targets are now:

- presentation canonicalization for equality-split recombination,
- runtime-shaped incremental evaluation.

The equality feature flag should stay scoped until the presentation
canonicalization gap is closed and larger generated corpora are checked. The
incremental feature flag would be:

```text
TAU_INCREMENTAL_EVAL=1
```

The patch should attach stable node IDs and read sets to typed IR nodes, reuse
cached node values after single-key updates, and fall back to full reevaluation
whenever the analysis is incomplete. The current standalone prototype already
emits the dependency-index shape that such a patch needs.
