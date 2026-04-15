# Table Demo Gallery

Project boundary: this is a community research prototype.
It is not an official IDNI or Tau Language table implementation, not an
endorsement claim, and not a statement about what IDNI intends to ship.
The demos are narrower than full TABA tables and may not meet the standard
required for an official Tau feature.

Run every demo with:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

The script clones official Tau Language, applies the local experiment patch,
regenerates the parser, builds Tau, and runs the solver checks. The demo suite
does not require committing Tau Language source into this repository.

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

## Boundary

These demos prove the patched Tau executable can parse and check a safe
guarded-choice table fragment. They do not prove unrestricted TABA tables,
same-stratum prime inside recursive rows, full NSO lowering, or full Guarded
Successor lowering.
