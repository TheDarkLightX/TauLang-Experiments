# Qelim Epiplexity Routing Experiment

This note records a bounded experiment, not a production optimization claim.

Question:

```text
Can a cheap structure metric predict when the restricted KB qelim prepass is
worth running?
```

The experiment treats epiplexity as a routing signal. It asks where exploitable
structure is visible:

- in the source syntax,
- in the compiled qelim carrier,
- or not clearly enough to route.

## Command

```bash
python3 scripts/run_qelim_epiplexity_router.py \
  --max-generated-cases 34 \
  --reps 10 \
  --out results/local/qelim-epiplexity-router.json
```

The script runs four modes:

```text
auto
auto+kb_guarded
bdd
bdd+kb_guarded
```

It checks exact output parity against `auto`.

## Metric

The source metric parses the Boolean formula and looks for restricted KB
rewrite structure. Two detectors are recorded:

- `raw_syntax_detector`: any restricted source rewrite appears useful,
- `guard_aligned_detector`: the rewrite is aligned with the current Tau guarded
  KB implementation.

The important correction from this experiment is that raw source structure is
not always still available at the qelim prepass. For example, a double-negation
shape may be visible in the input text but already collapsed by the time the KB
guard sees the compiled expression.

## Current Receipt

Current local receipt:

```text
cases: 40
repetitions: 10
semantic parity: passed
```

Detector result for the implementation-aligned metric:

```text
true positives: 24
true negatives: 16
false positives: 0
false negatives: 0
```

Raw source detector result:

```text
true positives: 24
true negatives: 15
false positives: 1
false negatives: 0
```

The one raw false positive is the `double_neg` case. That is useful negative
knowledge: structure visible in source syntax can disappear before the current
guarded KB pass.

## Timing Result

Median-based routing regret on this corpus:

```text
auto lane regret: 0.854718 ms
bdd lane regret:  0.284027 ms
```

Sum-of-case-medians comparison:

```text
auto route: 16.055879 ms
auto base:  16.016488 ms
auto+KB:    15.945601 ms
oracle:     15.201161 ms

bdd route: 16.702219 ms
bdd base:  17.235192 ms
bdd+KB:    17.085916 ms
oracle:    16.418192 ms
```

Interpretation:

- The implementation-aligned metric is good at predicting whether the current
  guarded KB pass has structural work to do.
- The same metric is not yet strong enough to pick the fastest route in the
  already-composed `auto` lane.
- In the BDD sublane, the route improved against plain `bdd` on this corpus,
  but still had regret against the oracle that picks the locally fastest mode
  case by case.
- This supports keeping guarded KB opt-in and improving the selector before
  promoting it.

## Boundary

This is not a theorem that epiplexity optimizes qelim.

The checked part is semantic parity of the tested routes on the generated
corpus. The timing result is empirical. A stronger claim would need a formal
cost model, a larger corpus, and separate thresholds for syntax-visible
structure versus carrier-visible structure.
