# Lean Proofs

This directory is for Lean proof packets and checked receipts used by the TauLang experiments.

Recommended structure:

```text
proofs/lean/finite_tables/
proofs/lean/infinite_tables/
proofs/lean/qelim/
proofs/lean/boundaries/
```

Acceptance rule:

A proof is not accepted unless it builds locally and contains no proof escapes:

```text
sorry
admit
axiom
unsafe
sorryAx
```

Every proof packet should include a short README explaining:

- exact theorem statement
- assumptions
- non-claims
- checker command
- relationship to Tau experiments
