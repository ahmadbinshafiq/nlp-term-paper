# Main run (sweep pool, N = 50 tasks), finished 2026-09-22 05:27

Chain (started after the tag `prereg-v1`): 300 faulty runs + 20 sham runs generated -> leak test and round trip green ->
GLM audited all 345 runs x 3 formats (second auditor, 3.7 h) -> Qwen audited them (primary auditor, 16.1 h) -> `analysis/analyze.py`.

- `scores.csv`: 2,070 rows (1,035 per auditor). Columns: `analysis/schema.md`.
- `analysis_primary.md`: the pre-registered analysis with the primary auditor. **Label: "refuted: another interaction".**
- `analysis_second.md`: the same tables for the second auditor (description only).
- `primary_input_*.csv`, `primary_test_*.csv`: the rows and the R output of the interaction test.
- `cache-after-sweep.zip`: every raw model answer, in case the cache folder is ever lost.

Headline (Qwen, exact step found, 50 runs per cell):

| fault type | log | diff | prov |
|---|---|---|---|
| wrong_argument | 0.88 | 0.84 | 0.92 |
| corrupted_output | 0.48 | 0.52 | 0.48 |
| dropped_note | **0.48** | **0.86** | **0.86** |
| overwritten_note | 1.00 | 1.00 | 1.00 |
| wrong_source | 1.00 | 1.00 | 1.00 |
| no_source | 0.94 | 0.90 | 0.94 |

The interaction is significant (p < 0.0001), but it comes from one cell: a dropped note is found far less often in the event log.
In 17 of the 26 misses in the log the auditor said "no fault", in 8 it named another step, and in 1 its answer was cut off. The other two classes show no format difference; the evidence class is at the ceiling.
