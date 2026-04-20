# Neuro-Symbolic Table Program Receipt

This receipt runs deterministic proposal fixtures through safe table specifications and checks the Tau table/raw equivalence obligations.

## Summary

| Metric | Value |
| --- | ---: |
| `tau_check_count` | `13` |
| `tau_group_count` | `13` |
| `tau_mode` | `individual` |
| `tau_checks_ok` | `true` |
| `fixture_suite_count` | `4` |
| `fixture_rows` | `19` |
| `fixture_suites_ok` | `true` |
| `ok` | `true` |

## Grouped Tau Obligations

| Source | Checks | Result | Last line |
| --- | ---: | --- | --- |
| `(individual mode)` | 0 | n/a | n/a |

## Tau Checks

| Check | Source | Result | Last line |
| --- | --- | --- | --- |
| `counterexample_garden_table_agrees_with_raw` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `counterexample_garden_counterexample_priority` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `counterexample_garden_proof_slice` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `frontier_weather_table_agrees_with_raw` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `frontier_weather_exact_priority` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `frontier_weather_expand_slice` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `proof_debt_ledger_table_agrees_with_raw` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `proof_debt_ledger_falsified_priority` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `proof_debt_ledger_verified_slice` | `examples/tau/neuro_symbolic_research_tables_v1.tau` | pass | `no solution` |
| `defi_lending_action_table_agrees_with_raw` | `examples/tau/defi_lending_risk_table_v1.tau` | pass | `no solution` |
| `defi_lending_exploit_priority` | `examples/tau/defi_lending_risk_table_v1.tau` | pass | `no solution` |
| `defi_lending_oracle_slice` | `examples/tau/defi_lending_risk_table_v1.tau` | pass | `no solution` |
| `defi_lending_allow_slice` | `examples/tau/defi_lending_risk_table_v1.tau` | pass | `no solution` |

## Fixture Suites

| Suite | Rows | Result |
| --- | ---: | --- |
| `counterexample_garden` | 5 | pass |
| `frontier_weather` | 5 | pass |
| `proof_debt_ledger` | 4 | pass |
| `defi_lending_risk` | 5 | pass |

## DeFi Examples

| Scenario | Decision |
| --- | --- |
| `oracle_and_exploit_overlap` | `freeze_market` |
| `oracle_divergence_only` | `quarantine_oracle` |
| `solvency_gap_with_healthy_flag` | `pause_borrow` |
| `liquidation_cascade` | `cap_liquidation` |
| `normal_market` | `allow` |
