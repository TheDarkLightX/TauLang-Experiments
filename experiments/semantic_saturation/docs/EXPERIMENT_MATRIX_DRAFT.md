# Experiment matrix before holdout

Status: draft, pending development calibration and audit. All numbers below are fixed design intent; no held-out result is known.

## Quality and mechanism experiment

The original generator creates 84 training rows, 84 development rows, and 336 test rows. Training/development are exploratory budget and implementation data. The test set is a single confirmatory pass; repeat runs concern timing/determinism only.

- Pure terms: 2, 4, 6, 8 variables; nominal generation budgets 16, 32, 64; 4 replicates per test stratum.
- Formula/one-binder families: 1, 2, 3 free variables; nominal budgets 16, 32, 64; 4 replicates.
- Mixed two-binder family: 0, 1, 2 free variables; nominal budgets 16, 32, 64; 4 replicates.
- Seen structural families: random term, random formula, quantified random formula, and factoring composition.
- Held-out structural templates: multiplexer trees, parity chains, proper-split composition, and mixed quantified pairs.

These are structural-template holdouts, not unseen semantic laws: XOR occurs in training and the proper-split law occurs in the inherited pilot. Mixed quantified pairs independently sample existential/universal binders; not every pair alternates. Actual binder patterns will be reported. Seeds are SHA256-derived from the frozen generator label namespace. No optimized targets are supplied by the generator. Exact context-plus-AST duplicates across splits are reported after generation, not silently removed.

The main representation-mechanism comparison is rewrite-disabled semantic egraph versus the explicit full-AST scoped congruence table, with the same checked pair transcript. Both retain every alternative and use typed emitted-byte cost. A mismatch requires investigation as a comparator or implementation difference before crediting an egraph benefit. Full hybrid versus the no-rewrite semantic controls is a search-policy/rule-generation comparison, not isolated evidence for an egraph data structure.

All primary arms use the same original AST. Matched semantic controls consume the same native candidate, fixed grammar bank, checked pairs and budgets. Native raw and retain-input-guarded output are reported separately. The native-plus-SymPy portfolio includes both components' work. Baselines that discard alternatives or have weaker binder congruence are not admissible mechanism controls.

## Provisional implementation budgets

- Egraph: 3 rewrite rounds, 1,000 enodes.
- Native: 5 seconds per direction, strict stdout/stderr/exit classification.
- SymPy: 5-second total CNF/DNF portfolio deadline, at most 8 propositions.
- Registry: first 64 visible subtrees, at most 64 checked pairs, first 128 fixed-bank candidates by declared byte objective, at most 3 signature-matching alternatives per subtree.
- Independent terms: at most 8 variables, 256 Boolean corners; 2,000,000 node evaluations.
- Independent formulas: at most 3 free variables/255 nonempty initial supports; 250,000 states; 2,000,000 node evaluations; 8 variable slots; 4 binder depth.

Quantified subtrees are complete candidate roots. Proposal traversal stops under their binders; any semantic pair is checked in its exact free-variable context. Both congruence engines still preserve scoped algebraic structure within binders. Every transformed final expression must independently parse back to its source AST and pass support comparison and native checks of the actual emitted typed strings in both directions. Retained identical originals are labeled structural identity, not a new equivalence finding; unknown is never promoted.

## Resource matrix

Run the independent evaluator with explicitly varied caps, separate from optimizer quality:

- Free variables n=0,1,2,3,4,5 on constant, atom, conjunction and endpoint-boundary formulas.
- Initial-support caps 255 and 65,535; n=5 is expected to reject before enumeration. Never allocate a 4-billion-entry vector.
- State caps 1,000; 10,000; 250,000, with node cap 2,000,000.
- Quantifier depths 0,1,2,3,4 on free counts 0,1,2,3. Quantified-false and proper-split contexts expose exhaustive versus short-circuit behavior. These synthetic stressors do not represent typical Tau workload prevalence.
- A fixed 24-row development-derived search slice evaluated at enode caps250,1,000,4,000 and rewrite rounds1,3,5. This is a separate search-resource screen, not retuning the primary test endpoint.

## Reuse matrix

Compare a no-cache gate, ordinary exact-pair syntax memoization, and the semantic registry while retaining native final certification on changed syntax. Streams use 64 requests per mixture; record cumulative cost from the empty cache and bank construction, and every cache hit/miss/unknown.

Mixtures: 100% exact repeats; 50% exact/50% syntactically different equivalent forms; 25% exact/25% equivalent variants/50% fresh; 100% fresh. Alpha-renamed contexts form a separate context-safety stream and must not share certificates without explicit alignment; no cross-context reuse is assumed. Bindings, theory, constants, temporal profile, checker source/binary identity, and variable ordering are part of the key.

The exact repetitions are deliberately repeated-workload data, separate from the structural holdout. The repeated source families and query sequences will be committed before running this matrix. Native-gate savings beyond ordinary exact memoization are not presumed: newly equivalent syntax still requires its own native check under the study's contract. A semantic index can reduce proposal work without automatically authorizing free native certification.

## Statistics and conclusions

Primary deterministic summaries: all denominators, wins/ties/regressions, absolute byte sums and per-family distributions. Byte nonregression after retain-input selection is a design invariant. Report paired median differences and a family-stratified bootstrap interval (2,000 fixed-seed resamples) only as finite synthetic-corpus uncertainty; use no p-value publication threshold.

Runtime observations are process-inclusive on one cloud CPU environment. The same-transcript quality run reports measured component times and full cold native receipt charges; shared caches make those components unsuitable as independent online method speedups. Run three fixed interleaved repetitions of the 24-row timing slice before any runtime claim, with cache/build costs explicit. Report all three, not the fastest.

The publication gate concerns a sound useful result, possibly negative, not a positive significance threshold. Known comparator counterexamples, aborted runs, platform differences, unknowns, and resource failures remain in the artifact.
