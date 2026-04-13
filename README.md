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
- BDD and finite-clopen carrier experiments
- Lean proof receipts for semantic claims
- benchmark harnesses and reproducibility scripts
- small Tau example programs written for this research

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
./scripts/setup_tau.sh
./scripts/apply_patches.sh
./scripts/run_benchmarks.sh
```

`setup_tau.sh` clones the official Tau Language repository into `external/tau-lang`. That directory is gitignored and should not be committed here.

## License Boundary

This repository contains original research code and documentation. It does not grant any rights to Tau Language itself. Tau Language remains governed by IDNI's license.

Patch files in `patches/` are intended for research review and reproduction. Keep patches small and focused. For substantial changes to Tau Language, the preferred path is an upstream pull request or explicit permission from IDNI.

## Current Research Threads

- Finite tables as an executable semantic kernel.
- Completed reference semantics for infinite tables.
- Safe recurrence fragments: monotone and omega-continuous kernels.
- Negative boundaries: same-stratum complement and unsafe current-state guards.
- Fragment-sensitive quantifier elimination.
- Proof-carrying optimization passes.
