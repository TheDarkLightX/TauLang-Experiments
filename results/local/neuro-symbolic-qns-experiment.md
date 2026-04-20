# Neuro-Symbolic qNS Experiment Receipt

This experiment uses Tau qNS8 finite Boolean algebra. Neural proposal rows are represented as bits; Tau computes exact promoted, falsified, review, frontier, and DeFi action masks.

## Summary

| Metric | Value |
| --- | ---: |
| `suite_count` | `3` |
| `row_count` | `16` |
| `rows_ok` | `true` |
| `ok` | `true` |

## Checks

| Suite | Check | Actual names | Result |
| --- | --- | --- | --- |
| `research_qns` | `promoted` | fixed_revision_law, safe_revision_packet | pass |
| `research_qns` | `falsified` | current_guard_law, unrestricted_taba_claim | pass |
| `research_qns` | `hard_reject` | malformed_claim | pass |
| `research_qns` | `review` | arbitrary_select_law, depth5_region, runtime_lowering_gap | pass |
| `research_qns` | `memory_revise_promoted` | fixed_revision_law, safe_revision_packet | pass |
| `frontier_qns` | `certify` | depth4_ln_exact | pass |
| `frontier_qns` | `expand` | depth5_guided_region | pass |
| `frontier_qns` | `repair` | exp_exp_near_miss | pass |
| `frontier_qns` | `prune` | cold_random_shard | pass |
| `frontier_qns` | `throttle` | expensive_proof_lane | pass |
| `defi_qns` | `freeze` | oracle_and_exploit_overlap | pass |
| `defi_qns` | `quarantine_oracle` | oracle_divergence_only | pass |
| `defi_qns` | `pause_borrow` | solvency_gap_with_healthy_flag | pass |
| `defi_qns` | `cap_liquidation` | liquidation_cascade | pass |
| `defi_qns` | `governance_review` | governance_override | pass |
| `defi_qns` | `allow` | normal_market | pass |
