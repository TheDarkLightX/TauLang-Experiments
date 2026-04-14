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

The intended workflow is:

```bash
git clone https://github.com/TheDarkLightX/TauLang-Experiments.git
cd TauLang-Experiments
./scripts/setup_tau.sh --accept-tau-license
./scripts/apply_patches.sh
./scripts/run_table_demos.sh
```

`setup_tau.sh` clones the official Tau Language repository into `external/tau-lang`. That directory is gitignored and should not be committed here.
By default, the script checks out the Tau commit used by the current patch
evidence. Set `TAU_REF=main` only when intentionally testing patch drift.

For the smooth path, run one command:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

That command clones official Tau if needed, applies the local experiment patch,
regenerates Tau's parser, builds Tau, and runs the safe table demos.

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
- an opt-in qelim rewrite probe flag,
  `TAU_QELIM_BDD_KB_REWRITE=1`, for the restricted c111-inspired
  simplification experiment. Current evidence keeps this opt-in: it preserves
  output parity and reduces compiled expression nodes on targeted formulas, but
  timing is mixed on generated matrices.

The table syntax is rejected unless `TAU_ENABLE_SAFE_TABLES=1` is set.

## Current Research Threads

- Finite tables as an executable semantic kernel.
- Completed reference semantics for infinite tables.
- Safe recurrence fragments: monotone and omega-continuous kernels.
- Negative boundaries: same-stratum complement and unsafe current-state guards.
- Fragment-sensitive quantifier elimination.
- Proof-carrying optimization passes.
- Restricted Knuth-Bendix-style rewrite normalization for Tau expressions.
