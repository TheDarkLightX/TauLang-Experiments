# TauEnergy Training Tutorial

Project boundary: TauEnergy is an advisory ranker. Tau, deterministic route
certificates, and fallback checks decide whether a route result is valid.

## Mental Model

The workbench has three roles:

- LLM interface: proposes questions, explanations, and candidate sketches.
- TauEnergy: ranks structured route candidates by energy.
- Tau and certificates: check syntax, route results, and acceptance conditions.

The training target is route order, not semantic authority.

```text
Tau formula
-> Tau syntax and status check
-> candidate route measurements
-> measured best valid route label
-> TauEnergy route ranker
-> WES-style checker order
```

## Setup Check

```bash
external/tau-lang/build-Release/tau --version
python3 -m py_compile tau_energy/*.py
```

If Tau syntax changes, regenerate the reports. The report includes hashes of
the grammar files under `external/tau-lang/parser`.

## Run The End-To-End Optimization

```bash
python3 scripts/run_tau_optimizer_workbench.py \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/optimizer_workbench.json

python3 scripts/run_tau_optimizer_workbench.py \
  --verify results/local/tau-energy/optimizer_workbench.json
```

This demonstrates one concrete optimization: indexed impacted-factor solving
for a sparse top-level conjunction.

## Train From Measured Labels

```bash
python3 scripts/train_tau_measured_fragment_energy.py \
  --examples 250 \
  --real-spec-limit 4 \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/measured_fragment_training_report.json

python3 scripts/train_tau_measured_fragment_energy.py \
  --verify results/local/tau-energy/measured_fragment_training_report.json
```

Each formula is checked by Tau. Each candidate route is accepted as a training
label only when its deterministic result matches Tau's status. The fastest
valid route becomes the measured target.

## Stress The Training

```bash
python3 scripts/stress_tau_measured_fragment_energy.py \
  --examples-per-seed 120 \
  --seeds 20260522 20260523 20260524 \
  --real-spec-limit 4 \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/measured_fragment_stress_report.json

python3 scripts/stress_tau_measured_fragment_energy.py \
  --verify results/local/tau-energy/measured_fragment_stress_report.json
```

Read the family-holdout table before interpreting the aggregate score. A weak
family holdout means the corpus does not yet teach that route family.

## Target The Ordered-BDD Gap

```bash
python3 scripts/train_tau_ordered_bdd_curriculum.py \
  --base-examples 120 \
  --bdd-pool-examples 96 \
  --bdd-train-sizes 0 2 4 8 16 32 \
  --real-spec-limit 4 \
  --tau-bin external/tau-lang/build-Release/tau \
  --out results/local/tau-energy/ordered_bdd_curriculum_report.json

python3 scripts/train_tau_ordered_bdd_curriculum.py \
  --verify results/local/tau-energy/ordered_bdd_curriculum_report.json
```

This curriculum measures whether ordered-BDD route selection improves when the
ranker receives targeted measured BDD examples.

## Reading Results

Use these fields first:

- `failed_check_count`: must be zero for the report to pass.
- `invalid_accept_count`: must be zero.
- `fitted_test_top1` or `fitted_top1`: learned route is first.
- `mean_calls_to_best_route`: expected WES checker calls before the best route.
- `family_holdout`: generalization by route family.

Do not use aggregate top-1 alone as a promotion claim.

## Demo Summary

After generating the artifacts, print a compact walkthrough:

```bash
python3 scripts/demo_tau_energy_training_results.py
```

The demo reports the accepted optimization, measured-training scores, stress
summary, weakest holdout family, and ordered-BDD curriculum steps.
