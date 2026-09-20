# Compute log (replaces the USD budget; planned API spend is 0)

Machine: Apple M4 Pro, 48 GB RAM. Runtime: Ollama 0.33.2. Model: `glm-4.7-flash:q8_0` (decision D-003).

## Measured so far

| Date | What | Input | Output | Wall time |
|---|---|---|---|---|
| 2026-09-20 | probe: agent turn 1, model cold | 439 tokens at 493/s | 56 tokens at 45/s | 26.8 s (24.6 s of it is model load) |
| 2026-09-20 | probe: auditor, 1,785-token log | 567/s | 40 tokens at 39/s | 4.2 s |
| 2026-09-20 | smoke test: agent tool call | 246 tokens at 514/s | 39 tokens at 46/s | 12.0 s (includes load) |
| 2026-09-20 | smoke test: auditor JSON | 164 tokens at 402/s | 34 tokens at 43/s | 1.2 s |

Memory: 32 GB loaded, 100% on the GPU at `num_ctx` 16384.
Rule of thumb from these numbers: reading about 500 tokens per second, writing about 45 tokens per second.

## The three machine-hour lines (gate: 60 machine-hours in total, plan section 4)

| Line | Calls | Seconds per call | Machine-hours |
|---|---|---|---|
| Generation: clean runs (up to 120) plus 300 continuations | to be measured in week 2 (plan section 3, steps 3 and 6) | | rough guess 10-15 |
| Sweep audits: 1,380 calls, plus 180 second-auditor calls | to be measured in week 3 (step 7) | | rough guess 8-12 |
| Development: probe, pilot, 18 validation continuations, re-audits, re-generation | | | rough guess 3-5 |

The guesses assume records of about 10,000 tokens. Record length is not measured yet.
