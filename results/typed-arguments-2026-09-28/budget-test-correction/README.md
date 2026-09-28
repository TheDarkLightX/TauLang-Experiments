# Explicit finite limit for the ten-step completion test

Proposed test-only correction for [Tau issue #194](https://github.com/IDNI/tau-lang/issues/194).
It changes the successful ten-step test to use a limit of 4,096 and fail if a
size-limit diagnostic appears. The production default remains 2,000. This does
not make the original command finish at the default limit or improve the solver.

Apply `budget-completion-test.patch` to Tau
`8b5a61ca98a72f0a2cbece9b1338c7295482bbd3`, reconfigure, and run:

```sh
ctest --test-dir build/release --output-on-failure --timeout 30 \
  -R '^test_repl-(run_cmd-value.*constant_size_budget|get_cmd-maxconstantsize_default_finite)$'
```

The included `CMakeLists.txt` also allows checking just those three declarations
with an already-built executable. Supply absolute paths:

```sh
cmake -S . -B check -DTAU=/path/to/tau -DTAU_SOURCE=/path/to/tau-lang
ctest --test-dir check --output-on-failure --timeout 30
```

This uses the upstream CTest helper and test input files. The recorded three
checks pass on the rename-only Release executable described in #194: default
limit 2,000, expected stop-at-limit diagnostic, and ten completed steps with the
explicit limit. The original default-limit completion test still fails. The
existing unit tests cover the simplification of repeated and absorbed disjuncts.

This is a targeted test correction verified on macOS 26.6.2 arm64 with Clang
22.1.2 and cvc5 1.3.1. It does not establish Linux coverage or a new full-suite
pass. The issue contains the complete original reproduction and environment.
