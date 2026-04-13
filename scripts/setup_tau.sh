#!/usr/bin/env bash
set -euo pipefail

TAU_REPO_URL="${TAU_REPO_URL:-https://github.com/IDNI/tau-lang.git}"
TAU_DIR="${TAU_DIR:-external/tau-lang}"

mkdir -p external

if [[ -d "$TAU_DIR/.git" ]]; then
  echo "Tau checkout already exists at $TAU_DIR"
  echo "Fetching latest refs..."
  git -C "$TAU_DIR" fetch --all --tags
else
  echo "Cloning official Tau Language repository into $TAU_DIR"
  git clone "$TAU_REPO_URL" "$TAU_DIR"
fi

cat <<'MSG'

Tau Language was obtained from the official repository.
This experiment repo does not redistribute Tau source or binaries.
Review IDNI's Tau Language license before use.
MSG
