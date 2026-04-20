# Game tables math v001

This Lean packet checks the bounded finite-game kernel used by the
post-AGI tokenomics game-table demo.

## Main theorem

```text
existsSafeNashCheck g safe desired profiles = true
iff
there exists p in profiles such that SafeNash g safe desired p
```

The theorem is exact relative to the listed players, listed candidate profiles,
and listed unilateral deviations supplied to the game object.

## Run

```bash
cd proofs/lean/game_tables_math_v001
lake env lean Proofs.lean
```

## Boundary

This is not mixed-strategy game theory, continuous game theory, or full
mechanism design. It proves the checker boundary used by the finite Tau demo.
