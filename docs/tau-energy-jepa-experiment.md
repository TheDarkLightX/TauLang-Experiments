# TauEnergy and TauJEPA Experiment

Project boundary: this is a community research prototype. It is not an official
IDNI or Tau Language feature, not an endorsement claim, and not a statement
about Tau Net production governance.

## Claim

A Tau-facing chatbot can be useful if the authority boundary is explicit:

```text
LLM interface -> proposes and explains
TauEnergy -> ranks candidate work items
TauJEPA -> ranks likely future failures
Tau or deterministic receipts -> decide syntax and semantic acceptance
```

TauEnergy can start as a deterministic linear baseline and later become a
trained EBRM over the same structured rows. The deterministic version is useful
because it gives reproducible labels, negative controls, and tests before a
neural scorer is introduced.

## What It Can Do

- Convert a user request into a semantic contract, Tau sketch task, witness
  schema task, receipt replay task, and repair list.
- Rank candidates so a tool checks the most receipt-ready item first.
- Rank stress scenarios such as grammar drift, stale training rows, missing
  witness fields, and authority overclaims.
- Build grammar-versioned synthetic data for a Tau-aware chat model.
- Turn broad Tau Net ideas into bounded experiment-lane proposals with receipt,
  rollback, and governance fields.

## Training Path

1. Snapshot the current Tau grammar files and compute a grammar hash.
2. Generate Tau-like syntax rows from semantic templates.
3. Keep rows only if the current Tau toolchain accepts them when a live parser
   is available.
4. Attach counterexamples, witness fields, command metadata, and receipt status.
5. Train TauEnergy on verifier-style labels such as `ready_for_tau_review`,
   `needs_repair`, `needs_current_grammar_check`, and
   `reject_authority_overclaim`.
6. Train a Tau-aware LLM on chat rows that preserve the same no-authority
   boundary.

If Tau syntax changes, the grammar hash changes. Synthetic rows tied to the old
hash become stale training data until regenerated and rechecked.

## Run

Build an advisory packet:

```bash
python3 scripts/run_tau_energy_copilot.py \
  --prompt "Let a user talk to a chatbot and draft Tau Net experiment proposals" \
  --export-dir results/local/tau-energy/packet
```

Build a training bundle:

```bash
python3 scripts/build_tau_energy_training_bundle.py \
  --out results/local/tau-energy/training_bundle.json
```

Export chat SFT rows:

```bash
python3 scripts/build_tau_llm_sft_dataset.py \
  --out results/local/tau-energy/tau_llm_sft.jsonl
```

## Non-Claims

- The chatbot does not execute Tau.
- TauEnergy does not accept proposals.
- TauJEPA does not verify future correctness.
- A custom LLM trained on Tau examples can still become stale after syntax
  changes.
- Tau Net production proposals require separate governance and deployment
  authority.
