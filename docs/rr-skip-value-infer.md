# RR Value-Inference Skip

This is a feature-gated Tau-side optimization experiment for the safe-table
solver corpus.

## Feature Flag

```bash
TAU_RR_SKIP_VALUE_INFER=1
```

When the flag is set, `get_nso_rr_with_defs` skips the second full
`infer_ba_types(build_spec(rr_with_defs), ...)` pass for command arguments that
are both:

- non-`spec` values,
- already ref-valued after parser-time type inference.

The ordinary path is unchanged when the flag is absent.

## Why This Was Worth Testing

Telemetry showed that the table-demo solver checks were dominated by:

```text
solve_cmd
  -> apply_rr_to_nso_rr_with_defs
     -> get_nso_rr_with_defs
        -> infer_ba_types
```

On the checked corpus, every `rr_get_defs` branch was `ref_value_rr`, and
`infer_ms` was more than 90% of `get_nso_rr_with_defs` time. The candidate
optimization is therefore direct: avoid re-inferring a value argument that was
already typed during parsing, then apply the same stored definitions as before.

## Reproduction

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --reps 3 \
  --out results/local/rr-skip-value-infer-demo-reps3.json
```

The wrapper runs the same safe-table solver checks twice:

- baseline mode,
- skip mode with `TAU_RR_SKIP_VALUE_INFER=1`.

It requires output parity first. Speed is measured only after all solver checks
still return `no solution`.

To run the local structural audit:

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --audit \
  --reps 1 \
  --out results/local/rr-skip-value-infer-audit-reps1.json
```

Audit mode sets:

```bash
TAU_RR_SKIP_VALUE_INFER=1
TAU_RR_SKIP_VALUE_INFER_AUDIT=1
```

For each skipped branch, Tau also computes the full inference path and checks
that the extracted RR is structurally equal to the skipped RR. If the comparison
fails, the command fails closed.

Audit mode is not a performance mode. It deliberately runs the full path.

To measure the shortcut inside one Tau process over all fifteen table-vs-raw
obligations:

```bash
python3 scripts/run_rr_skip_batched_table_checks.py \
  --reps 1 \
  --out results/local/rr-skip-batched-table-checks-reps1.json
```

This uses the same prefix-dot command-file shape as the batched table demo.

To test the same shortcut outside safe-table syntax, run the ordinary reference
solver corpus:

```bash
python3 scripts/run_rr_skip_reference_solver_corpus.py \
  --out results/local/rr-skip-reference-solver-corpus.json
```

This corpus uses small named `:tau` definitions and asks Tau to prove ordinary
Boolean-algebra identities unsatisfiable after reference expansion. It compares
baseline, skip, and audit mode. It is deliberately small, but it checks that the
optimization is not only a table-syntax artifact.

## Current Local Receipt

Fast mode:

```text
ok: true
checks: 5
repetitions: 3

baseline solve total: 261.038000 ms
skip solve total:      60.136580 ms
solve improvement:     76.963%

baseline get_rr:      209.216570 ms
skip get_rr:            4.595369 ms
get_rr improvement:    97.804%

baseline elapsed:   106770.857 ms
skip elapsed:       107136.971 ms
elapsed change:         -0.343%

skip branches:
  ref_value_skip_infer: 15
```

Audit mode:

```text
ok: true
checks: 5
repetitions: 1
audit rows: 5
structurally equal audit rows: 5
skip branches:
  ref_value_skip_infer: 5
```

Batched one-process mode:

```text
ok: true
checks: 15
repetitions: 1

baseline elapsed:      59058.949 ms
skip elapsed:          57177.551 ms
elapsed improvement:       3.186%

baseline solve total:    816.446700 ms
skip solve total:        200.560990 ms
solve improvement:        75.435%

baseline get_rr:         619.139900 ms
skip get_rr:               4.544364 ms
get_rr improvement:       99.266%
```

Ordinary reference-definition corpus:

```text
ok: true
cases: 9
audit rows: 9
structurally equal audit rows: 9

baseline elapsed: 692.424 ms
skip elapsed:     684.416 ms
elapsed improvement: 1.157%

baseline solve total: 16.448360 ms
skip solve total:      7.309008 ms
solve improvement:    55.564%

baseline get_rr: 11.644820 ms
skip get_rr:      2.432774 ms
get_rr improvement: 79.109%
```

## Interpretation

The internal command-body result is strong: skipping the redundant
value-argument inference pass removes almost all measured `get_rr` time on this
corpus.

The audit result strengthens the local evidence: on the checked corpus, the
skipped RR and full-inference RR are structurally equal, not merely
solver-result equivalent.

The one-process batched result is the stronger performance receipt. It removes
most repeated process startup and shows a small wall-clock improvement on the
demo corpus, while the internal solver-path improvement remains much larger.
The earlier one-process-per-check wrapper still has roughly flat wall-clock
time because repeated Tau startup and source loading dominate elapsed time.

The ordinary-reference corpus broadens the evidence. The skip path preserved
`no solution` results and passed the structural audit on named definitions such
as commutativity, absorption, double prime, De Morgan laws, and guarded choice.
This does not make the shortcut default-safe, but it reduces the chance that the
benefit is caused only by the safe-table parser surface.

Post-skip telemetry changes the next target. With
`TAU_RR_SKIP_VALUE_INFER=1` enabled on the five representative table-demo
solver checks, the compact RR telemetry receipt shows:

```text
rr_get:                    1.800762 ms
rr_apply_formula:         16.610380 ms
rr_formula_transform:      9.079930 ms
rr_formula_rewrite:        6.509593 ms
rr_formula_fixed_point:    0.691629 ms
solve total:              19.575530 ms
```

So the next internal solver-path target is not more `get_rr` work on this
corpus. It is `apply_rr_to_formula`, especially reference-argument
transformation and recurrence-definition rewriting.

The first feature-gated response is:

```bash
TAU_RR_TRANSFORM_DEFS_CACHE=1
```

This cache stores transformed recurrence-definition lists inside one Tau
process. It is designed for batched workloads where several `solve` obligations
share the same stored definitions and differ only in the main query.

Reproduce the direct comparison with:

```bash
python3 scripts/run_rr_transform_defs_cache_batched.py \
  --reps 1 \
  --out results/local/rr-transform-defs-cache-batched-reps1.json
```

Current local receipt, with `TAU_RR_SKIP_VALUE_INFER=1` enabled in both modes:

```text
ok: true
checks: 15
cache hits: 14 / 15

no-cache solve total: 201.090410 ms
cache solve total:    130.026990 ms
solve improvement:     35.339%

no-cache rr_apply_formula: 187.126540 ms
cache rr_apply_formula:    115.095850 ms
apply improvement:          38.493%

no-cache rr_formula_transform: 81.398570 ms
cache rr_formula_transform:     6.625784 ms
transform improvement:         91.860%

no-cache elapsed: 54390.996 ms
cache elapsed:    56725.073 ms
elapsed change:      -4.291%
```

Interpretation: the cache substantially reduces the internal formula-application
path. It is not yet a public demo wall-clock improvement because process-level
elapsed time remained noisy and worsened on this receipt.

## Active Rule Filtering

After transformed-definition caching, the remaining formula-application hotspot
is the rewrite pass itself. The next feature-gated candidate is:

```bash
TAU_RR_ACTIVE_RULES=1
```

The pass scans the current term for reference signatures and applies only
definition rules whose head reference signature is currently present. If a
rewrite introduces a new reference later, the surrounding `repeat_all` loop can
pick it up in a later pass. Rules with no recognizable head reference are kept
conservatively.

Reproduce the direct comparison with:

```bash
python3 scripts/run_rr_active_rules_batched.py \
  --reps 1 \
  --out results/local/rr-active-rules-batched-reps1.json
```

Current local receipt, with `TAU_RR_SKIP_VALUE_INFER=1` and
`TAU_RR_TRANSFORM_DEFS_CACHE=1` enabled in both modes:

```text
ok: true
checks: 15

baseline solve total: 123.479850 ms
active solve total:    35.047750 ms
solve improvement:     71.617%

baseline rewrite:      99.341180 ms
active rewrite:        11.068379 ms
rewrite improvement:   88.858%

active-rule rows:      45
rules before filter:   2250
rules after filter:      60
rules skipped:         2190

baseline elapsed:      53325.691 ms
active elapsed:        53391.626 ms
elapsed change:           -0.124%
```

Interpretation: this is the strongest current internal-path optimization after
the RR extraction skip. It is not a whole-command speedup on this receipt
because the benchmark is dominated by process setup and source loading.

## Boundary

This is not a default Tau optimization yet.

Promotion would require:

- a larger non-table corpus,
- a decision about the excluded three-variable distributivity candidate, which
  segfaulted in this Tau build before solver stats in the baseline and skip
  paths,
- cases where `type == tau::spec` remains on the full inference path,
- a code-level invariant or proof artifact that parser-time inference is enough
  for the skipped `ref_value` branch,
- a broader in-process benchmark beyond the safe-table demo corpus.
- a proof or code invariant for active-rule filtering, namely that skipping a
  rule whose head reference signature is absent from the current term preserves
  the fixed point reached by the surrounding rewrite loop.

The current status is:

```text
output parity passed on the checked safe-table solver corpus
internal RR extraction speedup measured
batched one-process wall-clock improvement measured on the demo corpus
ordinary reference-definition corpus passed structural audit
active-rule filter reduced internal rewrite time on the batched corpus
default promotion not justified yet
```
