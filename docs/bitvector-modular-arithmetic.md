# Fixed-Width Modular Arithmetic Experiment

This document records a small experiment for Tau's fixed-width bitvector
future-work lane. The goal is not to implement bitvectors in Tau. The goal is
to separate safe modular rewrites from tempting integer rewrites that fail
under overflow.

## Model

For width `w >= 1`, values are interpreted modulo `2^w`:

```text
bv_w(x) = x mod 2^w
```

The arithmetic operations are:

```text
add_w(x,y) = bv_w(x + y)
sub_w(x,y) = bv_w(x - y)
mul_w(x,y) = bv_w(x * y)
```

Standard reading:

- Every operation returns the representative of the result modulo `2^w`.

Plain English:

- Overflow is not an error in this model. Overflow wraps around.

## Runnable Corpus

Run:

```bash
python3 scripts/run_bitvector_modular_demo.py \
  --max-width 6 \
  --out results/local/bitvector-modular-demo.json
```

The script exhaustively checks small widths and records:

- safe rewrite laws that survive modulo arithmetic,
- counterexamples for integer-style rewrites that fail under overflow.

Safe examples include:

```text
add_w(x,0) = x
add_w(x,y) = add_w(y,x)
mul_w(x,1) = x
mul_w(x,0) = 0
shl_w(x,s) = mul_w(x,2^s)
not_w(not_w(x)) = x
```

Rejected examples include:

```text
x <= y does not imply add_w(x,z) <= add_w(y,z)
add_w(x,y) is not always >= x
mul_w(x,y) = mul_w(x,z) does not imply y = z
shr_w(shl_w(x,s),s) is not always x
```

These rejected laws are exactly the kind of rewrite hazards a Tau optimizer must
avoid when bitvectors enter normalization.

One nuance matters: an invalid rewrite does not need to fail at every width to
be unsafe. For example, one cancellation law has no counterexample at width 1,
but fails from width 2 onward. The corpus therefore requires safe laws to pass
at every tested width, while rejected laws only need a concrete counterexample
somewhere in the tested range.

## Boundary

This is a rewrite-triage corpus, not a Tau solver integration.

Promotion would require:

- a width-indexed semantics theorem,
- parser and CVC5-facing tests,
- constant-folding rules with proof receipts,
- negative tests for overflow-sensitive invalid rewrites.
