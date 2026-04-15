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
it uses the compound equivalence check for the table-vs-raw obligations. To run
the older separate-check audit path, use:

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
  on that corpus.
- opt-in qelim rewrite probe flags,
  `TAU_QELIM_BDD_KB_REWRITE=1` and
  `TAU_QELIM_BDD_KB_REWRITE=guarded`, for the restricted c111-inspired
  simplification experiment. Current evidence keeps this opt-in: it preserves
  output parity and reduces compiled expression nodes on targeted formulas and
  generated absorption-heavy matrices. A separate auto-route matrix shows it
  does not materially improve `TAU_QELIM_BACKEND=auto`, so it is not validated
  as a default Tau optimization.

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
