# qNS semantic BA v001

This Lean packet checks the finite powerset formulas used by the qNS semantic
Boolean-algebra demo.

## Main theorems

```text
unsafeLeak u n allowed review hardReject = bottom
```

Standard reading. The meet of auto-accepted candidates with hard-rejected
candidates is the empty carrier.

```text
partition u n allowed review hardReject = proposed u n
```

Standard reading. The join of auto-accept, human-review, and symbolic-reject
regions is exactly the proposed region inside the universe.

## Run

```bash
cd proofs/lean/qns_semantic_ba_v001
lake env lean Proofs.lean
```

## Boundary

This proves the formula-level finite powerset semantics. It does not prove the
C++ parser, the bit-mask implementation, neural scoring, or correctness of an
LLM atom extractor.
