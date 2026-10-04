#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != '--accept-tau-license' ]]; then
  printf '%s\n' 'Review https://github.com/IDNI/tau-lang/blob/7625580db1a54e0b55beaf753566c137df42fe66/LICENSE.md before use.' 'Rerun with --accept-tau-license to fetch and build official Tau for research.' >&2
  exit 2
fi
for tool in git cmake g++ gcc python3; do
  command -v "$tool" >/dev/null || { printf 'Missing build tool: %s\n' "$tool" >&2; exit 2; }
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TAU_DIR="${TAU_DIR:-$REPO/external/tau-semantic-saturation}"
DEPS="${TAU_SHARED_PREFIX:-$REPO/external/tau-semantic-dependencies}"
REF=7625580db1a54e0b55beaf753566c137df42fe66
mkdir -p "$(dirname "$TAU_DIR")" "$DEPS"
if [[ -e "$TAU_DIR" ]]; then
  [[ -d "$TAU_DIR/.git" ]] || { echo 'Existing destination is not a Git checkout.' >&2; exit 2; }
  [[ "$(git -C "$TAU_DIR" rev-parse HEAD)" == "$REF" ]] || { echo 'Existing checkout has another revision; choose a fresh TAU_DIR.' >&2; exit 2; }
  [[ -z "$(git -C "$TAU_DIR" status --porcelain)" ]] || { echo 'Existing checkout is modified; choose a fresh TAU_DIR.' >&2; exit 2; }
else
  git clone --no-checkout https://github.com/IDNI/tau-lang.git "$TAU_DIR"
  git -C "$TAU_DIR" checkout --detach "$REF"
fi
git -C "$TAU_DIR" submodule update --init --recursive
[[ "$(git -C "$TAU_DIR/external/parser" rev-parse HEAD)" == cdcc0f7e9bba21cce518405693ca55e75f292e3e ]]
cd "$TAU_DIR"
./dev dep-boost.sh -DTAU_BUILD_JOBS=1 -DTAU_SHARED_PREFIX="$DEPS"
./dev preset release-tau -DCMAKE_C_COMPILER="$(command -v gcc)" -DCMAKE_CXX_COMPILER="$(command -v g++)" \
  -DTAU_BAS=sbf,tau -DTAU_DONT_USE_FTXUI=ON -DTAU_LTO=OFF -DTAU_ARTIFACT_PREINST=OFF \
  -DTAU_BUILD_JOBS=1 -DTAU_SHARED_PREFIX="$DEPS"
./build/release/tau --version
sha256sum ./build/release/tau
printf 'Native executable: %s/build/release/tau\n' "$TAU_DIR"
