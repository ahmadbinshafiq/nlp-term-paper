# Pre-registration: Record Format x Fault Type

Version: **v1.0, frozen on 2026-09-21 with the git tag `prereg-v1`**, before any sweep run was generated.

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

- **Agent:** one LangGraph agent with four tools (search, read, write_note, finish) on MuSiQue questions with 3 or 4 hops, over a fixed passage pool (`DECISIONS.md`, D-002). With the question the agent gets MuSiQue's sub-questions as a plan, without answers (D-010). It works in rounds (search, read, write note); each act is one JSON action that must fit a schema of the allowed tools. Step cap: 38 = six rounds of six steps plus think and finish (D-009); every candidate is judged with that one cap.
- **Faults:** a correct run is replayed to step k and one fault is planted there by a tool wrapper. Six fault types in three classes, plus a sham control (`prereg/fault_catalogue.md`). `fault_class` is one of `tool`, `state`, `evidence`, `none`. `fault_type` is one of `wrong_argument`, `corrupted_output`, `dropped_note`, `overwritten_note`, `wrong_source`, `no_source`, or `sham` / `clean` for the controls.
- **Formats:** each run is written in three formats made from one event stream (`docs/schema.md`): `log`, `diff`, `prov`. Each format can be turned back into the identical event stream (round-trip test). So the three formats hold the same information. The renderers are chosen by the round-trip test only, never by how well the auditor does on a format.
- **Primary auditor:** `qwen3.8:27b` on Ollama 0.33.2, temperature 0, seed 0, thinking off, 1,024 output tokens, context size 16,384 (D-012). It did not produce the runs. One answer per record, as JSON: `{analysis, step_id or null, fault_class, fault_type, pointer}`; the short `analysis` text is written first, so that the model looks before it decides.
- **Second auditor:** `glm-4.7-flash:q8_0`, same options and prompt. It is fast, so it audits all sweep runs. Reported as description only.
- **Prompt:** one shared prompt for all formats. It lists the six fault types and says: "Name the first step where something went wrong, not the step where it was noticed." Each format also gets one short reading note. A reading note explains only the syntax of its format (what a line, an operation, a node and an edge are). It names no fault type, no check and no "normal" pattern. The notes differ in length by at most 20 percent. At `prereg-v1` the full text of the prompt and the notes is printed in an appendix here, not only the hashes, so any reader can check this rule.

## 3. Sample

**Gate.** A task enters only if its clean run passes all of these. All checks are mechanical.
1. The answer is correct: after normalization (lowercase, no punctuation, no articles, number words as digits) it equals the gold answer or an alias, or one is a run of whole words inside the other ("summer or fall" matches "usually in the summer or fall"; "1" does not match "1952"). MuSiQue gold answers are often long phrases, so plain exact match would reject correct runs (D-009).
2. The run reached `finish` within the step cap, and the `note_key` given to `finish` exists.
3. The final `cited_pid` is one of the gold supporting passages (checked offline; no model ever sees gold answers or gold passage labels).
4. No hidden fault of our own kinds: no `source_pid` is null, and every `source_pid` was read before its note was written. (A note key cannot be written twice and a passage cannot be read twice: the tools refuse that.)
5. All six faults can be built: for each fault, the set of eligible steps k (catalogue, rule 5) is not empty.

Two more natural patterns (the agent tried to send the same query twice, which the tool refuses; a read of a handle that no search returned) do not fail the gate. They are stored as flags and their counts are reported.

**If too few tasks pass (not needed: 55 of the 155 candidates that were run passed).** If the 250 candidates give fewer than 45 passing tasks: first drop checks 1 and 3 from the gate ("reaches finish with a cited answer") and keep both as covariates in a secondary model; the primary formula does not change. If still below 45, use rule D-003b (agent with thinking on, then `qwen3.8:27b` as agent).

**Candidates.** 250 questions with 3 or 4 hops in seed order: the first 120 (D-002) plus 130 more, added when the measured pass rate (about 30 percent) showed that 120 cannot give 55 passing tasks (D-011). The pass rate is reported in the paper.

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

**If the fit fails.** Failure means a convergence warning from either model. A singular fit (a variance estimated as 0) is not a failure. Then both models are fitted again without `(1 | run_id)`, so full and reduced always have the same random part. If a warning still remains, that p-value is still used, the warning is printed next to it, and a confirming label is reported as provisional. If a whole class is at 0 or 100 percent in every format, no package can fit that part; this is reported, the likelihood-ratio test is still the test, and no odds ratio is given for that class. On 1,000 simulated data sets the first fit warned in 5, and the refit removed the warning in 3 of them.

**What the test assumes.** The likelihood-ratio test assumes that the format x class pattern is the same in every task. The margins below use a bootstrap over tasks, which does not need this. A confirming label needs both. `prereg/power.md` reports the false-positive rate of the test on simulated data in which the pattern differs between tasks; if it is above 0.075, the paper says so next to the p-value.

**Margins.** For each fault class: margin = accuracy of the predicted format minus the mean accuracy of the other two formats, pooled over all faulty runs of that class (paired by run). Confidence intervals: percentile bootstrap, tasks resampled with replacement, all rows of a drawn task taken together, 2,000 resamples, seed 0.

**A margin "meets the rule"** if (i) it is at least 10 points and its 95 percent interval lies above zero, and (ii) the predicted format has strictly the highest accuracy in that class. The three predictions are checked one by one with no correction for multiple tests; the paper says this.

**Smallest effect of interest:** 10 points. **Equivalence bound B = 20 points** (`prereg/power.md`, decision D-013). Rule: B is the smallest of 10, 15, 20 points for which the chance of the label "null" is at least 0.80 when the true margins are 0. The simulation: 200 data sets per setting, N = 50 tasks, accuracy per class as on the 30 faulty validation runs with Qwen (tool 0.70, state 0.85, evidence 0.95), task SD 0.5 and run SD 1.0 on the logit scale (assumed). Chance of "null" at true margins of 0: 0.10 for B = 10, 0.71 for B = 15, 0.93 for B = 20. Because B is above 10, a null result can only say that no difference larger than 20 points was found.
The same simulation shows: the interaction test has 5 percent false positives and finds planted margins of 10 points in 94 percent of the data sets; one margin has a 95 percent interval of about +/- 8 points; all three margins meet the rule in 5, 37 and 69 percent of the data sets at true margins of 10, 15 and 20 points. This is known before any data and is part of the design.

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

If every format is at 95 percent or more in a class, the prediction for that class is marked "not testable (ceiling)" next to the label.

The 90 percent interval in step 3a is the usual equivalence test (two one-sided tests at alpha 0.05 each). All three must pass, so no correction is needed.

## 7. Controls (fixed in advance)

**Reference numbers.** Uniform chance = the mean over faulty runs of 1 / (number of act steps in the record). Tool-prior baseline = the expected score of picking a random `write_note` step. On the 30 faulty development runs: uniform chance = 0.089, tool-prior baseline = 0.223. The pass rules below use the same two quantities computed on the sweep runs.

Controls 1, 3 and 4 decide step 0 of the tree. Control 2 is a reported baseline.
1. **Sham check.** Every sham record is byte-identical to the clean record of its task (mechanical), so every rendering is identical too. The false-alarm rate is reported per format over all distinct no-fault tasks (45 at N = 50), with a Wilson 95 percent interval, next to the miss rate (null answers on faulty runs) per format. A format in which the auditor flags more freely gains hits and false alarms together, so both are shown.
2. **Position-only guesser (reported, not a gate).** It names the act step at the most frequent relative position of k, learned with the tested task left out. It sees no record. Because the runs are short and regular, k sits on few steps (step 12 in about a quarter of the runs), so a guesser without any record scores far above uniform chance; "always the most frequent step" is reported as well. These numbers are the honest floor for the auditor's accuracy.
3. **Structure-only guesser.** Every free text (think text, queries, titles, passage and note text, answer) is ignored; tool names, operation names, the touched state sections and null arguments stay. Each step gets a signature; the guesser names the step whose signature is rarest among the steps of the same tool in the run; ties go to the earliest step. Reported per fault type. Pass rule for `wrong_argument` and `corrupted_output` only: the upper end of the Wilson 95 percent interval of its hit rate is below the tool-prior baseline + 10 points. For `dropped_note`, `overwritten_note` and `no_source` the structure is the fault itself. There the guesser and one simple rule auditor on the event stream are reported as baselines next to the LLM auditor, and it is said openly when a class margin comes from a fault that a one-line rule finds.
4. **Shuffled labels.** Pass: the auditor's real exact score is above the 97.5 percent point of its scores against true steps shuffled within fault type (2,000 shuffles of runs, seed 0). The real score, the shuffled mean and the 97.5 percent point are reported. (A rule "near uniform chance" cannot work here, because runs of one fault type often share the same k.)

Controls 5 to 7 are gates that must be green before any audit call. They cannot be an "outcome":
5. **Leak test:** `tests/test_no_leak.py` is green. It reads `data/tasks.jsonl` and every `events.jsonl`; renderings are made in memory from these events and are not saved.
6. **Round trip:** every rendering of every run converts back to the identical event stream (`code/scripts/roundtrip.py`, which stops the chain on a failure).
7. **Only the fault differs:** each faulty record is byte-identical to its clean run before step k; each sham record is byte-identical to its clean run everywhere.

No guesser and no rule auditor may use the fact that a passage id is a hash of its text.

## 8. Secondary analyses (labelled as secondary in the paper)

- **Record length:** `log(tokens_in)` as a covariate, and a plot of accuracy against record length per format. This shows whether accuracy falls with length inside each format. Format and length are tied together across formats. If the token ranges of two formats overlap little, this analysis cannot separate them, and the paper says so. The token range per format is reported.
- **Position:** `rel_pos` (k divided by the number of steps) and `k_bin` as covariates; the distribution of k per fault type; results split by `hook_tool` for the tool faults.
- **Looser scoring:** within 3 steps of k (`within3`); fault-class naming (F1 per class); the share of wrong answers with `pred_step` after k (the auditor found the symptom, not the cause), per format.
- **Fourth arm (log plus inferred edges): cut before the freeze.** Its one contrast is on evidence faults, and both auditors found those in 5 of 5 development runs in every format, so the contrast could not show anything. This is cut-list item 5 of the plan, taken in full.
- **Second auditor, description only:** `glm-4.7-flash:q8_0` on all sweep runs. Reported: the same tables as for the primary auditor, the three margins with intervals, and whether their signs match. No test and no claim of replication. The 60-run subsample (the 6 faulty runs of the first 10 sweep tasks) is used only if the 3-repeat rule is triggered.
- **Natural plan/act mismatch.** A `write_note` step whose think text just before contains "search" and not "note" (12 of the 55 clean runs have one). Reported: the number of such runs, accuracy per format with and without runs that have such a step before k, and the share of wrong answers that name such a step. The primary test keeps all runs.
- **Native recorders** (callback log, SqliteSaver, inline PROV): a 7 x 3 table of "is the evidence for this fault present in this record?", filled by scripts, not by an auditor.
- **Cost:** tokens per audit, bytes per record, seconds per audit.
- Items that may be dropped if time runs out: LLM audits of native records, rebuild-timing extras.

## 9. What is frozen at `prereg-v1`

Everything in this file, `prereg/fault_catalogue.md` (v0.2, no fault operation was changed), `docs/schema.md`, and the code at the tagged commit. After the tag, `analysis/primary.R`, `analysis/margins.py`, `code/auditarch/score.py`, the renderers, `faults.py`, the prompt and the rules of sections 3 to 7 may not change. Descriptive tables, file names and completeness checks may still be added to `analysis/analyze.py`.

| Item | Value |
|---|---|
| Ollama | 0.33.2 |
| Agent | `glm-4.7-flash:q8_0`, digest `a035bf4bc812e1408631c2d2b14581b99dfe39f71d895aceb269b4a886080196` |
| Primary auditor | `qwen3.8:27b`, digest `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` |
| Second auditor | `glm-4.7-flash:q8_0` (same digest as the agent) |
| Options | temperature 0, seed 0, thinking off, `num_predict` 1024, `num_ctx` 16384. The longest development record is 7,692 tokens, so 16,384 leaves room; the too-long rule of section 3 is the backstop. |
| Prompt hash `log` | `ba8b77f02b64574ea7e93ea62fa1fc123ccb9b7577129cf415e005a243f5b0a5` |
| Prompt hash `diff` | `580493953bfd9de6d0b2d1d8a4f1e43ab9de066daab1e45d308f79bb0263f1ee` |
| Prompt hash `prov` | `168bfa490b87987c32e9abf27aba2b17c5b1e85904f1f25d9f267c0979b5b569` |
| `render/log.py` | sha256 `3bf39cc6902046c07e20014b0385a37e20c324eb6cd8e2fb5eeeab549cc4c6fd` |
| `render/diff.py` | sha256 `f75c7cf40ddab99b0e6c561e6fa34ddfd5005df802cd8f30fdd4bf2deb2b6fb7` |
| `render/prov.py` | sha256 `b22473cf434a5f61fefbcf0879a7fb41ed9130c1ed6aa7bce93ac0a7d0fa6104` |
| `faults.py` | sha256 `64a50dadd63bad970fd6eeec0a8dea046c44d394bfd4b9db98d134bfe279c83e` |
| `analysis/primary.R` | sha256 `71ce38ec882dc9a812cea03de49c807e606613b65df1980d19624e814ea03bf6` (run before on simulated data: p = 0.16 without an effect, p < 0.001 with a planted 20-point effect) |
| `analysis/margins.py` | sha256 `15a06c3a0e0b9272f0d4d48f4a69cb237fe164ae5a0830b3f88bc4ca5505b606` |
| Tasks | 5 development tasks (seed-order numbers 0, 1, 2, 11, 13) and N = 50 sweep tasks, fixed in `DECISIONS.md` |
| Bound B | 20 points (`prereg/power.md`, D-013). The simulation uses no real data. |
| Guessers and rule auditor | `code/auditarch/score.py`, sha256 `affd42699e91efe747f90345d831a1636efde5fee799a25fbf20a3aad0e51e1c` |

**Auditor checks before the tag (exploratory, development tasks only; numbers in `results/PILOT-NOTES.md`).**
- Parse gate (at least 90 percent valid JSON): GLM 96 percent, Qwen 98 percent. Passed.
- "Says no fault on most clean runs": GLM flagged 11 of 15 clean audits even after the one allowed prompt fix; GLM with thinking on did not finish one answer in three. This is why Qwen is the primary auditor (D-012). Qwen flagged 7 of 15; six of these seven are two steps that are real flaws of the agent (a plan that does not match the act; a note that the passage does not support). So the false-alarm rate is reported as "the auditor flags something" and not as pure auditor error.
- Floor/ceiling rule (below 10 or above 90 percent in all three formats): not met for Qwen over all faults (log 0.83, diff 0.87, prov 0.83). Per fault type, `wrong_argument`, `overwritten_note`, `wrong_source` and `no_source` were found in 5 of 5 development runs in every format.
- **No fault operation was changed.** The rule would allow it for those four, but the ceiling does not come from a detail of an operation. It comes from short, regular runs: a note's true source is always the passage read two steps before, and a plan always stands right before its act. Any variant of the operation keeps that. `overwritten_note` and `no_source` are at the ceiling for another reason: the fault is a structure anomaly that a one-line rule finds; that other variants would stay at the ceiling is expected, not tested. The per-format counts of both auditors on the development runs were seen before this choice. The paper states this limit, reports results per fault type, and shows the rule-auditor baseline next to the model.
- Determinism probe (6 development records, 2 per format, each audited 3 times without the cache, model unloaded between rounds; `results/probe-*.json`): Qwen gave the byte-identical answer in 6 of 6 records, GLM in 6 of 6. So one answer per record is enough. The 3-repeat rule (if fewer than 95 percent of the probe records give the same `step_id` in all repeats, the 60-run subsample is audited two more times without the cache; the primary test always uses `sample_id` 0) is not triggered.

**Appendix A: the shared prompt (identical for every format)**

```
You are an auditor. Below is the record of one run of a question-answering agent.

The agent works in steps. A think step writes a short plan. An act step calls one tool:
- search(query) returns 5 passages (handle, title, first words of the text).
- read(handle) returns one passage (pid, title, text) and stores it as evidence.
- write_note(key, text, source_pid) stores a note. source_pid names the passage the fact came from.
- finish(answer, note_key) gives the final answer and cites the source of that note.
A tool may refuse a call with an error, for example a repeated query. A refusal is normal. It is not a fault.

At most one fault was planted in this run, at exactly one act step. The six possible faults:
- wrong_argument (class tool): the tool was called with another argument than the plan just before it said.
- corrupted_output (class tool): the tool returned something that does not fit the call.
- dropped_note (class state): a write_note step returned ok, but no note was stored.
- overwritten_note (class state): a write_note step stored its text under another key that already existed.
- wrong_source (class evidence): a note names a source passage that its text did not come from.
- no_source (class evidence): a note has no source passage.
Many runs are clean, with no fault at all. Report a fault only if the record clearly shows it.
If nothing is clearly wrong, the right answer is: step_id null, fault_class none, fault_type none.

Name the first step where something went wrong, not the step where it was noticed.
Answer with JSON: analysis (two or three sentences: what you checked and what you found), step_id (the number
of the faulty step, or null if the run is clean), fault_class (tool, state, evidence, or none), fault_type
(one of the six names, or none), pointer (a short piece copied from the record that shows the fault; empty if clean).
```

**Appendix B: the reading notes (one per format; they explain the syntax only)**

- `log`: The record is an event log. Each block starts with `step N | think` or `step N | act | tool`. A think block has one `text:` line. An act block has a `call:` line with the arguments, a `return:` line with what the tool gave back, and one `effect:` line for every change the step made to the stored state, written as [operation, path] or [operation, path, value]. The value is left out when the call or the return already shows it.
- `diff`: The record is a list of state changes. Each block starts with `## step N (think)` or `## step N (act)`. Every line below it is one JSON Patch operation with `op` (add or replace), `path` (the place in the stored state) and `value`. The stored state has the sections scratch (think texts), calls (each tool call together with its return), evidence (passages that were read), notes, answer and decision.
- `prov`: The record is a W3C PROV graph in PROV-N notation. `activity(step:N, ...)` is a step; its kind, tool, arguments and return are attributes. `entity(...)` is a data item: thought:N, passage:<pid>, note:<key>@N or answer:N. `used(step, passage)` means the step read that passage. `wasGeneratedBy(item, step)` means the step produced the item. `wasDerivedFrom(a, b)` means that item a names item b as its source.

## 10. Deviations

Any change after `prereg-v1` is written into `results/deviations.md` with date, reason, and whether it was made before or after seeing results. The paper reports all of them.

## 11. Known limits, stated in advance

- The three formats are three ways to show one recorded run, not three recording systems. Real recorders also differ in what they record. This study removes that difference on purpose. So a result here says how a record should be shown to an LLM auditor once the information is there. It does not say that logging, checkpointing or provenance capture is the better architecture. The native-recorder table is a separate coverage check, filled by scripts. The state-diff format is computed by us; what LangGraph's SqliteSaver really stores is checked in week 5.
- One agent design. One dataset. Six synthetic faults, two per class.
- The agent is given MuSiQue's question decomposition as a plan, because this study tests auditors, not question answering. Only tasks that the agent solves cleanly enter the study (35 percent: 55 of the 155 candidates that were run; 9 of the 55 have 4 hops), so the runs are the easier ones.
- One small open-weights model as primary auditor (Qwen3.8 27B); it did not produce the runs. The second auditor (GLM) did, so its results carry the shared-model concern.
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
| 2026-09-21 | v1.0 | Frozen. Primary auditor Qwen3.8 27B, second auditor GLM on all runs (D-012). Fourth arm cut. No fault operation changed; reasons in section 9. Answer JSON gets an `analysis` field first. `too_long` flag instead of stopping the sweep. Hashes, chance numbers and the full prompt text added. |
| 2026-09-20 | v0.2 | Week-2 build: agent gets the sub-questions as a plan (D-010); 250 candidates (D-011); step cap 38, answer-match rule, JSON actions, tools that refuse repeats, 5 search results (D-009). Gate check 4 shortened because the tools now make two of its parts impossible. |
| 2026-09-20 | v0.1 | After a four-reviewer check (39 confirmed points). Decision tree with seven labels in fixed order replaces the five overlapping outcomes (D-007). Margin rule now also needs "predicted format is best in its class". Equivalence bound B set by a power rule, 90 percent intervals for the Null label; first simulation says margins near 20 points are what this study can detect (D-007). Fit-failure ladder made exact. Gate extended by mechanical checks and "all six faults buildable" (D-006). Controls given numbers and fixed algorithms; the sham check is now a hash check; the structure-only guesser is a baseline, not a pass/fail control, for faults whose cue is structural. Rules for kept runs, too-long records, the subsample, clean and sham selection. Second auditor is description only. Limits rewritten. Glossary added. The outcome column is named `exact` (the plan's formula wrote `correct`). |
