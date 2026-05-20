# Research Log: TauEnergy Measured Training

Date: 2026-05-20

## Hypothesis

TauEnergy can learn useful Tau optimizer route ordering from Tau-checked
formulas and measured route receipts. The model remains advisory. Tau and
deterministic route certificates remain authoritative.

## Experiment 1: One Genuine Optimization

Artifact:

```bash
python3 scripts/run_tau_optimizer_workbench.py \
  --verify results/local/tau-energy/optimizer_workbench.json
```

Result:

```text
accepted route: indexed_impacted_factor_solve
factor count: 24
impacted factors: 3
solver-call reduction: 8.0x
invalid accepts: 0
```

Interpretation: this is one concrete Tau optimization claim with a live Tau
receipt.

## Experiment 2: Synthetic Shape Learning

Artifact:

```bash
python3 scripts/train_tau_fragment_energy.py \
  --verify results/local/tau-energy/fragment_training_report.json
```

Result:

```text
Tau-checked formulas: 1000
failed checks: 0
held-out learned top-1: 1.0
hand route-prior baseline: 0.2
invalid accepts: 0
```

Interpretation: TauEnergy can learn formula-shape route categories, but this
uses a synthetic route oracle.

## Experiment 3: Measured Route Labels

Artifact:

```bash
python3 scripts/train_tau_measured_fragment_energy.py \
  --verify results/local/tau-energy/measured_fragment_training_report.json
```

Result:

```text
Tau-checked cases: 254
training rows: 1218
test rows: 306
held-out learned top-1: 0.921569
hand route-prior baseline: 0.254902
mean calls to best route: 1.137255
invalid accepts: 0
```

Interpretation: measured labels are viable. The model improves checker order
against the workbench hand baseline while preserving Tau authority.

## Experiment 4: Cross-Seed And Family Holdout

Artifact:

```bash
python3 scripts/stress_tau_measured_fragment_energy.py \
  --verify results/local/tau-energy/measured_fragment_stress_report.json
```

Result:

```text
cross-seed fitted top-1 min/mean/max: 0.8 / 0.88 / 0.96
cross-seed top-1 delta min/mean/max: 0.6 / 0.666667 / 0.76
family-holdout fitted top-1 min/mean/max: 0.041667 / 0.777778 / 1.0
invalid accepts: 0
```

Finding: random splits are strong, but ordered-BDD family holdout is weak.

```text
ordered-BDD holdout fitted top-1: 0.041667
ordered-BDD mean calls to best route: 2.041667
```

Interpretation: the ranker needs targeted BDD examples. More generic examples
are not the highest-value next step.

## Experiment 5: Ordered-BDD Curriculum

Artifact:

```bash
python3 scripts/train_tau_ordered_bdd_curriculum.py \
  --verify results/local/tau-energy/ordered_bdd_curriculum_report.json
```

Purpose: keep the non-BDD measured corpus fixed, add increasing numbers of BDD
training examples, and test on held-out BDD formulas.

Result:

```text
base measured examples: 124
held-out BDD pool: 96
failed checks: 0
invalid accepts: 0
top-1 with zero targeted BDD examples: 0.90625
top-1 with 32 targeted BDD examples: 0.9375
best top-1: 0.9375
```

Interpretation: the earlier ordered-BDD holdout failure was not a hard model
limit. A larger balanced measured base already transfers much better, and
targeted BDD examples add a smaller improvement. The next training work should
track both targeted route-family examples and balanced non-BDD coverage.

## Current Conclusion

The training can go farther. The next useful training is targeted, measured,
and fragment-specific. Ordered-BDD route selection is the first identified
curriculum target.

## Next Work

- Add more real Tau benchmark commands to the measured corpus.
- Add syntax-drift regeneration tests.
- Add route-specific certificate depth for BDD order selection.
- Compare linear ranker with a small tree or MLP only after improving labels.
