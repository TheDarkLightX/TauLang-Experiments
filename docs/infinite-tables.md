# Infinite Tables

The current working distinction is:

```text
finite executable lane
  embeds into
completed reference semantics
```

The finite executable lane is suitable for running examples and extracting witnesses. The completed reference semantics is needed for recurrence behavior that forms countable suprema.

## Core Theorems To Track

- Finite clopens embed into the completed reference carrier.
- The completed reference carrier represents countable unions.
- Finite clopens cannot represent every countable recurrence union, for example `EventuallyOne`.
- Monotone omega-continuous recurrence has a Kleene least fixed point.
- If finite iteration stabilizes, the completed least fixed point equals the finite stabilized iterate.
- Same-stratum complement is not monotone and must be stratified or separately proved safe.

## Boundary

This does not automatically prove unrestricted full TABA tables. It proves the semantic spine needed for a scoped infinite-table solution.
