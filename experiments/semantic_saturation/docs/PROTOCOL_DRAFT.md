# Checked semantic saturation in Tau: expanded protocol draft

Status: DESIGN, not frozen. No new held-out measurements have been run.

## Frozen-base intent

- Destination base: `65ef69bdc5e6f1e479236d9dfb4d9b6d2e5302d1`.
- Official Tau source: `7625580db1a54e0b55beaf753566c137df42fe66` (0.7.0-alpha), clean source, no patches.
- Planned Linux Release build with `sbf,tau` BA pack; archive exact configuration and dependency/compiler revisions. This is not the pilot Mac executable.
- Inherited pilot: selected exploratory 24-case corpus, not train/test evidence. Verify transferred manifest before reuse. All failure/cap correction history retained.

## Research questions and falsifiers

R1. Does the concrete typed, context-fixed checked semantic registry satisfy its semantics and fail-closed contract on broader generated inputs? Any accepted inequivalent output or incorrectly accepted malformed/unknown proof receipt falsifies implementation safety. Emitted-size nonregression follows by construction from retaining the input; it is a checked invariant, not an experimental discovery.

R2. Does a hybrid egraph improve quality/cost compared with equal-resource semantic selection and recursive semantic canonicalization? If matched candidate/certificate access plus recursive quotienting matches the frontier, report no incremental egraph benefit. A larger candidate pool is not egraph benefit.

R3. How much checker work can be amortized across repeated equivalent subproblems? Charge cold registry build and all native checks. Warm cache-only results must never be called end-to-end speedups.

R4. Does a mature Boolean simplifier dominate the pure-term or propositional-skeleton lane? A null hybrid advantage is a valid result.

## Scope

Typed non-temporal formulas over nontrivial atomless Boolean algebra; pure terms contain only variables and 0/1 constants. No temporal operators, lookback, uninterpreted/opaque interpreted BA constants, bitvectors, Tau runtime compilation, arbitrary recursion, or multi-output code generation. Proper-split formulas are included to distinguish atomless from two-element semantics.

Pure terms can use exhaustive 2^n Boolean assignments with a separate minterm-transfer theorem. Full BA formulas instead quantify over all nonempty supports of minterm cells. At n free BA variables this means 2^(2^n)-1 supports. Atomless existential elimination refines each live cell as left-only, right-only, or both (3 choices). State caps must be explicit: this independent oracle is exponentially/doubly-exponentially bounded and not a scalable general replacement for Tau.

## Candidate controls

Every method starts from the same original AST and receives the same root proposal stream, shared verified pair transcript, and declared search budget.

1. Native Tau normalize (raw output and parsed/serialized cost both reported).
2. Guarded native (retain original when normalize expands): input-adaptation control.
3. Rewrite-only equality saturation.
4. Semantic root-list minimum with no egraph.
5. Recursive semantic quotienting with child recombination and no egraph.
6. Hybrid rewrite + native-certified semantic unions + congruence rebuilding.
7. SymPy 1.14.0 simplify_logic CNF/DNF, on pure terms and opaque-atom formula skeleton only; never use Boolean BA-variable substitution for quantified BA formulas.

The method-native candidate-search experiment is separate from same-stream replay. Replay isolates the representation/search mechanism and assigns the full fixed transcript cost to every consumer; it does not establish online checker amortization. A separate online run charges each method for every proposal/check it actually generates or consumes, including cold registry construction. Report explicitly generated roots versus expressions represented or reconstructed through congruence. An extracted expression absent from the root list proves composition, not novelty or superiority over recursive quotienting.

## Data separation (to freeze before holdout)

Distinct seed namespaces for train, development, and held-out test. In addition to same-family seed holdout, reserve complete structural families absent from training/development (to be specified before freeze). Generated corpus families cover unstructured balanced/skewed trees, factoring/distributivity/absorption, logical skeletons over equality/inequality atoms, and quantified atomless splits. Independent random seeds test new instances within the same synthetic generator family, not real-world workload generalization. Repeated-workload experiments intentionally share semantic families and are reported separately.

Do not inspect held-out outputs while changing generators, candidate rules, budgets, emitter, costs, or stopping criteria. Fix bugs before holdout when possible; discovered correctness bugs invalidate dependent outcomes and require recorded amendments and a new untouched test seed. Retain old runs.

## Metrics

Primary: actual emitted UTF-8 expression bytes under one parseable serializer (same complete file wrapper cost separately). Also report native raw bytes, source AST nodes, expanded output AST nodes, unique structural DAG nodes, tree depth, accepted/rejected/unknown/timeout/error counts. No global optimum claim.

Cost accounting: process-inclusive native time, independent check time, candidate generation, registry cold construction, native pair checks/hits, egraph insertion/union/rebuild/extraction, emission, per-method end-to-end, peak memory when measured reliably. Timings are Linux-machine-specific whole-command measures, not intrinsic Tau optimization speedups.

Report paired distributions and family-specific wins/ties/regressions. Any confidence intervals are resampling uncertainty of this finite synthetic corpus, not arbitrary programs. Predeclare the primary comparison and avoid selecting a significance threshold after seeing results. No p-value-based publication rule.

## Resource stages

A. Import/check existing pilot; implement/freeze exact AST and check-gate semantics; unit/negative controls.
B. Train/dev only: bounded correctness and budget calibration; freeze corpus generator, policies, seeds, analysis code, scale matrix, and repeated-workload matrix before any holdout output is seen.
C. Independent review of frozen protocol and implementation, then one held-out evaluation.
D. Replay all emitted programs and independent validation; fixed repetitions for timing only, never pick best run.
E. Scale/resource and repeated-workload lanes; predeclared caps count as failures/unknowns.
F. Independent raw-evidence falsification, Lean replay, paper/manifest/reproduction audit.

## Publication gate

A self-contained scientific claim, rigorous null finding, or clearly useful systems case study. Target contribution: executable support-semantics reduction with a real exactness/refinement theorem for the precisely scoped quantified fragment, connected to concrete parser/receipt bytes and decisive boundary controls, together with a measured positive or negative account of registry/egraph tradeoffs. More cases or a theorem assuming a sound oracle alone is insufficient. Require honest prior-art position; executed raw evidence; valid exact scopes; complete failure accounting; no consequential unresolved correctness flaw; no Tau source or binary redistributed. Passing internal checks is not peer review or acceptance. Parent approves readiness before any GitHub push.
