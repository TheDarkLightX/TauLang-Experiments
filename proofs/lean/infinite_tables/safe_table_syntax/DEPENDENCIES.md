# Dependencies

The safe-table syntax Lean packet imports Mathlib:

```lean
import Mathlib.Order.CompleteBooleanAlgebra
```

The checked development used a local Mathlib checkout through Lake. A fresh clone of this experiment repo needs one of the following before `lake build` will work:

- a `deps/mathlib4` checkout at the path expected by `lakefile.lean`, or
- an edited `lakefile.lean` that pulls Mathlib from the official Mathlib repository.

The proof claim is not based on an unchecked transcript. The local source packet built with `lake build`, and the generated report recorded return code `0` with no forbidden proof escapes found.

Current report summary:

```json
{
  "id": "v552",
  "returncode": 0,
  "forbidden": [],
  "theorem_count": 11,
  "claim": "Safe TABA table expressions with lower-stratum guards, positive current references, lower-prime, lower-guarded CBF conditionals, and explicit defaults denote monotone omega-continuous simultaneous updates with a fixed-point receipt."
}
```
