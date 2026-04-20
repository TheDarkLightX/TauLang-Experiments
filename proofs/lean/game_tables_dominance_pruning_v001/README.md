# Game tables dominance pruning v001

This proof packet checks a finite game-table optimization.

## What is proved

If a profile has a listed allowed unilateral deviation with strictly higher
payoff for a listed player, then that profile is not Nash. Therefore profiles
certified by that evidence may be pruned before safe-Nash search.

Main theorem shape:

```text
prune profiles with certified profitable deviations
preserves existsSafeNashCheck
```

## Run

```bash
cd proofs/lean/game_tables_dominance_pruning_v001
lake env lean Proofs.lean
```

## Boundary

This is finite listed pure-strategy pruning. It is not mixed-strategy dominance
or continuous mechanism-design optimization.
