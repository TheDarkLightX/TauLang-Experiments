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
  git -C "$TAU_DIR" apply "../../$patch"
done

echo "Applied ${#patches[@]} patch file(s)."
