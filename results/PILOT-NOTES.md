# Pilot notes (exploratory, development tasks only, 2026-09-20)

All numbers below are from the 5 development tasks: 5 clean runs, 5 sham runs, 10 faulty runs (wrong_argument, wrong_source), each in 3 formats = 60 audit calls per pilot. Five runs per cell say nothing about which format is better; these pilots only check that the instrument works.

| Pilot folder | Auditor setting | Answers parsed | False alarms on the 15 clean audits | Exact step on the 30 faulty audits | Seconds per audit |
|---|---|---|---|---|---|
| `pilot-w3` | GLM, thinking off, first prompt | 100% | 15 of 15 | 22 of 30 | 11 |
| `pilot-w3b` | GLM, thinking off, prompt fix ("many runs are clean", analysis written first) | 97% | 11 of 15 | 19 of 30 | 16 |
| `pilot-w3d-qwen` | Qwen3.8 27B, thinking off, same prompt | 97% | 7 of 15 | 30 of 30 | 69 |
| `pilot-w3c-think` | GLM, thinking on, 4,096 output tokens | 68% | 1 of 9 finished answers (6 of 15 never finished) | 20 of 23 finished answers (7 of 30 never finished) | 102 |

What this shows:
- Without thinking, the small auditor almost never says "this run is clean". The go/no-go rule ("returns none on most clean and sham runs") is not met.
- With thinking, the auditor is good when it finishes (8 of 9 clean runs called clean, 20 of 23 faults found), but in 19 of 60 calls the hidden reasoning ran into a loop until the token limit, and no answer came out. That breaks the 90 percent parse rule.
- `wrong_source` is found 5 of 5 times in every format with thinking off: a ceiling. The week-4 check must look at this fault.
- The truncation check (`record too long for num_ctx`) fired once, as designed: thinking with 8,192 output tokens does not fit next to a record in a 16,384 window.

Qwen as auditor (`pilot-w3d-qwen`):
- It found every planted fault in every format (30 of 30). That is a ceiling: with these two faults Qwen leaves no room for a difference between formats.
- Its 7 "false alarms" on clean runs are not plain errors. Six of them are the same two steps, flagged in all three formats, and both are real flaws of the agent:
  task 0, step 18: the think text before says "I will search", but the act is write_note (the round structure forces a note there);
  task 1, step 6: the note says "Williamsburg is located in Richmond", which the passage does not say.
- So the "clean" runs are not perfectly clean. In the 55 passing runs, 12 of 173 notes (in 12 runs) follow a think text that talks about searching instead of the note. Wrong note texts cannot be counted mechanically.
- Consequence: the false-alarm rate measures "the auditor flags something", not only auditor error. The primary test uses faulty runs only, where the planted fault was found despite these flaws.

Next: `validation-w4-glm` and `validation-w4-qwen`: all six faults on the five development tasks (30 faulty runs, 5 sham, 5 clean), audited by both models. This is the pre-registered floor/ceiling check and decides the auditor before the tag.

## Validation on the development tasks (2026-09-21, exploratory): all six faults, both auditors

30 faulty runs (6 faults x 5 tasks), 5 sham, 5 clean, each in 3 formats = 120 audit calls per auditor. Cells hold 5 runs, so only floors and ceilings can be read, not which format is better.

Exact step found, as counts out of 5 (diff / log / prov):

| Fault | GLM, thinking off | Qwen3.8 27B, thinking off |
|---|---|---|
| wrong_argument | 3 / 1 / 0 | 5 / 5 / 5 |
| corrupted_output | 0 / 0 / 0 | 2 / 2 / 2 |
| dropped_note | 1 / 0 / 3 | 4 / 3 / 3 |
| overwritten_note | 5 / 5 / 4 | 5 / 5 / 5 |
| wrong_source | 5 / 5 / 5 | 5 / 5 / 5 |
| no_source | 5 / 5 / 4 | 5 / 5 / 5 |

| | GLM | Qwen |
|---|---|---|
| Exact step, all faulty audits | 57% | 84% |
| Right fault class named | 50% | 89% |
| Answers parsed | 96% | 98% |
| Clean-run audits flagged (of 15) | 11 | 7 |
| Said "no fault" on a faulty run (of 90) | 7 | 5 |
| Seconds per audit | 15 | 63 |
| Longest record | 7,299 tokens | 7,692 tokens (Qwen counts tokens differently) |

Reading:
- Evidence faults (wrong_source, no_source) and overwritten_note are at or near the ceiling for both auditors in every format. With these faults as they are, prediction P3 cannot show up: there is no room above 100 percent.
- corrupted_output is at the floor for GLM (0 of 15) and low for Qwen (6 of 15).
- Qwen gives nearly the same count in all three formats for every fault. GLM varies more, but it also flags 11 of 15 clean audits and names the right class only half the time, so much of its variation is noise.
- The pre-registered rule allows changing a fault before the tag only if it is at 0 or 100 percent in all three formats for the chosen auditor. With Qwen that holds for wrong_argument, overwritten_note, wrong_source and no_source (too easy). With GLM it holds for corrupted_output (too hard) and wrong_source (too easy).
