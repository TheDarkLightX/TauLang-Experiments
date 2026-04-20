# Neuro-Symbolic qNS LLM Experiment Receipt

Qwen proposes evidence bits for fixed rows. Tau qNS8 computes exact masks from those bits.

## Summary

| Metric | Value |
| --- | ---: |
| `model` | `qwen3.6:35b` |
| `tau_row_count` | `16` |
| `tau_rows_ok` | `true` |
| `research_rows` | `8` |
| `frontier_rows` | `8` |
| `defi_rows` | `8` |
| `ok` | `true` |

## Tau qNS Results

| Suite | Check | Actual names | Result |
| --- | --- | --- | --- |
| `llm_research_qns` | `promoted` | fixed_revision_law, safe_revision_packet | pass |
| `llm_research_qns` | `falsified` | current_guard_law, unrestricted_taba_claim | pass |
| `llm_research_qns` | `hard_reject` | malformed_claim | pass |
| `llm_research_qns` | `review` | arbitrary_select_law, depth5_region, runtime_lowering_gap | pass |
| `llm_research_qns` | `memory_revise_promoted` | fixed_revision_law, safe_revision_packet | pass |
| `llm_frontier_qns` | `certify` | depth4_ln_exact | pass |
| `llm_frontier_qns` | `expand` | depth5_guided_region | pass |
| `llm_frontier_qns` | `repair` | exp_exp_near_miss | pass |
| `llm_frontier_qns` | `prune` | cold_random_shard | pass |
| `llm_frontier_qns` | `throttle` | (none) | pass |
| `llm_defi_qns` | `freeze` | oracle_and_exploit_overlap | pass |
| `llm_defi_qns` | `quarantine_oracle` | oracle_divergence_only | pass |
| `llm_defi_qns` | `pause_borrow` | solvency_gap_with_healthy_flag, liquidation_cascade | pass |
| `llm_defi_qns` | `cap_liquidation` | (none) | pass |
| `llm_defi_qns` | `governance_review` | governance_override | pass |
| `llm_defi_qns` | `allow` | normal_market | pass |
