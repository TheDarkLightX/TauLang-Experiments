# Bounded game tables

This note records the first game-theory table experiment.

## Claim

The current claim is intentionally bounded:

```text
finite listed game + complete listed deviations + checked finite search
=> bounded safe-equilibrium demo
```

Standard reading. Given a finite listed game, if the listed deviations are the
deviations being modeled, then the checker decides whether the listed candidate
profiles contain a profile satisfying the safe-Nash predicate.

Plain English. The demo can check a small explicit mechanism game. It does not
solve general game theory.

## Mathematical kernel

The first Lean kernel proves:

```text
nashCheck g p = true iff Nash g p
```

and:

```text
existsSafeNashCheck g safe desired profiles = true
iff
there exists p in profiles such that SafeNash g safe desired p
```

The theorem is relative to the explicit lists in the game object. Missing
deviations are not inferred.

The lift proof adds a row-table and coverage bridge:

```text
table rows -> table-backed game functions -> listed-game checker
```

and:

```text
listed-game checker + profile/player/deviation coverage
=> intended-game safe equilibrium
```

Standard reading. If the profile returned by the checker is from the intended
profile set, every intended player is included in the player list, and every
intended unilateral deviation appears in the listed deviations, then a checked
listed safe Nash result is also safe Nash for the intended bounded game.

Plain English. The proof separates the solver from the model-building
obligation. The checker can be correct even when the input model is incomplete,
so coverage must be stated and checked separately.

The pruning proof adds an optimization law:

```text
certified profitable deviation
=> not Nash
```

and:

```text
pruning profiles with certified profitable deviations
preserves safe-equilibrium existence
```

Standard reading. If a profile has a listed allowed unilateral deviation whose
payoff is strictly greater for the deviating player, then the profile does not
satisfy the listed Nash predicate. Removing only profiles certified by that
condition does not change whether the remaining listed profile set contains a
safe Nash profile.

Plain English. The solver can skip strategically impossible profiles when it
has explicit profitable-deviation evidence.

## Demo model

The demo uses a small post-AGI tokenomics fixture:

- agent actions: `contribute`, `extract`, `exit`,
- protocol actions: `reward`, `tax`, `quarantine`,
- one unsafe profile: `extract/reward`,
- one desired safe equilibrium: `contribute/reward`.

The Python model checks the finite payoff table. The Tau example checks that the
table syntax lowers to the same guarded-choice expression as the raw formula.

Run:

```bash
./scripts/run_game_table_demo.sh --accept-tau-license
```

For the Python-only model check:

```bash
python3 scripts/run_game_table_demo.py
```

Proof receipts:

```bash
cd proofs/lean/game_tables_math_v001
lake env lean Proofs.lean

cd ../game_tables_lift_v001
lake env lean Proofs.lean

cd ../game_tables_dominance_pruning_v001
lake env lean Proofs.lean
```

## Boundary

This is not a claim about mixed strategies, continuous games, incomplete
information, mechanism-design optimality, or full TABA tables. The first useful
feature is a finite table surface that can classify bounded strategic profiles
with proof-backed checker semantics.
