# Tau Optimizer Workbench

Project boundary: this is a community research prototype. It is not an official
IDNI or Tau Language feature, not a default optimizer route, and not an
endorsement claim.

## Purpose

The workbench demonstrates a developer-facing version of TauEnergy:

```text
Tau formula and changed variables
-> factor/support world model
-> TauEnergy route ranking
-> WES-style evidence schedule
-> live Tau diagnostic receipt
-> accepted or rejected optimization claim
```

The current end-to-end optimization is narrow and concrete. For a sparse
top-level conjunction, the indexed-factor route solves only factors impacted by
a small variable delta. Live Tau still checks scan/index parity and reports the
full and indexed solver-call counts.

## Run

```bash
python3 scripts/run_tau_optimizer_workbench.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/optimizer_workbench.json
```

Verify the receipt:

```bash
python3 scripts/run_tau_optimizer_workbench.py \
  --verify results/local/tau-energy/optimizer_workbench.json
```

Train a small route ranker from live Tau labels:

```bash
python3 scripts/train_tau_optimizer_energy.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/optimizer_training_report.json
python3 scripts/train_tau_optimizer_energy.py \
  --verify results/local/tau-energy/optimizer_training_report.json
```

Train a larger fragment-route ranker from Tau-checked synthetic formulas:

```bash
python3 scripts/train_tau_fragment_energy.py \
  --examples 1000 \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/fragment_training_report.json
python3 scripts/train_tau_fragment_energy.py \
  --verify results/local/tau-energy/fragment_training_report.json
```

## What Counts As Success

The receipt is accepted only when:

- TauEnergy ranks the indexed route first.
- The WES-style scheduler finds a useful claim at the first checker call.
- Live Tau reports `scan_equals_indexed=1`.
- Live Tau reports zero full-solver and indexed-solver errors.
- The indexed route uses fewer solver calls than the full factor scan.
- The unchecked cache negative control is not accepted.

## World Model

The emitted `world_model` is intended for user discussion and developer review.
It names the changed variables, all factor supports, impacted factors,
unimpacted factors, and the transition from formula to factor graph to route
candidate to Tau receipt.

This is not a full semantic world model for all of Tau. It is the smallest
world model that makes one optimizer claim inspectable.

## Training Status

The first trainable model is a small linear ranker over live Tau-labeled route
rows. Each workload generates a Tau formula, records a fragment profile
(top-level conjunction, nonzero factors, support sizes, impacted factor ratio),
and supplies three candidates: indexed factor solving, full factor scan, and an
unchecked-cache negative control. Tau labels the indexed route useful only when
it reports scan/index parity, zero errors, and fewer solver calls than the full
scan.

This is still an early EBRM baseline. It is trained enough to learn this narrow
route family, but not trained enough to generalize across all Tau optimizer
designs. If Tau syntax changes, regenerate the synthetic formulas and relabel
them with the current Tau binary instead of treating old rows as stable facts.

The fragment-route trainer scales the same pattern to generated Tau formulas.
It samples read-once, small truth-table, ordered-BDD, Tseitin-style, and
quantified formula shapes from grammar-compatible Tau syntax. Every generated
formula is solved by the local Tau binary before the row is allowed into
training. The learned model is still only a route-ordering model; route-specific
certificates or Tau fallback decide semantic correctness. The reported baseline
is a conservative hand route-prior baseline inside this workbench, not a claim
about Tau's production optimizer heuristics.
