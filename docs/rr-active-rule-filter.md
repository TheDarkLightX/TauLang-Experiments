# RR Active Rule Filter

This note records the feature-gated recurrence-rewrite filter:

```bash
TAU_RR_ACTIVE_RULES=1
```

It is an internal Tau optimization experiment. It is not default Tau behavior.

## Scope

The pass runs inside `nso_rr_apply` when a list of recurrence-definition rules
is applied to a current term. It scans the current term for visible reference
signatures and skips definition rules whose left-hand reference signature is
not visible.

The surrounding rewrite loop still recomputes the active set on later passes.
This matters because one rewrite can introduce a reference that was not visible
in an earlier term.

## Candidate Law

For a term `t`, define:

```text
Refs(t) = the set of reference signatures occurring in t
```

For a rule `q`, define:

```text
Head(q) = the signature of the reference node in the left-hand side of q
```

when that reference node is recognizable.

The local law is:

```text
Head(q) notin Refs(t)
implies
apply(q, t) = t.
```

Standard reading: if the reference signature required by rule `q` is absent
from the current term `t`, then applying `q` to `t` does not change `t`.

Plain English: do not spend time trying a definition rule whose function symbol
does not occur in the expression currently being rewritten.

## Why The Law Is Only Local

The law says only that a rule cannot match the current term. It does not say
the rule is irrelevant forever.

It also does not imply one-pass equality with the ordinary sequential rule
pass. A rule skipped at the start of a pass can become applicable after an
earlier rule introduces its head reference. In that case, the active pass delays
the later rule until a later pass.

The loop-level obligation is:

```text
repeat_all(active_pass, t)
= repeat_all(full_pass, t).
```

That stronger statement needs more than the local nonmatch law. A proof would
need a fair delayed-scheduling argument plus a termination and confluence
argument for the relevant rule fragment, or a Tau-specific invariant that gives
the same result.

A useful intermediate invariant is:

```text
active_pass(t) = t
implies
full_pass(t) = t.
```

Standard reading: if no dynamically active rule can change the current term,
then no rule in the full library can change the current term.

Plain English: the filter may delay work, but it must not declare a term stable
while a skipped rule could still rewrite it.

This invariant depends on recomputing the active set at each pass. It should
not be proved by permanently pruning the rule library once at the start.

## Conservative Cases

The implementation keeps rules whose head reference cannot be recognized. This
is deliberate. Unknown rule shapes stay on the full path.

The current experiment also remains feature-gated because the local law still
needs a code-level proof or a checked invariant against Tau's exact rewriter
matching semantics.

## Current Receipt

Reproduce:

```bash
python3 scripts/run_rr_active_rules_batched.py \
  --reps 3 \
  --out results/local/rr-active-rules-batched-reps3.json
```

Current receipt, with `TAU_RR_SKIP_VALUE_INFER=1` and
`TAU_RR_TRANSFORM_DEFS_CACHE=1` enabled in both comparison modes:

```text
checks:                         15
output parity:                  passed
repetitions:                    3
active-rule rows:               135
rules before filter:            6750
rules after filter:              180
rules skipped:                  6570
solve improvement:              73.402%
rr_formula_rewrite improvement: 88.821%
elapsed improvement:            3.625%
```

Interpretation: the pass reduces internal recurrence-rewrite work sharply on
the batched table corpus. The three-repetition receipt also shows a small
whole-command speedup, but the internal rewrite and solve reductions are still
the main evidence.

## Ordinary Reference Corpus

The companion corpus avoids safe-table syntax:

```bash
python3 scripts/run_rr_active_rules_reference_corpus.py \
  --out results/local/rr-active-rules-reference-corpus.json
```

Current receipt:

```text
cases:                         9
output parity:                 passed
active-rule rows:              20
rules before filter:           34
rules after filter:            15
rules skipped:                 19
solve improvement:             0.736%
rr_formula_rewrite improvement: -45.847%
elapsed improvement:           0.326%
```

Interpretation: this is mostly boundary evidence. The filter preserves outputs
on ordinary named definitions, but the corpus is too small and rule-light for
the filter to help rewrite time. The useful claim remains narrower:
active-rule filtering helps when many definition rules are carried through a
batched solve path and most are irrelevant to the current term.

## Promotion Boundary

Do not promote this to default behavior until all of the following are true:

- the local nonmatch law is proved or encoded as a checked invariant against
  Tau's real matcher,
- fair delayed-scheduling soundness is proved for the relevant RR rewrite
  fragment, or the loop-level `repeat_all` equivalence is checked on a broader
  corpus with a proof plan,
- ordinary reference-definition corpora preserve outputs with the flag enabled,
- a larger in-process benchmark shows the internal rewrite reduction matters
  outside the safe-table demo corpus.
