# Frozen online reuse results

All 30 runs and 7,680 arm-requests completed; offline verification passed for 8,892 native processes. No UNKNOWN verdicts or cross-arm candidate/status mismatches occurred. All frozen repetitions remain visible.

## Certificate result

Each cached arm used 1,812 native processes and 822 exact certificate hits. No-cache used 3,456 processes. Every new equivalent syntax and fresh syntax still required two native processes. Thus semantic-registry lookup saved zero native calls beyond ordinary exact syntax/result memoization. Unsupported context cases rejected before native work; supported reordered/renamed contexts received separate certificates.

## Cost and attribution

Aggregate measured arm wall times: no-cache 195.365970 s; exact syntax 121.813380 s; fixed-bank signatures 91.103770 s; semantic registry 90.859502 s. Campaign wall time before final serialization was 543.826316 s, including 0.694243 s separate stream-label validation. Arm clocks exclude outer JSON orchestration/serialization, which explains part of the difference from campaign wall time.

The substantial formula-selection savings against exact-pair scanning are fixed-bank signature amortization/indexing. The semantic decision memo has the same fixed menu as the signature-index control and is redundant with its lookup. Its aggregate difference from that control is−0.244269 s across 30 runs, with mixed per-stream/per-repetition directions; this is not evidence of additional native reuse or a distinct semantic mechanism.

Concurrent figure rendering overlapped repetition 1/formula-25-25-50. See TIMING_NOTE.md. Small timing rankings must not be overinterpreted.

## Every stream and repetition

Times are cumulative cold-start seconds at request 64. A break-even point is the first request after which registry cost stayed strictly below the named baseline through request 64; “none” means no observed sustained break-even within this stream. It is not an extrapolation. Full 64-point curves are in summary.json.

| Rep | Stream | No cache s | Exact s | Index s | Registry s | Registry−exact s | Registry−index s | Point vs exact | Point vs index |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | term_tau-100-0-0 | 4.504668 | 0.089796 | 0.085951 | 0.091125 | +0.001329 | +0.005173 | none | none |
| 1 | term_tau-50-50-0 | 4.989254 | 2.813727 | 2.806074 | 2.781371 | -0.032356 | -0.024703 | 46 | 58 |
| 1 | term_tau-25-25-50 | 5.759521 | 4.724158 | 4.699729 | 4.723641 | -0.000517 | +0.023912 | 64 | none |
| 1 | term_tau-0-0-100 | 6.809449 | 6.747491 | 6.646825 | 6.694578 | -0.052913 | +0.047754 | 11 | none |
| 1 | term_tau-context-safety | 2.294883 | 0.299178 | 0.303958 | 0.299959 | +0.000780 | -0.003999 | none | 1 |
| 1 | formula-100-0-0 | 7.235794 | 0.142248 | 0.133685 | 0.126202 | -0.016046 | -0.007483 | 1 | 1 |
| 1 | formula-50-50-0 | 8.596192 | 5.082162 | 3.379823 | 3.386901 | -1.695261 | +0.007078 | 1 | none |
| 1 | formula-25-25-50 | 9.524414 | 7.984761 | 5.081404 | 5.005645 | -2.979116 | -0.075759 | 1 | 7 |
| 1 | formula-0-0-100 | 12.260995 | 12.164499 | 6.885135 | 6.845052 | -5.319447 | -0.040083 | 1 | 1 |
| 1 | formula-context-safety | 3.494242 | 0.436896 | 0.414459 | 0.413939 | -0.022957 | -0.000521 | 1 | 20 |
| 2 | term_tau-100-0-0 | 4.394402 | 0.086675 | 0.082954 | 0.082697 | -0.003977 | -0.000256 | 1 | 54 |
| 2 | term_tau-50-50-0 | 4.804952 | 2.725494 | 2.654078 | 2.685553 | -0.039941 | +0.031474 | 38 | none |
| 2 | term_tau-25-25-50 | 5.743181 | 4.717199 | 4.649463 | 4.646664 | -0.070535 | -0.002798 | 1 | 19 |
| 2 | term_tau-0-0-100 | 6.714750 | 6.662561 | 6.636459 | 6.637911 | -0.024650 | +0.001451 | 5 | none |
| 2 | term_tau-context-safety | 2.254690 | 0.297466 | 0.290179 | 0.288623 | -0.008844 | -0.001556 | 1 | 2 |
| 2 | formula-100-0-0 | 7.117384 | 0.131287 | 0.129248 | 0.119780 | -0.011507 | -0.009468 | 1 | 1 |
| 2 | formula-50-50-0 | 8.326600 | 4.929396 | 3.272936 | 3.274912 | -1.654484 | +0.001976 | 1 | none |
| 2 | formula-25-25-50 | 9.457449 | 7.821352 | 4.982178 | 4.974215 | -2.847137 | -0.007963 | 1 | 51 |
| 2 | formula-0-0-100 | 12.622772 | 12.597533 | 7.060163 | 7.103248 | -5.494284 | +0.043085 | 1 | none |
| 2 | formula-context-safety | 3.464285 | 0.438100 | 0.413651 | 0.412953 | -0.025147 | -0.000698 | 1 | 9 |
| 3 | term_tau-100-0-0 | 4.402839 | 0.090409 | 0.086917 | 0.085038 | -0.005372 | -0.001879 | 1 | 42 |
| 3 | term_tau-50-50-0 | 4.877808 | 2.720317 | 2.697054 | 2.675710 | -0.044607 | -0.021344 | 10 | 1 |
| 3 | term_tau-25-25-50 | 5.621894 | 4.665009 | 4.601278 | 4.590294 | -0.074716 | -0.010984 | 11 | 42 |
| 3 | term_tau-0-0-100 | 6.708644 | 6.749209 | 6.677550 | 6.591232 | -0.157976 | -0.086317 | 1 | 4 |
| 3 | term_tau-context-safety | 2.301217 | 0.295707 | 0.314334 | 0.292839 | -0.002868 | -0.021496 | 3 | 1 |
| 3 | formula-100-0-0 | 7.016892 | 0.131358 | 0.145757 | 0.118915 | -0.012443 | -0.026842 | 1 | 1 |
| 3 | formula-50-50-0 | 8.341834 | 4.963048 | 3.308383 | 3.303705 | -1.659343 | -0.004677 | 1 | 60 |
| 3 | formula-25-25-50 | 9.522933 | 8.027750 | 5.038223 | 5.000032 | -3.027718 | -0.038191 | 3 | 31 |
| 3 | formula-0-0-100 | 12.615880 | 12.768010 | 7.202270 | 7.160816 | -5.607194 | -0.041454 | 1 | 24 |
| 3 | formula-context-safety | 3.586152 | 0.510583 | 0.423655 | 0.445952 | -0.064630 | +0.022298 | 1 | none |

## Scope

The data concern a finite synthetic three-variable 0/1 atomless-BA fixed-bank workload. “Fresh” is syntax novelty, not promised semantic novelty. Per-stream class counts and per-category call/hit counts are in ANALYSIS.json. Raw commands, argv, stdout, stderr, exits, timeouts, support observations, exact context/profile identities and receipt hashes remain in the result tree. Verification establishes internal consistency against those retained receipts, not independent authenticity of recorded runtime clocks or external native execution provenance.
