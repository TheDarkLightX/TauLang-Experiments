# Tau Table Demo Examples

These examples are original experiment inputs. They are not copies of Tau
Language source code.

Run the demos with:

```bash
./scripts/run_table_demos.sh --accept-tau-license
```

Run the qelim-backed policy-shape demo with:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

Run the bounded game-table demo with:

```bash
./scripts/run_game_table_demo.sh --accept-tau-license
```

Run the finite qNS semantic Boolean-algebra demo with:

```bash
./scripts/run_qns_semantic_ba_demo.sh --accept-tau-license
```

Run the EML/qNS certificate demo with:

```bash
./scripts/run_eml_qns_demo.sh --accept-tau-license
```

## `full_style_taba_demo_v1.tau`

This is the main public demo. It uses Tau-native table syntax:

```tau
table {
  when G => V;
  else => D
}
```

The demo checks that this parsed table has the same meaning as the hand-written
guarded-choice expansion.

Breakthrough: the demo is no longer only JSON-side lowering or helper-function
syntax. Tau's parser accepts the feature-gated table syntax, and the solver
checks equivalence with the raw formula.

Boundary: this is safe guarded choice, not unrestricted TABA tables.

## `safe_table_kernel_builtins_v1.tau`

This file documents the helper surface loaded by the patch when
`TAU_ENABLE_SAFE_TABLES=1` is set.

It shows:

- fixed-guard select,
- fixed-guard revision,
- safe update,
- a checked idempotence shape for the demo update.

Boundary: the executable carrier is the four-cell finite carrier encoded in the
low four bits of `bv[8]`.

## `protocol_firewall_priority_ladder_v1.tau`

This demo shows overlapping guards with first-row priority. The table has rows
for emergency shutdown, exploit quarantine, oracle slowdown, liquidity caps,
governance review, normal allow, and default deny.

The public harness checks three facts:

- the table agrees with its exact raw guarded-choice expansion,
- the emergency row wins on the emergency slice, even if lower rows also match,
- the oracle row wins on the oracle slice after the earlier emergency and exploit
  guards are absent.

Why it is visually interesting: the table reads like a protocol firewall, while
the raw formula is a deeply nested Boolean expression. The solver proves they
mean the same thing.

## `collateral_admission_reason_table_v1.tau`

This demo turns collateral admission into a reason router. Instead of only
returning admit or deny, the table returns the first failed reason:

- registry failure,
- liquidity depth failure,
- age failure,
- provenance failure,
- governance separation failure,
- admit if no failure row matches.

The public harness checks that the table agrees with its raw expansion and that
the priority slices return the intended reason.

Why it is useful: a table can carry an explanation ladder. That is much clearer
than hiding the same logic inside one large formula.

## `incident_memory_table_v1.tau`

This demo shows rows whose values are state transformations, not just constants.
The table updates a symbolic incident-memory region:

- exploit witness writes an exploit region,
- oracle alarm writes an oracle region,
- governance patch revises a patch region,
- clear-oracle keeps the state outside the oracle region,
- default returns the previous state.

The public harness checks that the table agrees with its raw expansion and that
two row slices behave exactly as intended.

Why it matters: this is the small executable shape behind safe recursive tables.
A row can read the previous symbolic table state positively and construct the
next state.

## `pointwise_revision_table_v1.tau`

This demo shows the table-level update law directly. A table state is represented
as several named entries, and each entry is revised by the same local law:

```tau
table {
  when guard_i => replacement_i;
  else => old_i
}
```

The public harness checks:

- native table revision agrees with the runtime pointwise revision helper,
- the whole three-entry table revision has zero difference from its raw form,
- outside the guard, the old value is preserved,
- inside the guard, the replacement value is used,
- applying the same revision twice is the same as applying it once.

Why it matters: this is the executable shape that makes table updates finite and
symbolic. The implementation does not need to materialize infinitely many table
cells to express the update law.

## Qelim-backed policy-shape demo

This demo lives in the script layer rather than a `.tau` file:

```bash
./scripts/run_qelim_table_demos.sh --accept-tau-license
```

It runs `qelim` commands whose formulas mirror the table examples. The purpose
is to show that the experimental qelim backend has a visible, runnable table-
domain benchmark. It is not a claim that the current table solver checks use the
qelim backend.

## `post_agi_tokenomics_game_table_v1.tau`

This demo classifies a finite post-AGI tokenomics game surface. The agent can
contribute, extract, or exit. The protocol can reward, tax, or quarantine. The
table returns a symbolic classification such as safe Nash, unsafe extraction,
allowed but not equilibrium, or not desired.

The public harness checks the finite payoff model in Python and, when Tau is
available, checks that the Tau table syntax has the same meaning as the raw
guarded-choice expansion.

Boundary: this is a finite listed pure-strategy game. It is not mixed-strategy
game theory, continuous mechanism design, or an official Tau game-theory
feature.

## `qns_candidate_filter_v1.tau`

This demo uses feature-gated `qns8` and `qns64` Boolean algebras. The carriers
are finite powersets over audited atoms. In the main candidate-filter example,
each atom is a proposed action. In the concept and trace examples, the same
carrier shape is reused as a controlled-vocabulary concept set and as a bounded
trace-class quotient.

The public harness checks:

- native `qns8` and `qns64` meet, join, and prime-as-XOR-with-top behavior,
- exact Tau filtering of neural candidate masks through symbolic allow,
  review, and hard-reject masks,
- concept-set checks for missing requirements and risk hits,
- trace-class checks for safe, forbidden, and unclassified behavior.

Boundary: Tau does not compute the neural scores. Tau checks the exact symbolic
filtering step, and the host script renormalizes the surviving neural mass.

## Neuro-symbolic table programs

Files:

```text
examples/tau/neuro_symbolic_research_tables_v1.tau
examples/tau/defi_lending_risk_table_v1.tau
examples/tau/neuro_symbolic_qns_evidence_v1.tau
```

These examples turn neural proposal rows into safe symbolic table decisions:

- counterexample garden,
- frontier weather routing,
- proof debt ledger,
- DeFi lending risk routing.

Run them with:

```bash
python3 scripts/run_neuro_symbolic_table_programs.py
```

The runner checks table-vs-raw equivalence, priority slices, and deterministic
finite fixtures. The DeFi example is a policy-shape fixture only; it is not
financial advice or a live risk engine.

The qNS evidence-mask lane uses Tau `qns8` as the finite neuro-symbolic Boolean
algebra:

```bash
python3 scripts/run_neuro_symbolic_qns_experiment.py
```

The live local-LLM variant asks Qwen to assign evidence bits, then lets Tau qNS8
compute the exact masks:

```bash
python3 scripts/run_neuro_symbolic_qns_llm_experiment.py --model qwen3.6:35b
```

## EML/qNS certificate demo

This demo uses checked EML regression fixture artifacts outside Tau, then sends
finite evidence masks through Tau's `qns8` carrier. It verifies that all seven
valid certificates promote and all twenty-eight tampered certificates reject.

Boundary: Tau does not evaluate analytic EML expressions. Tau gates the finite
certificate masks that describe proof, holdout, residual, and review evidence.
