#!/usr/bin/env bash
set -euo pipefail

TAU_REPO_URL="${TAU_REPO_URL:-https://github.com/IDNI/tau-lang.git}"
TAU_DIR="${TAU_DIR:-external/tau-lang}"
TAU_REF="${TAU_REF:-f7423804bad14ea43a1e445088345a1ca715e845}"
ACCEPT_TAU_LICENSE="${ACCEPT_TAU_LICENSE:-}"

if [[ "${1:-}" == "--accept-tau-license" ]]; then
  ACCEPT_TAU_LICENSE=1
fi

if [[ "$ACCEPT_TAU_LICENSE" != "1" ]]; then
  cat <<'MSG' >&2
This script downloads Tau Language from the official IDNI repository.
Tau Language is governed by IDNI's license, not by this experiment repo.

This repo does not redistribute Tau source or binaries. It only supplies
research scripts, patch files, examples, and proof reports.

Rerun with:

  ./scripts/setup_tau.sh --accept-tau-license

or set:

  ACCEPT_TAU_LICENSE=1

after reviewing the Tau Language license.
MSG
  exit 2
fi

mkdir -p external

if [[ -d "$TAU_DIR/.git" ]]; then
  echo "Tau checkout already exists at $TAU_DIR"
  echo "Fetching latest refs..."
  git -C "$TAU_DIR" fetch --all --tags
else
  echo "Cloning official Tau Language repository into $TAU_DIR"
  git clone "$TAU_REPO_URL" "$TAU_DIR"
fi

echo "Checking out tested Tau ref: $TAU_REF"
git -C "$TAU_DIR" checkout "$TAU_REF"
echo "Initializing Tau submodules"
git -C "$TAU_DIR" submodule update --init --recursive

cat <<'MSG'

Tau Language was obtained from the official repository.
This experiment repo does not redistribute Tau source or binaries.
Review IDNI's Tau Language license before use.
MSG
