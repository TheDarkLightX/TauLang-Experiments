# Game tables lift v001

This proof packet extends the bounded game-table demo with a table-lowering
receipt.

## What is proved

The packet proves:

- first-match row-table lookup soundness,
- missing-key default lookup soundness,
- table-backed safe-equilibrium search exactness,
- a coverage bridge from listed-game checking to intended-game semantics.

The important coverage theorem separates two claims:

```text
the checker is correct for the listed game
```

from:

```text
the listed profiles, players, and deviations faithfully cover the intended game
```

Both are needed before interpreting a finite game-table result as a statement
about an intended mechanism.

## Run

```bash
cd proofs/lean/game_tables_lift_v001
lake env lean Proofs.lean
```

## Boundary

This is finite listed pure-strategy game semantics. It does not claim mixed
strategies, continuous action spaces, incomplete information, or full mechanism
design.
