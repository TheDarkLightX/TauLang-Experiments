# Multi-character variable printing

Tau `fd536d56e00f12187cbed123c67a735a6964c660` can print a conjunction as a single variable when `charvar=false`.

[Download the reproduction package](charvar-printer-reproduction.zip). It contains the correction, an API regression, a standard-library Python checker, independently computed Boolean expectations, and recorded test results.

SHA-256: `ab264d5ddc1f57b8a5e54d290849ce26455ca69349d4a61d696c504deb53d327`.

The corrected build passed nine print-and-parse examples (48 Boolean assignments), four controls, the focused 30-assertion API test, and all 2,369 registered Release tests. The included README lists build dependencies, source pins, optional-test exclusions and limited combined-patch checks. These results apply to the pinned source; they do not establish correctness for every expression or build configuration.
