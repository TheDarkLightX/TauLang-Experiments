import Lake
open Lake DSL

package «safe_table_syntax_packet» where

require mathlib from "../../../../../deps/mathlib4"

@[default_target]
lean_lib Proofs where
  roots := #[`Proofs]
