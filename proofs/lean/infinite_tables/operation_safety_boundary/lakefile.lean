import Lake
open Lake DSL

package «operation_safety_boundary» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

require mathlib from "../../../../../deps/mathlib4"

@[default_target]
lean_lib Proofs
