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
