cmake_minimum_required(VERSION 3.22)
project(budget_check NONE)
enable_testing()
set(TAU_EXECUTABLE_NAME tau_under_test)
add_executable(tau_under_test IMPORTED)
set_target_properties(tau_under_test PROPERTIES IMPORTED_LOCATION "${TAU}")
list(APPEND CMAKE_MODULE_PATH "${TAU_SOURCE}/tests/repl")
include(add_repl_test)
set(TF "${TAU_SOURCE}/tests/integration/test_files")
set(A2J "${TF}/tau-named_a_to_j-length_10.in")
add_repl_test(get_cmd-maxconstantsize_default_finite "get maxconstantsize" "maxconstantsize: *2000")
add_repl_test_fail(run_cmd-value_past_constant_size_budget
	"i1:tau := in file(\\\"${TF}/tau-nonzero_a1_to_a10-length_10.in\\\"). o1:tau := out console. run 10 steps always (o1[t] != o1[t-1] && o1[t] != 0 && o1[t] != 1 && o1[t] != i1[t])."
	"o1\\[6\\] := .*passed the constant size budget")
# Complete ten steps with simplified Tau constants under an explicit finite
# limit. The default limit can stop this sequence earlier; the preceding
# test separately checks that the default limit reports an incomplete run.
add_repl_test(run_cmd-values_stay_within_constant_size_budget
	"set maxconstantsize 4096. i1:tau := in file(\\\"${A2J}\\\"). o1:tau := out console. run 10 steps always (o1[t] != o1[t-1] && o1[t] != 0 && o1[t] != 1 && o1[t] != i1[t])."
	"o1\\[9\\] := ")
set_tests_properties("test_repl-run_cmd-values_stay_within_constant_size_budget"
    PROPERTIES FAIL_REGULAR_EXPRESSION "Error|passed the constant size budget")
