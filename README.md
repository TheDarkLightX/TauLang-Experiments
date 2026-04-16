# TauLang Experiments

Independent research artifacts, examples, proofs, benchmarks, and patch files for experiments with Tau Language.

This repository does **not** redistribute Tau Language source code or binaries. Users must obtain Tau Language from the official IDNI repository and comply with its license:

```text
https://github.com/IDNI/tau-lang
```

## Purpose

This repo is for educational and research work around Tau Language, including:

- finite table semantics experiments
- infinite table reference-semantics research
- quantifier-elimination dispatch experiments
- restricted Tau rewrite-normalizer experiments
- BDD and finite-clopen carrier experiments
- Lean proof artifacts for semantic claims
- benchmark harnesses and reproducibility scripts
- small Tau example programs written for this research

## Project Boundary

This is a community research prototype.
It is not an official IDNI or Tau Language implementation, not an endorsement
claim, and not a statement about what IDNI intends to ship.
The table syntax, helper functions, qelim experiments, and patches here may be
weaker, narrower, or differently shaped than the standard required for an
official Tau feature.

## Repository Layout

```text
docs/       Research notes, license guidance, and design writeups
examples/   Original Tau examples and experiment inputs
patches/    Minimal patch files against official Tau Language checkouts
proofs/     Lean proof artifacts and theorem packets
scripts/    Setup, patching, and benchmark helpers
results/    Benchmark reports and generated experiment summaries
```

## Reproduction Model

The full public demo path is:

```bash
git clone https://github.com/TheDarkLightX/TauLang-Experiments.git
cd TauLang-Experiments
./scripts/run_public_demos.sh --accept-tau-license
```

`setup_tau.sh` clones the official Tau Language repository into `external/tau-lang`. That directory is gitignored and should not be committed here.
By default, the script checks out the Tau commit used by the current patch
evidence. Set `TAU_REF=main` only when intentionally testing patch drift.

The public demo wrapper runs both:

- the safe table syntax and solver-equivalence demo,
- the qelim-backed policy-shape demo with residual semantic validation.

To run only the table demo, use:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

That command clones official Tau if needed, applies the local experiment patch,
regenerates Tau's parser, builds Tau, and runs the safe table demos. By default
it uses the grouped batched equivalence check for the table-vs-raw obligations.
To run the proof-compression compound query instead, use:

```bash
TABLE_DEMO_EQUIV_MODE=compound ./scripts/run_table_demos.sh --accept-tau-license
```

To run the older separate-check audit path, use:

```bash
TABLE_DEMO_EQUIV_MODE=individual ./scripts/run_table_demos.sh --accept-tau-license
```

To run only the qelim-backed policy-shape demo, use:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

The current table demo gallery is documented in:

```text
docs/demo-gallery.md
```

## License Boundary

This repository contains original research code and documentation. It does not grant any rights to Tau Language itself. Tau Language remains governed by IDNI's license.

Patch files in `patches/` are intended for research review and reproduction. Keep patches small and focused. For substantial changes to Tau Language, the preferred path is an upstream pull request or explicit permission from IDNI.

The current patch is an experiment patch, not an official Tau release. It adds:

- a four-cell finite Boolean-algebra carrier used by table demos,
- safe table helper functions,
- pointwise revision helper aliases for finite masks and symbolic `tau` values,
- feature-gated `table { when ... else ... }` syntax for guarded choice,
- guarded qelim experiment code used by the optimization research thread.
- a feature-gated equality-split recombination pass,
  `TAU_EQUALITY_SPLIT_RECOMBINE=1`. Current evidence is scoped: it reaches
  target-sized output on `8` of `8` extended recombination probes, matches all
  `8` under `mnf`, and matches `3` of `8` exactly under `normalize`. The
  remaining mismatch is presentation ordering, not a missed semantic reduction
  on that corpus. On the generated path-sensitive corpus, the same flag moves
  target-sized output from `2` of `48` baseline cases to `48` of `48` enabled
  cases. Exact `normalize` text still matches `24` of `48`, while `mnf`
  matches all `48`. On the four-variable equality-chain stress corpus, it
  reaches target-sized output on `105` of `105` cases and matches all `105`
  under `mnf`; exact `normalize` text matches `84` of `105`. On the
  five-variable wide corpus, it reaches target-sized output on `200` of `200`
  cases and matches all `200` under `mnf`; exact `normalize` text matches
  `130` of `200`.
- opt-in qelim rewrite probe flags,
  `TAU_QELIM_BDD_KB_REWRITE=1` and
  `TAU_QELIM_BDD_KB_REWRITE=guarded`, for the restricted c111-inspired
  simplification experiment. Current evidence keeps this opt-in: it preserves
  output parity and reduces compiled expression nodes on targeted formulas and
  generated absorption-heavy matrices. A separate auto-route matrix shows it
  does not materially improve `TAU_QELIM_BACKEND=auto`, so it is not validated
  as a default Tau optimization.
- an opt-in RR extraction shortcut,
  `TAU_RR_SKIP_VALUE_INFER=1`, for ref-valued command arguments that have
  already passed parser-time type inference. Current evidence is scoped to the
  checked corpora: it preserves the checked `no solution` results, reduces
  internal solve-command time by `76.963%`, and reduces measured `get_rr` time
  by `97.804%` on the safe-table three-repetition receipt. The one-process
  table corpus shows a `3.186%` wall-clock improvement, and the ordinary
  reference-definition corpus passes `9` of `9` structural audit rows with a
  `79.109%` measured `get_rr` improvement. This is still opt-in evidence, not
  default-promotion evidence.
- an opt-in transformed-definition cache,
  `TAU_RR_TRANSFORM_DEFS_CACHE=1`, for the next RR formula-application
  bottleneck after the value-inference skip. With
  `TAU_RR_SKIP_VALUE_INFER=1` held fixed, the batched table-check receipt shows
  `14` cache hits over `15` formula applications, a `91.860%` reduction in RR
  formula transform time, and a `35.339%` reduction in internal solve-command
  time. The same run did not improve whole-process elapsed time, so this is an
  internal-path optimization candidate, not a public demo default.
- an opt-in active-rule filter,
  `TAU_RR_ACTIVE_RULES=1`, for the remaining RR rewrite bottleneck after the
  first two RR flags are enabled. On the batched table-check receipt, with
  `TAU_RR_SKIP_VALUE_INFER=1` and `TAU_RR_TRANSFORM_DEFS_CACHE=1` held fixed,
  the three-repetition receipt skipped `6570` of `6750` rule applications
  considered by dynamic signature reachability, reduced RR formula rewrite time
  by `88.821%`, reduced internal solve-command time by `73.402%`, and reduced
  whole-process elapsed time by `3.625%`. This remains feature-gated because
  the proof obligation is not closed.
  The ordinary reference-definition corpus preserves outputs but does not show
  rewrite-time benefit, so the current claim is scoped to rule-heavy batched
  workloads. `TAU_RR_ACTIVE_RULES_AUDIT=1` adds a slower final-result audit
  that checks the active repeated-rewrite result against the full
  repeated-rewrite result; the current batched audit has `15 / 15`
  structurally equal rows. The proof obligation is documented in
  `docs/rr-active-rule-filter.md`.

The table syntax is rejected unless `TAU_ENABLE_SAFE_TABLES=1` is set.

## Current Research Threads

- Finite tables as an executable semantic kernel.
- Completed reference semantics for infinite tables.
- Safe recurrence fragments: monotone and omega-continuous kernels.
- Negative boundaries: same-stratum complement and unsafe current-state guards.
- Fragment-sensitive quantifier elimination.
- Proof-carrying optimization passes.
- Restricted Knuth-Bendix-style rewrite normalization for Tau expressions.
- Upstream future-work experiments: Boolean-function storage, safe
  redefinitions, normalization/sat performance, and incremental execution.

The future-work experiment map is:

```text
docs/tau-future-work-map.md
```

The first incremental-execution prototype is:

```bash
python3 scripts/run_incremental_execution_demo.py \
  --out results/local/incremental-execution-demo.json
```

It models a Tau-like expression language and checks that read-set-guided
incremental recomputation matches full reevaluation after a single input change.
The matching Lean packet closes the scoped semantic kernel for read membership,
partial evaluation, cache invalidation, and unread-key cache reuse. It is still
not a theorem about the full Tau runtime. The current prototype also emits
stable node IDs and a changed-key dependency index, matching the implementation
shape a runtime cache would need.

The first successful table-demo overhead reduction is:

```bash
python3 scripts/run_table_demo_compound_check.py \
  --out results/local/table-demo-compound-check.json
```

It replaces the repeated table-vs-raw equivalence checks with one compound
mismatch query. The current local receipt preserves the same equivalence family
and reduces elapsed time by about `55.167%` on the checked corpus. This is a
demo-obligation optimization, not a new table semantic feature.

The audit-friendly batching variant is:

```bash
python3 scripts/run_table_demo_batched_checks.py \
  --mode batch-only \
  --transport split-file \
  --layout grouped \
  --out results/local/table-demo-batched-checks.json
```

It uses Tau's existing prefix-dot CLI shape and the opt-in
`TAU_CLI_FILE_SPLIT_MODE=1` grouped command-file path to run all table-vs-raw
checks in one Tau process while preserving one `solve` result per obligation.
The current local receipt checks `15` obligations and reduces the old
all-sources-first file batch from `54357.861 ms` to `33817.738 ms`, a
`37.787%` batch-path reduction. This is command-file parse shaping and demo
harness optimization, not a solver speedup.

The first equality-aware path simplification prototype is:

```bash
python3 scripts/run_equality_path_simplification_demo.py \
  --out results/local/equality-path-simplification-demo.json
```

It targets Tau's known issue that path simplification does not use equalities
between variables. The current model reduces `29` expression nodes to `10` on
the checked corpus while preserving semantics under the required equality
assumptions. It also records counterexamples showing that the rewrite is
unsound outside those assumptions.

The related Tau-facing branch-recombination probe is:

```bash
python3 scripts/run_equality_split_tau_probe.py \
  --out results/local/equality-split-tau-probe.json
```

It asks the current Tau binary to prove candidate shorter normal forms
equivalent to equality-split formulas that Tau currently leaves longer after
normalization. The baseline local probe had `4` useful reduction cases, passed
all equivalence checks, and reduced the combined normalized-character count
from `152` to `36` in the candidate target forms. With
`TAU_EQUALITY_SPLIT_RECOMBINE=1`, the scoped C++ pass reduces the four-case
probe to the target combined size and reaches target-sized output on an
eight-case extended alias-order probe. The extended corpus matches under `mnf`
on `8` of `8` probes and matches exactly under `normalize` on `3` of `8`
probes. The remaining mismatch is presentation canonicalization rather than a
missed semantic reduction on this corpus, so this remains an opt-in, scoped
normalizer experiment rather than a default Tau optimization.
The generated path-sensitive corpus is harder than the smoke tests, but the
feature-gated pass now closes it on size: target-sized output improves from `2`
of `48` baseline cases to `48` of `48` enabled cases, and the enabled normalized
character count is `378`, exactly the target count. Exact `normalize` text still
matches `24` of `48`, while all `48` still match under `mnf`. The remaining
target is presentation canonicalization, not missed equality-split
recombination on this generated corpus.

The four-variable stress corpus extends the same idea to equality chains where
the alias branch can simplify the residual to a different atom, or to true:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --stress-path-corpus \
  --out results/local/equality-split-stress-enabled.json
```

Current receipt:

```text
target-sized cases:          105 / 105
Tau-normalized characters:   847
target-normalized characters: 847
MNF-matched target cases:    105 / 105
exact normalize matches:      84 / 105
```

The five-variable wide corpus is:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --wide-path-corpus \
  --out results/local/equality-split-wide-enabled.json
```

Current receipt:

```text
target-sized cases:          200 / 200
Tau-normalized characters:   1980
target-normalized characters: 1980
MNF-matched target cases:    200 / 200
exact normalize matches:     130 / 200
```

Whole-command timing receipt from the same 200-case corpus:

```text
baseline normalize time:     19958.521 ms
enabled normalize time:      19432.444 ms
baseline MNF time:           16847.849 ms
enabled MNF time:            16813.717 ms
```

This timing is measured around separate Tau invocations, so it includes process
startup and file I/O. It is useful as a regression screen for the experiment,
not as an in-process optimizer benchmark. The current result says the
feature-gated recombination pass removes the normalized-size blowup without
showing a whole-command timing regression on this corpus.

Optional idempotence screen:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 python3 scripts/run_equality_split_tau_probe.py \
  --wide-path-corpus \
  --check-idempotence \
  --out results/local/equality-split-wide-enabled-idempotence.json
```

Current receipt:

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

Native opt-in guarded-MNF run:

```bash
TAU_EQUALITY_SPLIT_RECOMBINE=1 TAU_NORMALIZE_GUARDED_MNF=1 \
  python3 scripts/run_equality_split_tau_probe.py \
  --wide-path-corpus \
  --check-idempotence \
  --out results/local/equality-split-wide-enabled-cxx-guarded-mnf-charvar-true-idempotence-rerun.json
```

Native opt-in receipt:

```text
exact normalize-text matches:         200 / 200
target-sized cases:                   200 / 200
normalized characters:                1480
first-pass idempotent cases:          200 / 200
second-pass growth cases:             0 / 200
same-size second-pass changes:        0 / 200
whole-command normalize time:         18893.125 ms
```

The idempotence screen uses Tau's one-character-variable parser mode. That is
load-bearing because Tau's compact pretty printer writes meets by adjacency, so
`wx` must be reparsed as `w & x`, not as one multi-character variable.

This closes the wide-corpus presentation frontier for the current guarded-MNF
experiment. The guarded-MNF route is implemented as an experimental opt-in Tau
patch behind `TAU_NORMALIZE_GUARDED_MNF=1`. It uses `mnf` as the printed form
only when it does not increase size, and it skips recursive-reference cases.
It is not a default runtime mode. The timing number above is still a
whole-command screen with process startup and file I/O, not an in-process
speedup proof.

The fixed-width modular arithmetic rewrite-triage corpus is:

```bash
python3 scripts/run_bitvector_modular_demo.py \
  --max-width 6 \
  --out results/local/bitvector-modular-demo.json
```

The bitvector constant-folding corpus is:

```bash
python3 scripts/run_bitvector_constant_folding_demo.py \
  --width 4 \
  --count 80 \
  --out results/local/bitvector-constant-folding-demo.json
```

Current local receipt: pure constant folding reduced generated width-4 nodes by
11.299%, while the additional identity simplifier reduced them by 59.351%.
Both pure constant folding and the identity simplifier are now Lean-proved for
the small expression kernel.

The arbitrary-stream-name proof kernel is documented in
`docs/arbitrary-stream-names.md`.

The opt-in type-inference fast-path telemetry is documented in
`docs/infer-fast-var-name.md`. The latest direct wrapper preserved results but
did not show a stable speedup, so it remains an experiment rather than a
promoted optimization.

The follow-up scoped cache-key model is documented in
`docs/var-name-cache-key.md`. It shows why a Tau type-inference cache cannot be
keyed by variable name alone when scoped shadowing is possible.

The implementation-shaped cache plan is documented in
`docs/type-inference-cache-plan.md`.

The first Tau-side variable-update cache attempt is documented in
`docs/infer-variable-update-cache.md`. It preserved outputs but was slower on
the current safe-table solver corpus, so it remains negative optimization
evidence.

The first successful internal RR extraction shortcut is:

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --reps 3 \
  --out results/local/rr-skip-value-infer-demo-reps3.json
```

It compares baseline RR extraction with `TAU_RR_SKIP_VALUE_INFER=1`. Current
receipt: output parity passed, internal solve-command time improved by
`76.963%`, and measured `get_rr` time improved by `97.804%` on the safe-table
solver corpus. It is not a public demo wall-clock speedup yet, because the
current harness is dominated by repeated Tau process startup.

The structural audit mode is:

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --audit \
  --reps 1 \
  --out results/local/rr-skip-value-infer-audit-reps1.json
```

Current audit receipt: `5` of `5` skipped RR branches were structurally equal to
the full-inference RR branch. Audit mode deliberately runs the full path too, so
it is correctness evidence, not a speed measurement.

The one-process batched timing lane is:

```bash
python3 scripts/run_rr_skip_batched_table_checks.py \
  --reps 1 \
  --out results/local/rr-skip-batched-table-checks-reps1.json
```

Current batched receipt: output parity passed across `15` table-vs-raw
obligations, wall-clock elapsed time improved by `3.186%`, internal
solve-command time improved by `75.435%`, and measured `get_rr` time improved
by `99.266%`. This is still a demo-corpus result, not a default Tau promotion.

The ordinary reference-definition corpus is:

```bash
python3 scripts/run_rr_skip_reference_solver_corpus.py \
  --out results/local/rr-skip-reference-solver-corpus.json
```

Current receipt: `9` Boolean-algebra identity cases passed, `9` of `9` audit
rows were structurally equal to the full-inference path, measured `get_rr` time
improved by `79.109%`, and solver-command total time improved by `55.564%`.
This broadens the evidence beyond safe-table syntax but remains a synthetic
corpus.

Post-skip telemetry now points at the next internal solver-path target. With
`TAU_RR_SKIP_VALUE_INFER=1`, the five representative table-demo checks spend
about `1.800762 ms` in `get_rr` but `16.610380 ms` in RR formula application.
The next target is therefore reference-argument transformation and
definition-rewrite work inside `apply_rr_to_formula`.

The first scoped response is:

```bash
python3 scripts/run_rr_transform_defs_cache_batched.py \
  --reps 1 \
  --out results/local/rr-transform-defs-cache-batched-reps1.json
```

Current receipt: with the value-inference skip enabled in both modes, the
transformed-definition cache hit `14` of `15` formula applications, reduced RR
formula transform time by `91.860%`, reduced RR formula-application time by
`38.493%`, and reduced internal solve-command time by `35.339%`. It did not
improve whole-process elapsed time on that run.
