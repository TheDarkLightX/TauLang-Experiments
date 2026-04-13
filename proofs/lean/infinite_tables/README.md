# Infinite Tables Proof Index

This directory contains checked Lean proof packets for the scoped infinite-table semantics program.

## Current Packets

| Packet | Directory | Role |
| --- | --- | --- |
| A/B/C | `clopen_boolref_embedding/` | Embeds finite clopens into completed reference semantics and proves the `EventuallyOne` obstruction. |
| F/H | `kleene_stabilization/` | Proves Kleene fixed-point minimality and finite-stabilization agreement. |
| J | `unsafe_recurrence_boundary/` | Proves unrestricted same-stratum complement is not monotone and not omega-continuous. |

## Current Solved Claim

The checked packets support this scoped claim:

```text
finite executable clopen semantics embeds into completed reference semantics,
completed reference semantics can express countable recurrence unions,
finite stabilization agrees with the completed Kleene least fixed point,
and unrestricted same-stratum complement is excluded from the safe recurrence kernel.
```

## Not Yet Claimed

These packets do not yet prove unrestricted full TABA tables.

Open layers include:

```text
official table syntax adequacy
full NSO syntax
full Guarded Successor integration
full CBF fragment coverage
Tau runtime lowering
BDD canonicalization and optimization receipts
```

## Local Checking

Each packet is a standalone Lake project:

```bash
cd proofs/lean/infinite_tables/kleene_stabilization
lake build

cd ../clopen_boolref_embedding
lake build

cd ../unsafe_recurrence_boundary
lake build
```

A proof packet is accepted only if the Lean build passes and no proof escapes appear:

```text
sorry
admit
axiom
unsafe
sorryAx
```
