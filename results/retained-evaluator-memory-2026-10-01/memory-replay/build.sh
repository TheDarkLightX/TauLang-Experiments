#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -e tau-source ]]; then
  echo 'Use a fresh extraction: tau-source already exists.' >&2
  exit 1
fi
git clone https://github.com/IDNI/tau-lang.git tau-source
git -C tau-source checkout --detach a739b90259729590dee7b424df05ba65bfdeacf2
git -C tau-source submodule update --init external/parser
git -C tau-source/external/parser checkout --detach 5b14b6fde86f16dc52c4c0a953a8a1e53c88f95a
git -C tau-source apply ../memory-evaluator.patch
git -C tau-source/external/parser apply ../../../parser-scratch.patch
if [[ $(uname -s) == Darwin ]]; then
  git -C tau-source apply ../macos-build.patch
fi
cd tau-source
./dev preset release-tests -DTAU_LTO=OFF -DTAU_ARTIFACT_PREINST=ON "$@"
