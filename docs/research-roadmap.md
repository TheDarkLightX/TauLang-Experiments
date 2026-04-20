# Research Roadmap

## 1. Finite Tables

Goal: make finite tables an executable semantic kernel.

Core artifacts:

- table `set`, `select`, and `common` semantics
- pointwise Boolean operations
- finite-clopen or BDD-backed carriers
- deterministic examples and traces
- correctness statements in Lean

## 2. Infinite Table Reference Semantics

Goal: separate executable finite approximants from completed reference semantics.

Core artifacts:

- finite clopen embedding into completed stream-predicate semantics
- countable union support for reference semantics
- Kleene least-fixed-point semantics for safe recurrence
- finite-stabilization theorem connecting finite execution to completed semantics
- negative boundary theorems for unsafe same-stratum complement

## 3. Quantifier-Elimination Dispatch

Goal: choose the QE backend based on fragment shape.

Candidate lanes:

- current Tau antiprenex pipeline
- BDD existential abstraction
- finite-mask QE
- splitter-based QE
- Skolem split-witness QE
- syntax-directed simplification before semantic compilation

Working principle:

```text
qelim algorithm choice should be fragment-sensitive, because the fastest method depends on where the structure lives: in syntax, or in the compiled carrier.
```

## 4. Proof-Carrying Optimization

Goal: every optimization should emit semantic evidence.

Evidence classes:

- same denotation
- same satisfying assignments
- same finite approximants
- same least fixed point under monotonicity and omega-continuity assumptions
- counterexample witness when a rewrite is invalid

## 5. Tau Runtime Bridge

Goal: keep runtime experiments behind feature flags and patches.

The repo should demonstrate behavior without redistributing Tau itself.

## 6. Neuro-Symbolic Boolean Algebras

Goal: make the symbolic side of a neuro-symbolic loop exact, replayable, and
small enough to audit.

Current artifact:

```bash
./scripts/run_qns_semantic_ba_demo.sh --accept-tau-license
```

The first carrier family is `qns8` and `qns64`, finite powerset Boolean
algebras over audited atoms. It is useful for candidate filtering,
controlled-vocabulary concept sets, and bounded trace-class quotients. It is
not raw natural-language semantics and it is not probabilistic Tau.

The EML/qNS certificate demo uses the same finite carrier as a fast evidence
gate after bounded symbolic-regression search:

```bash
./scripts/run_eml_qns_demo.sh --accept-tau-license
```

This is not full symbolic regression and not native Tau analytic semantics.
The point is the public architecture: slow formula search outside Tau, compact
certificate masks inside Tau, and fail-closed rejection for missing evidence.

## 7. Upstream Future-Work Alignment

Goal: map official Tau future-work items to small reproducible experiments.

The detailed status page is `docs/tau-future-work-map.md`.

The official future-work list includes:

- fixed-width modular arithmetic in Tau specifications
- efficient data storage and manipulation using Boolean functions
- normalization and satisfiability performance
- redefinitions of functions or predicates
- arbitrary stream names
- Boolean-function normalization performance

Current best-aligned experiment tracks:

- **Boolean-function storage:** safe table helpers, pointwise revision, and
  source-to-helper lowering.
- **Normalization and sat performance:** guarded qelim dispatch, restricted
  rewrite normalization, equality-aware path simplification, and solver
  telemetry.
- **Redefinitions:** compatibility-checked pointwise revision as a semantic
  model for safe updates.
- **Incremental execution:** read-set analysis, partial evaluation, and
  single-key update semantics before runtime recomputation.
- **Fixed-width modular arithmetic:** width-indexed modular rewrite triage,
  including counterexamples for invalid integer rewrites under overflow.
- **Fixed-width constant folding:** a checked constant-folding and identity
  simplification kernel plus an executable corpus.
- **Arbitrary stream names:** stream-key renaming should preserve denotation
  when the renamed environment agrees with the original environment.

First runnable artifact:

```bash
python3 scripts/run_incremental_execution_demo.py \
  --out results/local/incremental-execution-demo.json
```

This is a Tau-like prototype over the four-cell Boolean algebra. It verifies
that incremental recomputation matches full reevaluation after one input key
changes, while recomputing fewer unique residual nodes on the current corpus.
It also includes irrelevant-change controls where the cached value is reused
without recomputing any node.
The prototype emits a runtime-shaped dependency plan with stable node IDs and
checks that the changed-key dependency index matches the unique recomputation
set.

Matching proof artifact:

- the scoped Lean packet proves read membership correctness,
  evaluation-depends-only-on-reads, partial-evaluation soundness, incremental
  cache-invalidation soundness, and unread-key cache reuse
- the proof packet is intentionally smaller than Tau itself, so it should guide
  the runtime patch rather than be presented as a whole-language proof

Boundary:

- These are community research experiments, not upstream Tau commitments.
- A theorem about a helper IR is not a theorem about Tau's parser or full
  runtime.
- A benchmark on the local corpus is not a global performance theorem.
- Exhaustive small-width bitvector checks are rewrite triage, not a full solver
  or CVC5 integration.
- The bitvector identity rewrites are now locally Lean-proved for the small
  expression kernel. This is still not a full Tau bitvector implementation or
  CVC5 integration.
- Stream-renaming invariance is a parser/runtime correctness obligation, not an
  implementation by itself.
- Equality-aware path simplification is path-scoped. Representative
  substitution is valid only under the branch equalities that justify it.
- The Tau-facing equality-split recombination probe shows a normalizer
  opportunity, not a completed default Tau optimization. The feature-gated pass
  closes the smoke corpus and the generated path-sensitive corpus on normalized
  size: `48 / 48` generated cases are target-sized with the flag enabled. The
  four-variable equality-chain stress corpus is also closed on size:
  `105 / 105` stress cases are target-sized with the flag enabled. The
  five-variable wide corpus is also closed on size: `200 / 200` wide cases are
  target-sized with the flag enabled. A whole-command timing screen on the
  wide corpus measured `19958.521 ms` baseline normalize time and `19432.444 ms`
  enabled normalize time, with Tau process startup included in both numbers.
  An idempotence screen sharpened the next target: baseline had `7 / 200`
  first-pass fixed points, while the enabled pass had `140 / 200`; `60 / 200`
  enabled outputs still changed under a second `normalize`, and `30 / 200`
  grew. A guarded second-pass candidate keeps `200 / 200` target-sized output,
  keeps total normalized size at `1980` characters, and improves exact target
  presentation to `160 / 200`. The next target is fixed-point presentation
  canonicalization and still broader generated corpora.
