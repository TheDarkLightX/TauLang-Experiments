#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAU_DIR="${TAU_DIR:-"$ROOT/external/tau-lang"}"
BUILD_DIR="${TAU_BUILD_DIR:-"$TAU_DIR/build-Release"}"
TAU_BIN="${TAU_BIN:-"$BUILD_DIR/tau"}"
RESULT_DIR_ARG="${RESULT_DIR:-results/local/tau-energy}"
JOBS="${JOBS:-2}"
ACCEPT_FLAG=""
MODE="quick"

usage() {
  cat <<'MSG' >&2
Usage: ./scripts/run_tau_energy_training_demo.sh [--accept-tau-license] [--quick|--full]

This script obtains Tau Language through scripts/setup_tau.sh when needed.
Tau Language is governed by IDNI's license, not by this experiment repo.
MSG
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --accept-tau-license)
      ACCEPT_FLAG="--accept-tau-license"
      shift
      ;;
    --quick)
      MODE="quick"
      shift
      ;;
    --full)
      MODE="full"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ "$RESULT_DIR_ARG" == /* ]]; then
  RESULT_DIR_PATH="$RESULT_DIR_ARG"
else
  RESULT_DIR_PATH="$ROOT/$RESULT_DIR_ARG"
fi
mkdir -p "$RESULT_DIR_PATH"
cd "$ROOT"

if [[ "${TAU_ENERGY_DEMO_SKIP_SETUP_PATCH:-0}" != "1" ]]; then
  "$ROOT/scripts/setup_tau.sh" $ACCEPT_FLAG
  "$ROOT/scripts/apply_patches.sh"
else
  echo "Skipping Tau setup and patch application; using existing checkout."
fi

if [[ ! -x "$TAU_BIN" ]]; then
  cmake -S "$TAU_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
fi
cmake --build "$BUILD_DIR" --target tau -j "$JOBS"

if [[ "$MODE" == "full" ]]; then
  MEASURED_EXAMPLES="${TAU_ENERGY_MEASURED_EXAMPLES:-250}"
  STRESS_EXAMPLES="${TAU_ENERGY_STRESS_EXAMPLES:-120}"
  STRESS_SEEDS=(${TAU_ENERGY_STRESS_SEEDS:-20260522 20260523 20260524})
  BDD_BASE_EXAMPLES="${TAU_ENERGY_BDD_BASE_EXAMPLES:-120}"
  BDD_POOL_EXAMPLES="${TAU_ENERGY_BDD_POOL_EXAMPLES:-96}"
  BDD_TRAIN_SIZES=(${TAU_ENERGY_BDD_TRAIN_SIZES:-0 2 4 8 16 32})
  REAL_SPEC_LIMIT="${TAU_ENERGY_REAL_SPEC_LIMIT:-4}"
else
  MEASURED_EXAMPLES="${TAU_ENERGY_MEASURED_EXAMPLES:-80}"
  STRESS_EXAMPLES="${TAU_ENERGY_STRESS_EXAMPLES:-40}"
  STRESS_SEEDS=(${TAU_ENERGY_STRESS_SEEDS:-20260522 20260523})
  BDD_BASE_EXAMPLES="${TAU_ENERGY_BDD_BASE_EXAMPLES:-48}"
  BDD_POOL_EXAMPLES="${TAU_ENERGY_BDD_POOL_EXAMPLES:-36}"
  BDD_TRAIN_SIZES=(${TAU_ENERGY_BDD_TRAIN_SIZES:-0 4 8 16})
  REAL_SPEC_LIMIT="${TAU_ENERGY_REAL_SPEC_LIMIT:-2}"
fi

echo "== TauEnergy optimizer workbench =="
python3 "$ROOT/scripts/run_tau_optimizer_workbench.py" \
  --tau-bin "$TAU_BIN" \
  --out "$RESULT_DIR_ARG/optimizer_workbench.json" \
  --timeout-s "${TAU_ENERGY_OPT_TIMEOUT_S:-120}"
python3 "$ROOT/scripts/run_tau_optimizer_workbench.py" \
  --verify "$RESULT_DIR_ARG/optimizer_workbench.json"
echo

echo "== TauEnergy measured route training ($MODE) =="
python3 "$ROOT/scripts/train_tau_measured_fragment_energy.py" \
  --tau-bin "$TAU_BIN" \
  --examples "$MEASURED_EXAMPLES" \
  --real-spec-limit "$REAL_SPEC_LIMIT" \
  --tau-timeout-s "${TAU_ENERGY_TAU_TIMEOUT_S:-10}" \
  --route-timeout-s "${TAU_ENERGY_ROUTE_TIMEOUT_S:-10}" \
  --out "$RESULT_DIR_ARG/measured_fragment_training_report.json"
python3 "$ROOT/scripts/train_tau_measured_fragment_energy.py" \
  --verify "$RESULT_DIR_ARG/measured_fragment_training_report.json"
echo

echo "== TauEnergy stress report ($MODE) =="
python3 "$ROOT/scripts/stress_tau_measured_fragment_energy.py" \
  --tau-bin "$TAU_BIN" \
  --examples-per-seed "$STRESS_EXAMPLES" \
  --seeds "${STRESS_SEEDS[@]}" \
  --real-spec-limit "$REAL_SPEC_LIMIT" \
  --tau-timeout-s "${TAU_ENERGY_TAU_TIMEOUT_S:-10}" \
  --route-timeout-s "${TAU_ENERGY_ROUTE_TIMEOUT_S:-10}" \
  --out "$RESULT_DIR_ARG/measured_fragment_stress_report.json"
python3 "$ROOT/scripts/stress_tau_measured_fragment_energy.py" \
  --verify "$RESULT_DIR_ARG/measured_fragment_stress_report.json"
echo

echo "== TauEnergy ordered-BDD curriculum ($MODE) =="
python3 "$ROOT/scripts/train_tau_ordered_bdd_curriculum.py" \
  --tau-bin "$TAU_BIN" \
  --base-examples "$BDD_BASE_EXAMPLES" \
  --bdd-pool-examples "$BDD_POOL_EXAMPLES" \
  --bdd-train-sizes "${BDD_TRAIN_SIZES[@]}" \
  --real-spec-limit "$REAL_SPEC_LIMIT" \
  --tau-timeout-s "${TAU_ENERGY_TAU_TIMEOUT_S:-10}" \
  --route-timeout-s "${TAU_ENERGY_ROUTE_TIMEOUT_S:-10}" \
  --out "$RESULT_DIR_ARG/ordered_bdd_curriculum_report.json"
python3 "$ROOT/scripts/train_tau_ordered_bdd_curriculum.py" \
  --verify "$RESULT_DIR_ARG/ordered_bdd_curriculum_report.json"
echo

echo "== TauEnergy public site snapshot =="
python3 "$ROOT/scripts/build_tau_energy_site_snapshot.py" \
  --optimizer "$RESULT_DIR_ARG/optimizer_workbench.json" \
  --measured "$RESULT_DIR_ARG/measured_fragment_training_report.json" \
  --stress "$RESULT_DIR_ARG/measured_fragment_stress_report.json" \
  --bdd "$RESULT_DIR_ARG/ordered_bdd_curriculum_report.json" \
  --out "$RESULT_DIR_ARG/public_site_snapshot.json"
python3 "$ROOT/scripts/build_tau_energy_site_snapshot.py" \
  --verify "$RESULT_DIR_ARG/public_site_snapshot.json"

if [[ "${TAU_ENERGY_UPDATE_SITE_ASSET:-0}" == "1" ]]; then
  python3 "$ROOT/scripts/build_tau_energy_site_snapshot.py" \
    --optimizer "$RESULT_DIR_ARG/optimizer_workbench.json" \
    --measured "$RESULT_DIR_ARG/measured_fragment_training_report.json" \
    --stress "$RESULT_DIR_ARG/measured_fragment_stress_report.json" \
    --bdd "$RESULT_DIR_ARG/ordered_bdd_curriculum_report.json" \
    --out "$ROOT/docs/assets/tau-energy-demo-summary.json"
fi
echo

python3 "$ROOT/scripts/demo_tau_energy_training_results.py" \
  --optimizer "$RESULT_DIR_ARG/optimizer_workbench.json" \
  --measured "$RESULT_DIR_ARG/measured_fragment_training_report.json" \
  --stress "$RESULT_DIR_ARG/measured_fragment_stress_report.json" \
  --bdd "$RESULT_DIR_ARG/ordered_bdd_curriculum_report.json"

echo
echo "TauEnergy training demo passed."
RESULT_LABEL="$RESULT_DIR_ARG"
if [[ "$RESULT_LABEL" == "$ROOT/"* ]]; then
  RESULT_LABEL="${RESULT_LABEL#"$ROOT/"}"
fi
echo "Results are under $RESULT_LABEL."
