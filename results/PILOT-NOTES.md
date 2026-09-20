# Pilot notes (exploratory, development tasks only, 2026-09-20)

All numbers below are from the 5 development tasks: 5 clean runs, 5 sham runs, 10 faulty runs (wrong_argument, wrong_source), each in 3 formats = 60 audit calls per pilot. Five runs per cell say nothing about which format is better; these pilots only check that the instrument works.

| Pilot folder | Auditor setting | Answers parsed | False alarms on the 15 clean audits | Exact step on the 30 faulty audits | Seconds per audit |
|---|---|---|---|---|---|
| `pilot-w3` | GLM, thinking off, first prompt | 100% | 15 of 15 | 22 of 30 | 11 |
| `pilot-w3b` | GLM, thinking off, prompt fix ("many runs are clean", analysis written first) | 97% | 11 of 15 | 19 of 30 | 16 |
| `pilot-w3c-think` | GLM, thinking on, 4,096 output tokens | 68% | 1 of 9 finished answers (6 of 15 never finished) | 20 of 23 finished answers (7 of 30 never finished) | 102 |

What this shows:
- Without thinking, the small auditor almost never says "this run is clean". The go/no-go rule ("returns none on most clean and sham runs") is not met.
- With thinking, the auditor is good when it finishes (8 of 9 clean runs called clean, 20 of 23 faults found), but in 19 of 60 calls the hidden reasoning ran into a loop until the token limit, and no answer came out. That breaks the 90 percent parse rule.
- `wrong_source` is found 5 of 5 times in every format with thinking off: a ceiling. The week-4 check must look at this fault.
- The truncation check (`record too long for num_ctx`) fired once, as designed: thinking with 8,192 output tokens does not fit next to a record in a 16,384 window.

Next: `pilot-w3d-qwen` (Qwen3.8 27B as auditor, thinking off), which is the plan's next step. It starts by itself when the clean runs are finished, because both models do not fit into memory together.
