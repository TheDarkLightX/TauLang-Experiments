#!/usr/bin/env bash
set -euo pipefail

TAU_DIR="${TAU_DIR:-external/tau-lang}"
PATCH_DIR="${PATCH_DIR:-patches}"

if [[ ! -d "$TAU_DIR/.git" ]]; then
  echo "Missing Tau checkout at $TAU_DIR" >&2
  echo "Run ./scripts/setup_tau.sh first." >&2
  exit 1
fi

shopt -s nullglob
patches=("$PATCH_DIR"/*.patch)

if [[ ${#patches[@]} -eq 0 ]]; then
  echo "No patch files found in $PATCH_DIR."
  exit 0
fi

patch_present() {
  local patch_name="$1"
  case "$patch_name" in
    0001-taba-safe-tables-and-qelim-demo.patch)
      [[ -f "$TAU_DIR/src/boolean_algebras/finite_table_ba.h" ]] &&
      grep -q "safe_table_expr" "$TAU_DIR/parser/tau.tgf" &&
      grep -q "safe_table_ba_enabled" "$TAU_DIR/src/finite_table_builtins.h"
      ;;
    0002-qns-candidate-ba.patch)
      [[ -f "$TAU_DIR/src/boolean_algebras/qns_candidate_ba.h" ]] &&
      grep -q "qns64_ba" "$TAU_DIR/src/runtime.h" &&
      grep -q "TAU_ENABLE_QNS_BA" "$TAU_DIR/src/boolean_algebras/qns_candidate_ba.h"
      ;;
    *)
      return 1
      ;;
  esac
}

for patch in "${patches[@]}"; do
  echo "Applying $patch"
  if patch_present "$(basename "$patch")"; then
    echo "Already present: $patch"
    continue
  fi
  if git -C "$TAU_DIR" apply --reverse --check "../../$patch" >/dev/null 2>&1; then
    echo "Already applied: $patch"
    continue
  fi
  git -C "$TAU_DIR" apply --check "../../$patch"
  git -C "$TAU_DIR" apply "../../$patch"
done

echo "Applied ${#patches[@]} patch file(s)."

if [[ -x "$TAU_DIR/parser/gen" && -f "$TAU_DIR/parser/tau.tgf" ]]; then
  echo "Regenerating Tau parser from patched grammar"
  (cd "$TAU_DIR" && ./parser/gen parser/tau.tgf)
fi
