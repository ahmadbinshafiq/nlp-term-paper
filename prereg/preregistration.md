# Pre-registration: Record Format x Fault Type

Version: **v0.1 (draft), 2026-09-20.** It becomes binding when the git tag `prereg-v1` is set at the end of week 4, before any sweep run is generated.

Everything done before that tag (probe, pilot, validation runs) is **exploratory**, uses development tasks only, and is reported apart from the main results. Every change before the tag goes into the changes log with its reason. Allowed reasons: answers that cannot be parsed; floor or ceiling (section 9); a leak found by a control; a rule that turned out to be unclear. Not allowed: a change made because one format did better or worse than another on development runs.

Words that may be new are explained in the glossary at the end.

## 1. Question and hypothesis

**Question.** Does the form of an audit record change how well an auditor finds a fault, when the information in the record is held equal?

**Hypothesis.** The record format that finds the faulty step best depends on the fault class.

| Prediction | Fault class | Predicted best format |
|---|---|---|
| P1 | `tool` (wrong argument, corrupted output) | event log (`log`) |
| P2 | `state` (dropped note, overwritten note) | state diffs (`diff`) |
| P3 | `evidence` (wrong source, no source) | PROV graph (`prov`) |

The reasons behind each prediction are in `prereg/fault_catalogue.md`.
Honest note: each fault class was chosen to match the natural unit of one format, and the faults and the formats were built by the same person. The study does not show that these are the faults that matter most in practice. All claims are limited to these six faults.

## 2. Design in short

- **Agent:** one LangGraph agent with four tools (search, read, write_note, finish) on MuSiQue questions with 3 or 4 hops, over a fixed passage pool (`DECISIONS.md`, D-002). Step cap: 30. It may be raised once to 35 in week 2 if 4-hop runs come close. The final value is logged in `DECISIONS.md` before any sweep-pool task is run, and every candidate is judged with that one cap.
- **Faults:** a correct run is replayed to step k and one fault is planted there by a tool wrapper. Six fault types in three classes, plus a sham control (`prereg/fault_catalogue.md`). `fault_class` is one of `tool`, `state`, `evidence`, `none`. `fault_type` is one of `wrong_argument`, `corrupted_output`, `dropped_note`, `overwritten_note`, `wrong_source`, `no_source`, or `sham` / `clean` for the controls.
- **Formats:** each run is written in three formats made from one event stream (`docs/schema.md`): `log`, `diff`, `prov`. Each format can be turned back into the identical event stream (round-trip test). So the three formats hold the same information. The renderers are chosen by the round-trip test only, never by how well the auditor does on a format.
- **Auditor:** `glm-4.7-flash:q8_0` on Ollama 0.33.2, temperature 0, seed 0, thinking off, 1,024 output tokens, one fixed context size. One answer per record, as JSON: `{step_id or null, fault_class, fault_type, pointer}`.
- **Prompt:** one shared prompt for all formats. It lists the six fault types and says: "Name the first step where something went wrong, not the step where it was noticed." Each format also gets one short reading note. A reading note explains only the syntax of its format (what a line, an operation, a node and an edge are). It names no fault type, no check and no "normal" pattern. The notes differ in length by at most 20 percent. At `prereg-v1` the full text of the prompt and the notes is printed in an appendix here, not only the hashes, so any reader can check this rule.

## 3. Sample

**Gate.** A task enters only if its clean run passes all of these. All checks are mechanical.
1. The answer is correct (normalized exact match against the gold answer and its aliases).
2. The run reached `finish` within the step cap, and the `note_key` given to `finish` exists.
3. The final `cited_pid` is one of the gold supporting passages (checked offline; no model ever sees gold data).
4. No hidden fault of our own kinds: no note key is written twice, no `source_pid` is null, and every `source_pid` was read before its note was written.
5. All six faults can be built: for each fault, the set of eligible steps k (catalogue, rule 5) is not empty.

Two more natural patterns (the same query searched twice; a read of a handle that no search returned) do not fail the gate. They are stored as flags and their counts are reported.

**If too few tasks pass.** If the week-2 pass rate, projected to 120 candidates, gives fewer than 45 passing tasks: first drop checks 1 and 3 from the gate ("reaches finish with a cited answer") and keep both as covariates in a secondary model; the primary formula does not change. If still below 45, use rule D-003b (agent with thinking on, then `qwen3.8:27b` as agent).

**Pools.** The first 5 passing tasks in seed order are **development tasks** (pilot, validation), never in the main analysis. The sweep pool is the next passing tasks, capped at 50. N is written into `DECISIONS.md` before the first audit call of the sweep, and no sweep run is audited before all sweep runs are generated. If N is below 40 after both fallbacks, the primary test is still run, but every outcome label is reported as exploratory.

**Runs.** N x 6 faulty runs, one per task and fault, with k set by the catalogue rule. At N = 50: 300 faulty runs, 25 clean controls, 20 sham controls = 345 runs, each audited in 3 formats. Primary test rows: 300 x 3 = 900 (720 at N = 40).
- Clean controls: the first 25 sweep tasks in seed order. Sham controls: the last 20 sweep tasks in seed order.
- Every faulty run is kept, whatever happens after k (step cap hit, no `finish`, answer unchanged). k is never re-drawn. A run is rebuilt only if its record before step k is not byte-identical to the clean run.
- **Too-long records.** Every audit call checks `prompt_eval_count + num_predict < num_ctx`. If the check fails for any of the three formats of a run, all three rows of that run leave the primary test. This depends only on length, never on the answer. Counts are reported per fault class and format. `num_ctx` is fixed in week 3 from the worst case (tokens per step of the longest format x the step cap, plus prompt and output), not from the longest pilot run.

## 4. Outcome

**Faulty step** = the earliest step whose recorded call, return or state change is wrong. By construction this is k, the step where the wrapper fired, even if the damage shows up later.

- `exact` = 1 if the auditor's `step_id` equals k, else 0. An answer that cannot be parsed, or a null `step_id`, counts as 0. It is never dropped. This is the primary outcome. It is defined on faulty runs only.
- `false_alarm` (control runs only) = 1 unless the answer parsed and had `step_id` null and `fault_class` `none`.

## 5. The one primary test

Mixed-effects logistic regression in R (`lme4`), on the faulty runs and the three formats only:

```r
ctrl    <- glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))
full    <- glmer(exact ~ format * fault_class + (1 | task_id) + (1 | run_id), family = binomial, control = ctrl)
reduced <- glmer(exact ~ format + fault_class + (1 | task_id) + (1 | run_id), family = binomial, control = ctrl)
anova(reduced, full)   # likelihood-ratio test of the interaction, 4 degrees of freedom, alpha = 0.05
```

**If the fit fails.** Failure means a convergence warning from either model. A singular fit (a variance estimated as 0) is not a failure. The steps below are always applied to both models together, so full and reduced always have the same random part: (1) drop `(1 | run_id)`; (2) `glmmTMB` with both random intercepts; (3) `glmmTMB` without `(1 | run_id)`. The step used is reported. Every step is tried on the simulated files before the tag. If a format x class cell is at 0 or 100 percent, this is reported, the likelihood-ratio test is still the test, and no odds ratio is reported for that cell.

**What the test assumes.** The likelihood-ratio test assumes that the format x class pattern is the same in every task. The margins below use a bootstrap over tasks, which does not need this. A confirming label needs both. `prereg/power.md` reports the false-positive rate of the test on simulated data in which the pattern differs between tasks; if it is above 0.075, the paper says so next to the p-value.

**Margins.** For each fault class: margin = accuracy of the predicted format minus the mean accuracy of the other two formats, pooled over all faulty runs of that class (paired by run). Confidence intervals: percentile bootstrap, tasks resampled with replacement, all rows of a drawn task taken together, 2,000 resamples, seed 0.

**A margin "meets the rule"** if (i) it is at least 10 points and its 95 percent interval lies above zero, and (ii) the predicted format has strictly the highest accuracy in that class. The three predictions are checked one by one with no correction for multiple tests; the paper says this.

**Smallest effect of interest:** 10 points. **Equivalence bound B:** fixed at `prereg-v1` by this rule. `prereg/power.md` simulates the whole decision tree of section 6 (at least 500 data sets per setting; N = 40 and 50; true margins 0, 10, 15, 20 points; accuracy level as seen on the 18 faulty validation runs) and reports the chance of each outcome and the expected interval width. B is the smallest of 10, 15, 20 points for which the chance of "Null" is at least 0.80 when the true margins are 0. If none reaches 0.80, B = 20, the chance is printed, and the paper says that a Null result was unlikely to be reachable. If B is above 10, the paper says that effects between 10 points and B cannot be ruled out.
A first rough simulation (2026-09-20) suggests that one margin has a standard error of about 5.5 points at N = 50. So this study can detect margins of about 20 points, not 10, and B = 10 cannot work. This is known before any data and is part of the design, not an excuse made afterwards.

**Also reported, as description only:** all nine pairwise format differences inside the classes, with intervals; the margins per fault type (6); for each prediction, the margin of the predicted format in its own class minus its mean margin in the other two classes.

## 6. Decision tree

Walk the steps in this order. The first step that applies gives the label.

| Step | Label | Rule |
|---|---|---|
| 0 | **Not interpretable** | One of the controls 1 to 4 (section 7) fails. No confirming claim is made, whatever the other numbers say. |
| 1 | **Refuted: one format dominates** | The same format has strictly the highest accuracy in all three classes, and its paired difference to each of the other two formats, pooled over all faulty runs, has a 95 percent interval above zero. If the interaction is also significant, this is reported as "dominates, size differs by class". |
| 2a | **Confirmed** | The interaction is significant and all three margins meet the rule. |
| 2b | **Partly confirmed** | The interaction is significant and one or two margins meet the rule. Reported per prediction. |
| 2c | **Refuted: another interaction** | The interaction is significant and no margin meets the rule. |
| 3a | **Null** | The interaction is not significant, and all three margins have 90 percent intervals fully inside -B to +B. Wording: "no predicted advantage as large as B was found". |
| 3b | **Underpowered** | The interaction is not significant, but at least one interval reaches beyond -B or +B. Reported as "cannot tell", with the power file. |

The 90 percent interval in step 3a is the usual equivalence test (two one-sided tests at alpha 0.05 each). All three must pass, so no correction is needed.

## 7. Controls (fixed in advance)

**Reference numbers.** Uniform chance = the mean over faulty runs of 1 / (number of act steps in the record). Tool-prior baseline = the expected score of picking a random `write_note` step. Both numbers are written here at `prereg-v1`, from the development runs.

Controls 1 to 4 decide step 0 of the tree:
1. **Sham check.** For every sham run, the hash of each rendering equals the hash of the same rendering of its clean run (mechanical). The false-alarm rate is reported per format over all distinct no-fault tasks (45 at N = 50), with a Wilson 95 percent interval, next to the miss rate (null answers on faulty runs) per format. A format in which the auditor flags more freely gains hits and false alarms together, so both are shown.
2. **Position-only guesser.** It names the step at the most frequent relative position of k, learned with the tested task left out. It sees no record. Pass: the upper end of its 95 percent interval is below uniform chance + 10 points.
3. **Structure-only guesser.** Every free text (think text, queries, titles, passage and note text, answer) becomes a placeholder; tool names, keys, ids, operation names, paths and null stay. Each step gets a signature (node kind, tool name, list of operations and top-level paths of its patch, which arguments are null). The guesser names the step whose signature is rarest among the steps of the same tool in the run; ties go to the earliest step. Reported per fault type. Pass rule for `wrong_argument` and `corrupted_output` only: upper end of the interval below the tool-prior baseline + 10 points. For `dropped_note`, `overwritten_note`, `no_source` (and `wrong_source`, if the rule "the source must be the latest read" finds it) the structure is the fault itself. There the guesser and one simple rule auditor on the event stream are reported as baselines next to the LLM auditor, and it is said openly when a class margin comes from a fault that a one-line rule finds.
4. **Shuffled labels.** Scoring the auditor's answers against true steps shuffled within fault type: upper end of the interval below uniform chance + 10 points.

Controls 5 to 7 are gates that must be green before any audit call. They cannot be an "outcome":
5. **Leak test:** `tests/test_no_leak.py` is green on every run and every rendering.
6. **Round trip:** every rendering of every run converts back to the identical event stream.
7. **Only the fault differs:** each faulty record is byte-identical to its clean run before step k; each sham record is byte-identical to its clean run everywhere.

No guesser and no rule auditor may use the fact that a passage id is a hash of its text.

## 8. Secondary analyses (labelled as secondary in the paper)

- **Record length:** `log(tokens_in)` as a covariate, and a plot of accuracy against record length per format. This shows whether accuracy falls with length inside each format. Format and length are tied together across formats. If the token ranges of two formats overlap little, this analysis cannot separate them, and the paper says so. The token range per format is reported.
- **Position:** `rel_pos` (k divided by the number of steps) and `k_bin` as covariates; the distribution of k per fault type; results split by `hook_tool` for the tool faults.
- **Looser scoring:** within 3 steps of k (`within3`); fault-class naming (F1 per class); the share of wrong answers with `pred_step` after k (the auditor found the symptom, not the cause), per format.
- **Fourth arm:** event log plus inferred edges, against `prov`, on evidence faults only. This asks whether recorded edges beat guessed edges.
- **Second auditor, description only:** `qwen3.8:27b` on the 60-run subsample = the 6 faulty runs of the first 10 sweep tasks in seed order. Reported: the three margins with intervals, and whether their signs match the primary auditor. No test and no claim of replication. The same 60 runs are used for the 3-repeat rule and the thinking-on re-audit, if these happen.
- **Native recorders** (callback log, SqliteSaver, inline PROV): a 7 x 3 table of "is the evidence for this fault present in this record?", filled by scripts, not by an auditor.
- **Cost:** tokens per audit, bytes per record, seconds per audit.
- Items that may be dropped if time runs out, in this order (plan, section 5): LLM audits of native records, extra rule auditors, second auditor, rebuild-timing extras, fourth arm on all runs.

## 9. What is frozen at `prereg-v1`

The shared prompt and the reading notes (four hashes, one per format `log`, `diff`, `prov`, `log_inferred`; each is sha256 of the shared prompt plus that format's note and equals the `prompt_hash` column), the JSON answer schema, sha256 of the three renderers, the Ollama version, both model digests, all model options including the context size, the fault catalogue, the gate, the step cap, the task order, the bound B, the two guessers, the analysis script `analysis/primary.R` (run before on simulated data), and `prereg/power.md`.

| Item | Value at v0.1 |
|---|---|
| Ollama | 0.33.2 |
| Agent and primary auditor | `glm-4.7-flash:q8_0`, digest `a035bf4bc812e1408631c2d2b14581b99dfe39f71d895aceb269b4a886080196` |
| Second auditor | `qwen3.8:27b`, digest `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` |
| Options | temperature 0, seed 0, thinking off, `num_predict` 1024, `num_ctx` 16384 (final value set in week 3) |
| Prompt hashes, renderer hashes, B, chance numbers | to be added in week 4 |

**Auditor checks before the tag (exploratory, development tasks only).**
Parse gate: at least 90 percent of pilot answers are valid JSON; if not, one prompt or schema fix, then `qwen3.8:27b` as primary auditor. Floor/ceiling: on the 18 faulty validation runs, if `exact` is below 10 percent or above 90 percent in all three formats, switch the auditor to thinking on (`num_predict` 8192), else to `qwen3.8:27b`. A single fault operation may be made harder or easier only if `exact` for that fault type is 0 or 100 percent in all three formats on its development runs, and the change is logged before any per-format comparison is looked at.

## 10. Deviations

Any change after `prereg-v1` is written into `results/deviations.md` with date, reason, and whether it was made before or after seeing results. The paper reports all of them.

## 11. Known limits, stated in advance

- The three formats are three ways to show one recorded run, not three recording systems. Real recorders also differ in what they record. This study removes that difference on purpose. So a result here says how a record should be shown to an LLM auditor once the information is there. It does not say that logging, checkpointing or provenance capture is the better architecture. The native-recorder table is a separate coverage check, filled by scripts. The state-diff format is computed by us; what LangGraph's SqliteSaver really stores is checked in week 5.
- One agent design. One dataset. Six synthetic faults, two per class.
- One small open-weights model as auditor, which also produced the runs. The second auditor is a partial answer and may be dropped under the cut order; if so, the paper says that the shared-model concern has no answer.
- The study can detect large differences only (section 5).

## Glossary

- **Hops:** the number of facts that must be chained to answer a question.
- **Step k:** the step of the run where the fault is planted.
- **Step cap:** the largest number of steps a run may take.
- **Gate:** the test a clean run must pass to enter the study.
- **Sham:** the fault wrapper is switched on but changes nothing, like a placebo.
- **PROV graph:** a W3C standard for writing down what used and made what. Here steps and data items are nodes; "used" and "was derived from" are edges.
- **Pointer:** the line, patch path or graph node that the auditor names as its evidence.
- **Fourth arm / inferred edges:** an event log plus edges that a simple text-overlap rule guesses afterwards.
- **Thinking off:** the model answers directly, without a hidden reasoning text first.
- **Mixed-effects logistic regression:** a yes/no model that knows that rows from the same task and the same run belong together. `(1 | task_id)` means "each task has its own base difficulty".
- **Interaction:** "the effect of the format depends on the fault class". This is exactly the hypothesis.
- **Likelihood-ratio test:** compares the model with and without the interaction.
- **Bootstrap over tasks:** re-draw the tasks many times with replacement to see how much a number would move with other tasks.
- **Equivalence test:** a test that can show "the difference is smaller than B", which a normal test cannot.

## Changes log

| Date | Version | Change |
|---|---|---|
| 2026-09-20 | v0 | First draft. Local models (D-003, D-003d). |
| 2026-09-20 | v0.1 | After a four-reviewer check (39 confirmed points). Decision tree with seven labels in fixed order replaces the five overlapping outcomes (D-007). Margin rule now also needs "predicted format is best in its class". Equivalence bound B set by a power rule, 90 percent intervals for the Null label; first simulation says margins near 20 points are what this study can detect (D-007). Fit-failure ladder made exact. Gate extended by mechanical checks and "all six faults buildable" (D-006). Controls given numbers and fixed algorithms; the sham check is now a hash check; the structure-only guesser is a baseline, not a pass/fail control, for faults whose cue is structural. Rules for kept runs, too-long records, the subsample, clean and sham selection. Second auditor is description only. Limits rewritten. Glossary added. The outcome column is named `exact` (the plan's formula wrote `correct`). |
