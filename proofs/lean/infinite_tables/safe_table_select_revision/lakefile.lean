import Lake
open Lake DSL

package «safe_table_select_revision» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

require mathlib from "../../../../../deps/mathlib4"

@[default_target]
lean_lib Proofs
