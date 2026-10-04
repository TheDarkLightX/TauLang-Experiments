# Timing limitation retained

The study execution log reported concurrent rendering of three Matplotlib quality
figures at approximately 2026-10-04 04:48:53.5–04:49:01.5 UTC, with a tool-reported
duration of 8.9 seconds. The rounded endpoints span 8.0 seconds and are not a more
precise duration estimate.

Filesystem receipt and run-index mtimes place this overlap within
rep-1/formula-25-25-50 (first native receipt 04:48:37.336516 UTC; run index
04:49:08.041491 UTC). Raw receipt persistence may lag measured request completion,
so no finer request/arm attribution is asserted.

All fixed repetitions and requests remain in the result. Nothing was excluded,
repeated, or tuned. Frozen source and protocol were unchanged. Native call counts
and exact candidate/certificate behavior are primary; small timing differences
between signature-bank indexing and its redundant semantic-decision memo should
not be overinterpreted. See TIMING_NOTE.json for structured provenance.
