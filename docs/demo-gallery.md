# Table Demo Gallery

Project boundary: this is a community research prototype.
It is not an official IDNI or Tau Language table implementation, not an
endorsement claim, and not a statement about what IDNI intends to ship.
The demos are narrower than full TABA tables and may not meet the standard
required for an official Tau feature.

Run the full public demo suite with:

```bash
./scripts/run_public_demos.sh --accept-tau-license
```

Run only the safe table syntax and solver-equivalence demo with:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

The default demo runner uses the compound equivalence check for the table-vs-raw
obligations. For an audit-friendly batched path that keeps one solver result
per obligation while using one Tau process and the opt-in command-file runner,
run:

```bash
TABLE_DEMO_EQUIV_MODE=batched ./scripts/run_table_demos.sh --accept-tau-license
```

For the older one-check-at-a-time audit path, run:

```bash
TABLE_DEMO_EQUIV_MODE=individual ./scripts/run_table_demos.sh --accept-tau-license
```

Run only the qelim-backed policy-shape demo with:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

The script clones official Tau Language, applies the local experiment patch,
regenerates the parser, builds Tau, and runs the qelim-backed policy checks with
residual semantic validation. The demo suite does not require committing Tau
Language source into this repository.

## What The Demos Show

The current public suite checks these table behaviors:

- Native table syntax lowers to the same Boolean-algebra value as the raw
  guarded-choice expansion.
- Overlapping guards are handled by first-row priority.
- A table can act as an explanation ladder, returning the first failed admission
  reason.
- A table row can contain a state transformer, so the table computes a next
  symbolic memory state from an old symbolic memory state.
- Pointwise revision can update a symbolic table entry while preserving old
  values outside the guard.
- The parser rejects table syntax unless `TAU_ENABLE_SAFE_TABLES=1` is set.

## Demo 1: Protocol Firewall

File:

```text
examples/tau/protocol_firewall_priority_ladder_v1.tau
```

This demo is a priority ladder:

```tau
table {
  when emergency => freeze;
  when exploit => quarantine;
  when oracle => slow;
  when liquidity => cap;
  when governance => review;
  when normal => allow;
  else => deny
}
```

The interesting fact is not that the table can be expanded. The interesting fact
is that the expansion is checked by Tau, including priority slices. The emergency
slice proves that emergency wins even if lower rows also match.

## Demo 2: Collateral Admission Reason Router

File:

```text
examples/tau/collateral_admission_reason_table_v1.tau
```

This table returns the first failed collateral-admission reason. It is useful for
explaining policies because the symbolic object carries both the decision shape
and the reason priority.

The solver checks the whole expansion and selected slices, including the case
where provenance is the first remaining failed check after registry, depth, and
age have passed.

## Demo 3: Incident Memory

File:

```text
examples/tau/incident_memory_table_v1.tau
```

This table is a symbolic state update:

```tau
table {
  when exploit_witness => st_update_tau(state,exploit_seed,exploit_region,exploit_region);
  when oracle_alarm => st_update_tau(state,oracle_seed,oracle_region,oracle_region);
  when governance_patch => st_revise_tau(state,patch_region,patch_label);
  when clear_oracle => st_select_tau(state,oracle_region');
  else => state
}
```

This is the closest public demo to the safe recursive-table semantics. The row
values are not fixed labels. They are formulas that transform an existing
symbolic state into a next symbolic state.

## Demo 4: Pointwise Revision

File:

```text
examples/tau/pointwise_revision_table_v1.tau
```

This demo is the direct table-update law:

```tau
table {
  when guard => replacement;
  else => old
}
```

The checked meaning is that the table preserves the old value outside `guard`,
uses `replacement` inside `guard`, and is idempotent when the same guard and
replacement are applied twice.

This is the important implementation move. A runtime does not need to store an
infinite table. It needs a finite symbolic revision rule that can be checked
pointwise.

## Demo 5: Qelim-Backed Policy Shapes

Command:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

This is a separate qelim-kernel demo. It does not run the table solver path.
Instead, it runs `qelim` commands whose formulas are shaped like the table
demos: priority ladders, collateral-reason routing, incident-memory updates,
pointwise revision, independent table shards, and DP-style guard constraints.
The printed residual formulas are checked by the scoped semantic validator, not
only by syntactic string comparison.

The current local receipt for the smooth wrapper is:

```text
cases:              9
repetitions:        5
semantic parity:     passed
syntactic fail, semantic pass: 2
auto route counts:   { components: 10, dp: 5, monolithic: 30 }
auto speedup:        5.150276 x
```

This makes the qelim optimization visible without overstating the table solver
claim. The `solve --tau` table demos currently emit no qelim telemetry, so this
demo is intentionally described as qelim-backed, not as table-runtime
acceleration.

## Demo 6: Table Solver Telemetry

Command:

```bash
python3 scripts/run_table_demo_solve_telemetry.py \
  --reps 3 \
  --out results/local/table-demo-solve-telemetry-reps3.json
```

This is the direct telemetry path for the ordinary table demos. It measures the
`solve --tau` command body with `TAU_SOLVE_STATS=1`.

The current local receipt is:

```text
cases:                 5
repetitions:           3
solve telemetry:       passed
dominant phase counts: { apply_ms: 5 }
```

Standard reading: every representative table-equivalence check emitted exactly
one solver telemetry row and returned `no solution`.

Plain English: the table demos are reaching Tau's solver correctly, but the
solver core is not the expensive part inside the measured command body.

Boundary: this does not prove a qelim speedup. It shows that current table-demo
optimization work should target rewrite-rule application and end-to-end command
loading before changing the solver core.

## Demo 7: Compound Table Check

Command:

```bash
python3 scripts/run_table_demo_compound_check.py \
  --reps 1 \
  --out results/local/table-demo-compound-check.json
```

This demo uses one compound mismatch query instead of fifteen separate
table-vs-raw solver calls.

The checked law is:

```text
unsat(diff_1 or ... or diff_n)
implies
unsat(diff_i) for every i.
```

The current local receipt is:

```text
checks:              15
individual elapsed:  118544.824 ms
compound elapsed:     53147.339 ms
elapsed reduction:       55.167%
```

The smooth demo runner now uses the compound-only path by default. The latest
fresh run of:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

produced:

```text
equivalence mode: compound
compound checks:  15
compound elapsed: 52894.501 ms
result:           passed
```

Standard reading: the disjunction of all table-vs-raw mismatch formulas has no
solution, so each individual mismatch formula also has no solution.

Plain English: the demo checks the same equivalence family in one larger Tau
query instead of repeatedly starting Tau and reloading the sources.

Boundary: this is not a new table operator. It is an obligation-shaping and
harness optimization for the public demo checks.

Proof receipt: the companion Lean packet
`tau_compound_table_check_2026_04_15` proves that unsatisfiability of the
compound mismatch predicate is equivalent to unsatisfiability of every listed
mismatch predicate. The packet is intentionally about the logical harness law,
not Tau's solver implementation.

## Demo 8: Batched Table Checks

Command:

```bash
python3 scripts/run_table_demo_batched_checks.py \
  --reps 1 \
  --out results/local/table-demo-batched-checks.json
```

Tau's CLI grammar accepts multiple commands in one input when each command
after the first is prefixed by a dot:

```text
cmd_1 . cmd_2 . ... . cmd_n
```

The current local receipt is:

```text
checks:              15
individual processes: 15
batched processes:     1
transport:          file
individual elapsed:  118534.210 ms
batched elapsed:      58227.056 ms
elapsed reduction:       50.877%
result:             passed
```

Standard reading: the batched run returned one `no solution` result for each of
the fifteen table-vs-raw mismatch obligations.

Plain English: this keeps the per-check audit trail while avoiding repeated Tau
startup and source loading.

Boundary: this is a CLI batching and demo-harness optimization. It does not
change Tau's solver, table semantics, or parser grammar. The command-file path
is opt-in behind `TAU_CLI_FILE_MODE=1`.

## Demo 9: RR Value-Inference Skip

Command:

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --reps 3 \
  --out results/local/rr-skip-value-infer-demo-reps3.json
```

This demo measures a feature-gated internal shortcut:

```bash
TAU_RR_SKIP_VALUE_INFER=1
```

The shortcut skips the second full type-inference pass for non-`spec`,
ref-valued command arguments that already passed parser-time type inference.

Current local receipt:

```text
checks:                       5
repetitions:                  3
output parity:                passed
baseline solve total:       261.038000 ms
skip solve total:            60.136580 ms
solve improvement:           76.963%
baseline get_rr:            209.216570 ms
skip get_rr:                  4.595369 ms
get_rr improvement:          97.804%
whole-process elapsed change: -0.343%
```

Standard reading: on the checked corpus, the skip branch returns the same
solver results while reducing measured command-body RR extraction time.

Plain English: Tau was typing an already-typed value a second time on this
path. The feature flag removes that redundant pass for the scoped branch.

Boundary: this is not a default Tau optimization. Whole-process elapsed time is
roughly flat because this wrapper is dominated by process startup and source
loading. Promotion would need a larger corpus and a proof or code invariant for
the parser-time typing premise.

Audit command:

```bash
python3 scripts/run_rr_skip_value_infer_demo.py \
  --audit \
  --reps 1 \
  --out results/local/rr-skip-value-infer-audit-reps1.json
```

Current audit receipt:

```text
audit rows:                    5
structurally equal audit rows: 5
```

The audit mode computes the full inference path and checks structural equality
against the skipped RR. It fails closed on mismatch and is not a timing mode.

## Boundary

These demos prove the patched Tau executable can parse and check a safe
guarded-choice table fragment. They do not prove unrestricted TABA tables,
same-stratum prime inside recursive rows, full NSO lowering, or full Guarded
Successor lowering. The qelim-backed policy-shape demo proves a separate kernel
optimization path, not a speedup of the current table solver checks. The solver
telemetry demo identifies a separate optimization surface for the ordinary
table checks. The compound table check shows one concrete way to reduce repeated
demo overhead without changing the semantics. The batched table check shows a
second way to reduce repeated overhead while preserving one solver result per
obligation. The RR value-inference skip shows an internal command-body
optimization candidate, not a default runtime claim.
