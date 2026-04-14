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

for patch in "${patches[@]}"; do
  echo "Applying $patch"
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
