# Neuro-Symbolic Safe Table Programs

This spec defines a small executable suite for neuro-symbolic table programs.

The common contract is:

```text
neural proposer emits candidate rows
host checks convert observations into fixed lower-stratum guards
Tau table program classifies or revises each row
receipt records promoted, rejected, falsified, or deferred rows
```

The safety rule is the same one used by the safe infinite-table tutorial:

```text
T_next(i) = table { when G(i) => A(i); else => T_old(i) }
          = (G(i) & A(i)) | (G(i)' & T_old(i))
```

`G(i)` and `A(i)` are evidence tables computed before the recursive update.
They do not read the current same-stratum table state.

## Program Specs

| Program | Tau file | Neural role | Symbolic role |
| --- | --- | --- | --- |
| Counterexample Garden | `examples/tau/neuro_symbolic_research_tables_v1.tau` | Propose laws and counterexamples | Prioritize parse rejection, checked counterexamples, unsafe boundaries, checked proofs, and model-search rows |
| Frontier Weather | `examples/tau/neuro_symbolic_research_tables_v1.tau` | Propose search regions and near misses | Route compute to certify, expand, repair, prune, throttle, or observe |
| Proof Debt Ledger | `examples/tau/neuro_symbolic_research_tables_v1.tau` | Propose claims and replay artifacts | Classify claims as falsified, Lean debt, runtime debt, boundary debt, verified, or experimental |
| DeFi Lending Risk | `examples/tau/defi_lending_risk_table_v1.tau` | Propose risk alarms from monitors or LLM analysis | Route overlapping alarms to freeze, oracle quarantine, borrow pause, liquidation cap, governance review, allow, or deny |
| qNS Evidence Masks | `examples/tau/neuro_symbolic_qns_evidence_v1.tau` | Propose finite row masks and evidence masks | Use Tau `qns8` Boolean algebra to compute promoted, falsified, review, frontier, and DeFi action sets |

## Counterexample Garden

The table:

```tau
table {
  when parse_bad => reject_parse;
  when checked_counterexample => falsified;
  when unsafe_pattern => unsafe_boundary;
  when proof_checked => promoted;
  when needs_more_models => search_more;
  else => review
}
```

This makes failed ideas useful. A model may generate a false law, but if the
counterexample is checked, the row becomes boundary evidence instead of noise.

## Frontier Weather

The table:

```tau
table {
  when exact_witness => certify;
  when high_yield & high_cost' => expand;
  when near_miss => repair;
  when stale_low_yield => prune;
  when high_cost => throttle;
  else => observe
}
```

This is the search-allocation layer for depth-5 and deeper frontiers. The
neural side proposes where to search. GPU/Tau/Lean receipts determine which
regions deserve more compute.

## Proof Debt Ledger

The table:

```tau
table {
  when counterexample_found => falsified;
  when replay_ok & missing_lean => lean_debt;
  when replay_ok & missing_runtime => runtime_debt;
  when replay_ok & boundary_open => boundary_debt;
  when replay_ok => verified;
  else => experimental
}
```

This keeps experimental claims from being promoted beyond their evidence.

## DeFi Lending Risk

The table:

```tau
table {
  when exploit_witness => freeze_market;
  when oracle_divergence => quarantine_oracle;
  when solvency_gap => pause_borrow;
  when liquidation_cascade => cap_liquidation;
  when governance_override => governance_review;
  when healthy => allow;
  else => deny
}
```

The priority order is deliberate. If an exploit witness and a healthy signal
overlap, the exploit row wins. This is a safe-table policy example, not a live
financial risk engine.

## Experiment

Run:

```bash
python3 scripts/run_neuro_symbolic_table_programs.py
```

The runner checks:

- Tau table/raw equivalence for each table program.
- Priority slices for important overlapping-guard cases.
- Deterministic finite fixtures that model neural proposal rows.
- DeFi scenarios where overlapping alarms must resolve to the highest-priority
  safe action.

The default mode runs one Tau `solve --tau` command per obligation. A grouped
mode exists for profiling larger suites, but the individual mode is the
canonical demo of the Tau language surface.

Generated artifacts:

```text
results/local/neuro-symbolic-table-programs.json
results/local/neuro-symbolic-table-programs.md
```

Run the qNS evidence-mask lane with:

```bash
python3 scripts/run_neuro_symbolic_qns_experiment.py
```

Run the live local-LLM qNS lane with:

```bash
python3 scripts/run_neuro_symbolic_qns_llm_experiment.py --model qwen3.6:35b
```

In that path, Qwen proposes evidence bits for a fixed finite frontier. Tau qNS8
then computes the promoted, falsified, review, frontier, and DeFi action masks.
The model does not decide the final masks.

Generated artifacts:

```text
results/local/neuro-symbolic-qns-experiment.json
results/local/neuro-symbolic-qns-experiment.md
results/local/neuro-symbolic-qns-llm-experiment.json
results/local/neuro-symbolic-qns-llm-experiment.md
```

## Boundary

These examples do not trust model output. The neural system proposes rows and
candidate explanations. Tau checks the table programs and records the symbolic
decision shape. The examples are finite executable approximants of the safe
infinite-table pattern, not unrestricted TABA tables.
