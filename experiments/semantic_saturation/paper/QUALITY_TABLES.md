# Validated heldout quality tables

Source: completed `heldout-001` run, validated analysis and validation JSON. All methods have 336 outcomes. W/T/L means hybrid wins/ties/losses against the named row. Costs are typed UTF-8 expression bytes.

| Method | Bytes | AST nodes | Structural DAG nodes | Changed accepted | Retained identity | Hybrid W/T/L |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Native reserialized | 49,361 | 7,982 | 3,777 | 332 | 4 | 102/234/0 |
| Native guarded | 19,705 | 3,342 | 2,497 | 279 | 57 | 102/234/0 |
| Rewrite guarded | 26,688 | 4,027 | 3,149 | 335 | 1 | 181/151/4 |
| Semantic root list | 19,173 | 3,256 | 2,446 | 280 | 56 | 94/242/0 |
| Scoped recursive congruence | 15,796 | 2,560 | 2,035 | 334 | 2 | 76/260/0 |
| Semantic graph without rewrites | 15,796 | 2,560 | 2,035 | 332 | 4 | 76/260/0 |
| Hybrid | 14,448 | 2,284 | 1,883 | 336 | 0 | 0/336/0 |
| Root-only hybrid | 14,933 | 2,372 | 1,938 | 336 | 0 | 18/309/9 |
| SymPy | 44,408 | 7,714 | 5,527 | 175 | 161 | 218/108/10 |
| Native + SymPy portfolio | 18,128 | 3,067 | 2,357 | 291 | 45 | 79/247/10 |

## Family totals

| Family | Cases | Native guarded | Native + SymPy | Recursive congruence | Hybrid | Hybrid vs portfolio W/T/L |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Random terms | 48 | 3,422 | 3,188 | 2,785 | 2,591 | 15/30/3 |
| Random formulas | 36 | 432 | 432 | 400 | 400 | 2/34/0 |
| Quantified random | 36 | 353 | 353 | 353 | 353 | 0/36/0 |
| Factoring composition | 48 | 2,837 | 2,503 | 2,326 | 1,853 | 11/37/0 |
| Multiplexer holdout | 48 | 3,917 | 3,015 | 3,622 | 3,293 | 7/35/6 |
| Parity holdout | 48 | 7,027 | 6,920 | 5,360 | 5,032 | 37/10/1 |
| Proper-split holdout | 36 | 1,633 | 1,633 | 866 | 842 | 7/29/0 |
| Mixed-quantifier holdout | 36 | 84 | 84 | 84 | 84 | 0/36/0 |

## Prespecified paired differences

Every median is zero. Intervals are 95% family-stratified bootstrap intervals for the mean on this synthetic corpus, with 2,000 fixed-seed resamples. They are not population generalization intervals.

| First arm minus second arm | Mean bytes | Median bytes | 95% interval for mean |
| --- | ---: | ---: | --- |
| Hybrid minus Root-only hybrid | -1.443 | 0 | [-3.185, -0.104] |
| Hybrid minus Native guarded | -15.646 | 0 | [-19.887, -11.753] |
| Hybrid minus Native + SymPy portfolio | -10.952 | 0 | [-14.839, -7.333] |
| Hybrid minus Scoped recursive congruence | -4.012 | 0 | [-5.048, -3.080] |
| Hybrid minus Semantic root list | -14.062 | 0 | [-17.670, -10.824] |
| Semantic graph without rewrites minus Scoped recursive congruence | 0.000 | 0 | [0.000, 0.000] |

## Descriptive component accounting

These are shared-transcript charges, not independent online method timings. Components are nested; columns must not be summed. The sum of per-case harness wall times was 633.586 seconds, with 10,148 native processes across the campaign.

| Method | Search seconds | Cold native charge seconds | Component-accounted seconds |
| --- | ---: | ---: | ---: |
| Native reserialized | 0.000 | 103.023 | 115.669 |
| Native guarded | 0.000 | 93.523 | 105.972 |
| Rewrite guarded | 6.821 | 45.073 | 59.638 |
| Semantic root list | 0.029 | 303.642 | 347.714 |
| Scoped recursive congruence | 1.712 | 302.754 | 348.610 |
| Semantic graph without rewrites | 1.493 | 302.826 | 348.470 |
| Hybrid | 30.032 | 302.279 | 376.474 |
| Root-only hybrid | 30.776 | 302.414 | 377.343 |
| SymPy | 73.667 | 51.292 | 126.133 |
| Native + SymPy portfolio | 73.667 | 129.005 | 216.148 |
