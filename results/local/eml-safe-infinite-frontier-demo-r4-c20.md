# EML Safe Infinite-Frontier Table Receipt

This is the table-native reading of the scaled Qwen/MLX run.
It treats the finite candidate frontier as a prefix of a countable candidate stream.

## Summary

| Metric | Value |
| --- | ---: |
| `finite_prefix_rows` | `86` |
| `approximant_count` | `5` |
| `promoted_rows` | `4` |
| `review_rows` | `82` |
| `rejected_rows` | `82` |
| `tau_frontier_table_check_ok` | `true` |
| `source_receipt_ok` | `true` |
| `row_gate_ok` | `true` |
| `ok` | `true` |

## Safe Table Reading

Candidate indices live in an infinite stream. This run only materializes a finite prefix.

For each candidate index `i`, the executable frontier update is:

```text
T_next(i) = table { when G(i) => A(i); else => T_old(i) }
          = (G(i) & A(i)) | (G(i)' & T_old(i))
```

`G` and `A` are fixed lower-stratum evidence tables from parsing, numeric checks, review status, and the qNS Tau gate. They do not read the current recursive table state.

## Approximants

| Stage | Frontier | Rows | Screened | Promoted | Review | Rejected | Prefix | Support |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | MLX depth-4 GPU frontier | 3 | 2089472 | 1 | 2 | 2 | 3 | 1 |
| 2 | Qwen 3.6 sweep round 1 | 28 | 29 | 3 | 25 | 25 | 31 | 4 |
| 3 | Qwen 3.6 sweep round 2 | 17 | 30 | 0 | 17 | 17 | 48 | 4 |
| 4 | Qwen 3.6 sweep round 3 | 20 | 30 | 0 | 20 | 20 | 68 | 4 |
| 5 | Qwen 3.6 sweep round 4 | 18 | 20 | 0 | 18 | 18 | 86 | 4 |

## Proof Bridge

| Artifact | Role | Present |
| --- | --- | --- |
| `docs/infinite-tables.md` | finite executable lane embeds into completed reference semantics | true |
| `docs/safe-table-select-revision.md` | pointwise revision law and fixed-guard discipline | true |
| `proofs/lean/infinite_tables/CURRENT_STATUS.md` | checked monotone omega-continuous safe table syntax status | true |
| `proofs/lean/infinite_tables/safe_table_select_revision/README.md` | select/revision packet for fixed guards and replacement tables | true |
| `/Users/danax/projects/Formal_Methods_Philosophy/tutorials/safe-infinite-tables-in-tau-language.md` | tutorial framing for safe infinite-recursive table approximants | true |

## Tau Witness

- Source: `examples/tau/eml_safe_infinite_frontier_table_v1.tau`
- Universal table/raw equivalence check: `no solution`
- OK: `true`

## Final Nonzero Rows

| Candidate index | Mask | Evidence atoms |
| ---: | ---: | --- |
| 1 | `0x3F` | proposed, parse_ok, domain_ok, train_fit, holdout_fit, memory_update_ready |
| 3 | `0x3F` | proposed, parse_ok, domain_ok, train_fit, holdout_fit, memory_update_ready |
| 13 | `0x3F` | proposed, parse_ok, domain_ok, train_fit, holdout_fit, memory_update_ready |
| 21 | `0x3F` | proposed, parse_ok, domain_ok, train_fit, holdout_fit, memory_update_ready |
