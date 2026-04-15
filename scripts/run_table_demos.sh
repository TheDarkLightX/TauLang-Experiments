#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAU_DIR="${TAU_DIR:-"$ROOT/external/tau-lang"}"
BUILD_DIR="${TAU_BUILD_DIR:-"$TAU_DIR/build-Release"}"
JOBS="${JOBS:-2}"
ACCEPT_FLAG=""
TABLE_DEMO_EQUIV_MODE="${TABLE_DEMO_EQUIV_MODE:-compound}"

if [[ "${1:-}" == "--accept-tau-license" ]]; then
  ACCEPT_FLAG="--accept-tau-license"
fi

case "$TABLE_DEMO_EQUIV_MODE" in
  compound|individual) ;;
  *)
    echo "Unsupported TABLE_DEMO_EQUIV_MODE=$TABLE_DEMO_EQUIV_MODE" >&2
    echo "Use TABLE_DEMO_EQUIV_MODE=compound or TABLE_DEMO_EQUIV_MODE=individual." >&2
    exit 2
    ;;
esac

if [[ "${TAU_TABLE_DEMO_SKIP_SETUP_PATCH:-0}" != "1" ]]; then
  "$ROOT/scripts/setup_tau.sh" $ACCEPT_FLAG
  "$ROOT/scripts/apply_patches.sh"
else
  echo "Skipping Tau setup and patch application; using existing checkout."
fi

if [[ ! -x "$BUILD_DIR/tau" ]]; then
  cmake -S "$TAU_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
fi
cmake --build "$BUILD_DIR" --target tau -j "$JOBS"

TAU_BIN="${TAU_BIN:-"$BUILD_DIR/tau"}"
RESULT_DIR="${RESULT_DIR:-"$ROOT/results/local"}"
mkdir -p "$RESULT_DIR"

clean_output() {
  sed -E 's/\x1b\[[0-9;]*m//g'
}

expect_no_solution() {
  local name="$1"
  shift
  local out
  out="$("$@" 2>&1 | clean_output)"
  printf '%s\n' "$out" > "$RESULT_DIR/${name}.txt"
  if [[ "$(printf '%s\n' "$out" | tail -n 1)" != "no solution" ]]; then
    echo "FAILED: $name" >&2
    printf '%s\n' "$out" >&2
    exit 1
  fi
  echo "passed: $name"
}

expect_rejected_without_flag() {
  local name="$1"
  shift
  local out
  out="$("$@" 2>&1 | clean_output || true)"
  printf '%s\n' "$out" > "$RESULT_DIR/${name}.txt"
  if ! printf '%s\n' "$out" | grep -Eq "Syntax Error|Parsing constant|Incompatible or absent type information"; then
    echo "FAILED: $name" >&2
    printf '%s\n' "$out" >&2
    exit 1
  fi
  echo "passed: $name"
}

tau_source() {
  sed '/^[[:space:]]*#/d' "$1"
}

expect_tau_file_no_solution() {
  local name="$1"
  local file="$2"
  local check="$3"
  local src
  src="$(tau_source "$ROOT/$file")
$check"
  expect_no_solution \
    "$name" \
    env TAU_ENABLE_SAFE_TABLES=1 "$TAU_BIN" --charvar false \
      -e "$src" \
      --severity info --color false --status true
}

TABLE_SRC="$(tau_source "$ROOT/examples/tau/full_style_taba_demo_v1.tau")"
TABLE_CHECK="$TABLE_SRC
solve --tau (priority_quarantine_update(q,riskgate,reviewgate,depguard,seed,manualadd) != priority_quarantine_raw(q,riskgate,reviewgate,depguard,seed,manualadd))"

expect_no_solution \
  "safe_table_idempotence" \
  env TAU_ENABLE_SAFE_TABLES=1 "$TAU_BIN" --charvar false \
    -e "solve --tau (st_update_tau(st_update_tau(q,b,g,a),b,g,a) != st_update_tau(q,b,g,a))" \
    --severity info --color false --status true

expect_no_solution \
  "finite_carrier_update" \
  env TAU_ENABLE_SAFE_TABLES=1 "$TAU_BIN" --charvar false \
    -e "solve --bv !(st_update4({ #x03 }:bv[8], { #x01 }:bv[8], { #x02 }:bv[8], { #x04 }:bv[8]) = { #x01 }:bv[8])" \
    --severity info --color false --status true

expect_no_solution \
  "finite_carrier_pointwise_revision" \
  env TAU_ENABLE_SAFE_TABLES=1 "$TAU_BIN" --charvar false \
    -e "solve --bv !(st_pointwise_revise4({ #x01 }:bv[8], { #x02 }:bv[8], { #x02 }:bv[8]) = { #x03 }:bv[8])" \
    --severity info --color false --status true

if [[ "$TABLE_DEMO_EQUIV_MODE" == "compound" ]]; then
  (
    cd "$ROOT"
    python3 scripts/run_table_demo_compound_check.py \
      --tau-bin "$TAU_BIN" \
      --mode compound-only \
      --out "$RESULT_DIR/table-demo-compound-check.json"
  ) > "$RESULT_DIR/table-demo-compound-check.txt"
  echo "passed: compound_table_equivalence_check"
else
  expect_no_solution \
    "tau_native_table_agrees_with_raw" \
    env TAU_ENABLE_SAFE_TABLES=1 "$TAU_BIN" --charvar false \
      -e "$TABLE_CHECK" \
      --severity info --color false --status true

  expect_tau_file_no_solution \
    "protocol_firewall_table_agrees_with_raw" \
    "examples/tau/protocol_firewall_priority_ladder_v1.tau" \
    "solve --tau (protocol_firewall_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != protocol_firewall_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny))"

expect_tau_file_no_solution \
  "protocol_firewall_emergency_priority" \
  "examples/tau/protocol_firewall_priority_ladder_v1.tau" \
  "solve --tau (protocol_firewall_emergency_slice_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != protocol_firewall_emergency_slice_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny))"

expect_tau_file_no_solution \
  "protocol_firewall_oracle_slice" \
  "examples/tau/protocol_firewall_priority_ladder_v1.tau" \
  "solve --tau (protocol_firewall_oracle_slice_table(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny) != protocol_firewall_oracle_slice_raw(emergency,exploit,oracle,liquidity,governance,normal,freeze,quarantine,slow,cap,review,allow,deny))"

expect_tau_file_no_solution \
  "collateral_reason_table_agrees_with_raw" \
  "examples/tau/collateral_admission_reason_table_v1.tau" \
  "solve --tau (collateral_reason_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != collateral_reason_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit))"

expect_tau_file_no_solution \
  "collateral_reason_registry_priority" \
  "examples/tau/collateral_admission_reason_table_v1.tau" \
  "solve --tau (collateral_registry_priority_slice_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != collateral_registry_priority_slice_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit))"

expect_tau_file_no_solution \
  "collateral_reason_provenance_slice" \
  "examples/tau/collateral_admission_reason_table_v1.tau" \
  "solve --tau (collateral_provenance_slice_table(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit) != collateral_provenance_slice_raw(registry_bad,depth_bad,age_bad,provenance_bad,separation_bad,deny_registry,deny_depth,deny_age,deny_provenance,deny_separation,admit))"

expect_tau_file_no_solution \
  "incident_memory_table_agrees_with_raw" \
  "examples/tau/incident_memory_table_v1.tau" \
  "solve --tau (incident_memory_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != incident_memory_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label))"

expect_tau_file_no_solution \
  "incident_memory_exploit_priority" \
  "examples/tau/incident_memory_table_v1.tau" \
  "solve --tau (incident_memory_exploit_slice_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != incident_memory_exploit_slice_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label))"

expect_tau_file_no_solution \
  "incident_memory_clear_slice" \
  "examples/tau/incident_memory_table_v1.tau" \
  "solve --tau (incident_memory_clear_slice_table(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label) != incident_memory_clear_slice_raw(state,exploit_witness,oracle_alarm,governance_patch,clear_oracle,exploit_region,oracle_region,patch_region,exploit_seed,oracle_seed,patch_label))"

expect_tau_file_no_solution \
  "pointwise_revision_entry_agrees_with_helper" \
  "examples/tau/pointwise_revision_table_v1.tau" \
  "solve --tau (pointwise_revise_entry(old,guard,replacement) != pointwise_revise_entry_raw(old,guard,replacement))"

expect_tau_file_no_solution \
  "pointwise_revision_whole_table_agrees" \
  "examples/tau/pointwise_revision_table_v1.tau" \
  "solve --tau (pointwise_revision_diff(old_mint,old_borrow,old_liquidate,guard_mint,guard_borrow,guard_liquidate,replacement_mint,replacement_borrow,replacement_liquidate) != 0)"

expect_tau_file_no_solution \
  "pointwise_revision_outside_guard_preserves_old" \
  "examples/tau/pointwise_revision_table_v1.tau" \
  "solve --tau (pointwise_revision_outside_guard(old,guard,replacement) != pointwise_revision_outside_guard_raw(old,guard,replacement))"

expect_tau_file_no_solution \
  "pointwise_revision_inside_guard_uses_replacement" \
  "examples/tau/pointwise_revision_table_v1.tau" \
  "solve --tau (pointwise_revision_inside_guard(old,guard,replacement) != pointwise_revision_inside_guard_raw(old,guard,replacement))"

  expect_tau_file_no_solution \
    "pointwise_revision_idempotent" \
    "examples/tau/pointwise_revision_table_v1.tau" \
    "solve --tau (pointwise_revision_twice(old,guard,replacement) != pointwise_revision_once(old,guard,replacement))"
fi

expect_rejected_without_flag \
  "tau_native_table_rejected_without_flag" \
  env -u TAU_ENABLE_SAFE_TABLES "$TAU_BIN" --charvar false \
    -e "$TABLE_CHECK" \
    --severity info --color false --status true

cat > "$RESULT_DIR/table-demo-summary.txt" <<'MSG'
Tau table demos passed.

Checked:
- safe symbolic table update is idempotent on the checked formula
- finite four-cell carrier update matches the expected low-bit result
- finite four-cell carrier pointwise revision matches the expected low-bit result
- Tau-native table syntax agrees with its raw guarded-choice expansion
- priority firewall table agrees with its raw expansion
- priority firewall slices prove first-row priority under overlapping guards
- collateral admission table returns the first failed reason
- incident memory table applies state-transforming rows correctly
- pointwise revision table entries agree with the runtime helper
- pointwise revision preserves old values outside the guard
- pointwise revision uses replacement values inside the guard
- pointwise revision is idempotent for the same guard and replacement
- the table syntax is rejected when TAU_ENABLE_SAFE_TABLES is absent

Scope:
- safe guarded-choice tables only
- no unrestricted TABA recurrence
- no same-stratum prime
- no full NSO or Guarded Successor lowering
MSG

cat >> "$RESULT_DIR/table-demo-summary.txt" <<MSG

Equivalence mode:
- $TABLE_DEMO_EQUIV_MODE
MSG

RESULT_LABEL="$RESULT_DIR"
if [[ "$RESULT_LABEL" == "$ROOT/"* ]]; then
  RESULT_LABEL="${RESULT_LABEL#"$ROOT/"}"
fi

echo "Tau table demos passed. Results written to $RESULT_LABEL"
