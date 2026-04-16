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

## Interpretation

The internal command-body result is strong: skipping the redundant
value-argument inference pass removes almost all measured `get_rr` time on this
corpus.

The audit result strengthens the local evidence: on the checked corpus, the
skipped RR and full-inference RR are structurally equal, not merely
solver-result equivalent.

The whole-process result is intentionally not claimed as a public demo speedup.
The current wrapper still launches many Tau processes, so process startup,
source loading, parsing, and file I/O dominate elapsed time. This is why the
internal solver time improves while wall-clock time is roughly flat.

## Boundary

This is not a default Tau optimization yet.

Promotion would require:

- a larger non-table corpus,
- cases where `type == tau::spec` remains on the full inference path,
- a code-level invariant or proof artifact that parser-time inference is enough
  for the skipped `ref_value` branch,
- an in-process benchmark that removes process startup from the timing signal.

The current status is:

```text
output parity passed on the checked safe-table solver corpus
internal RR extraction speedup measured
default promotion not justified yet
```
