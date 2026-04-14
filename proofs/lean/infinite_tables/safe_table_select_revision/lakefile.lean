import Lake
open Lake DSL

package «safe_table_select_revision» where
  leanOptions := #[
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.25.0-rc2"

@[default_target]
lean_lib Proofs
