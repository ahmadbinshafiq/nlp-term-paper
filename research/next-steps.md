# Next steps for the term paper (v5, 2026-09-15)

## 0. One-paragraph reminder of the hypothesis and the design

One LangGraph agent answers MuSiQue 3/4-hop questions over fixed offline passages. Run length: expected 20-26 canonical steps, to be measured in the 5 clean runs (section 3, step 3); the +/-3 window and the deferred 40-step tier depend on it. Each clean run is replayed to step k and one of six faults is planted through the tool wrapper on an act step (tool: wrong argument, corrupted output; state: dropped note, overwritten note; evidence: wrong source, no source). One cheap auditor (claude-haiku-4-5-20251001, temperature 0) sees the same faulty run in three lossless renderings of one canonical event stream: event log, application-state diffs, PROV graph with used/wasDerivedFrom edges; a fourth arm (log plus inferred edges) is a secondary contrast. Prediction: log wins tool faults, diffs win state faults, graph wins evidence faults. One pre-registered test: the format x fault-class interaction over the three lossless formats in a mixed-effects logistic model. Refuted if one format dominates every class, or if the interaction is not significant and every predicted margin's 95 percent CI lies inside +/-10 points. Native recorders (callback JSONL, SqliteSaver, inline PROV) form a secondary arm scored by a mechanical evidence-present matrix; if their differences vanish under information-equivalent rendering, they were record coverage, not structure.

## 1. This week

First 48 hours:
1. Email the supervisor, book 30 minutes, attach `docs/supervisor-brief.md` (section 6). Deliverable: email sent, date logged.
2. Create `code/` skeleton, `DECISIONS.md` (D-001, 2026-09-15: D primary, C fallback), `hours.csv`, `budget.md`, a private GitHub or GitLab remote (push at every tag); tag `start`. Deliverable: remote URL in `DECISIONS.md`.
3. Environment: `uv venv --python 3.13` (uv already has CPython 3.13.14; skip 3.12). Install langgraph, langgraph-checkpoint-sqlite, langchain-core, langchain-anthropic, anthropic, `prov[dot]` 3.2.1, jsonpatch, rank-bm25, datasets, pydantic, pandas, pytest. Deliverable: `uv.lock`; smoke test prints one StateSnapshot and one PROV-JSON with a wasDerivedFrom edge.
4. Data: load `dgslibisey/MuSiQue` validation (2,417 rows); keep ids starting `3hop` or `4hop` (1,165); sample 120 candidates, seed 0, in order. Split rows into `tasks.jsonl` (id, question, paragraphs with idx, title, text) and `gold.jsonl` (answer, aliases, is_supporting, paragraph_support_idx, decomposition). Log D-002 before measuring recall: pooled corpus over all sampled tasks' paragraphs (about 20 x 120), stable `ent:passage:<pid>` ids. Deliverable: BM25 top-3 recall over sub-questions in `DECISIONS.md` (proceed above 0.8, else HotpotQA); `tests/test_no_leak.py` asserting `events.jsonl` and every rendering contain no gold field (`is_supporting`, `paragraph_support_idx`, `decomposition`, the `answer_aliases` list). The answer string itself may appear, because a correct run writes it through `finish`; the test forbids gold metadata, not the agent's own output.
5. Budget: 150 USD hard cap in the console. Check the deprecations page for Haiku 4.5 and log the posted status: "not sooner than 2026-10-15" is a floor, not a schedule, and that date falls in week 5 (rule D-003c, section 2). One Haiku call with structured output via `output_config.format` (not the deprecated `output_format`). Deliverable: `docs/cost.md` with `usage` (input and output), prices from the pricing page (Haiku 4.5: 1 / 5 USD per MTok, half batched; Sonnet 5: 2 / 10, verify) and three cost lines: generation, sweep audits, development (probe, pilot, 18 validation continuations, re-audits, re-generation).
6. `docs/schema.md`: canonical event = exactly (step_id, node_kind, tool_call, tool_return, state_patch). Exactly two node kinds: `think` (no tool; patch touches `scratch[step_id]` only) and `act` (one tool call; patch touches `calls[step_id]` plus that tool's state effect). Four tools: `search(query)` returns handles; `read(handle)` returns text, writes `evidence[pid]`; `write_note(key, text, source_pid)` writes `notes[key]`; `finish(answer, note_key)` writes `answer` (text) and `decision` ({note_key, cited_pid}: the note the answer rests on and that note's recorded `source_pid`, copied by the tool, never chosen by the model). Notes and answers are tool effects, not node kinds. Every state key is a dict keyed by id; the recorder copies each tool call and return into `calls[step_id]`, so the state patch alone carries every field and nothing lives only in messages. Fault hooks: tool faults on search and read steps; state faults on write_note steps (dropped: write swallowed, `ok` returned; overwritten: written to another existing key); evidence faults on write_note `source_pid` only (wrong: another pid; none: null); because finish copies `cited_pid` from the note, the bad source propagates to the final claim without a hook on finish, which would always land on the last act step and hand the guesser a position cue. Three hand-written events. `docs/data-statement.md`: MuSiQue license (check HF and GitHub), Wikipedia-derived text, offline use, no human subjects, no personal data collected, real names only as benchmark text, passages sent to the Anthropic API under its terms, all faults synthetic. Deliverable: both files committed.

Rest of week 1:
7. `code/auditarch/schema.py` (pydantic), fold/unfold tests green.
8. `prereg/preregistration.md` v0 and `prereg/fault_catalogue.md` (about 3 h base, counted inside section 3, item 0). Prereg: hypothesis, predictions, thresholds from `research/full-report.md`; changes log; pilot marked exploratory. Catalogue: seven rows (class, hook tool, exact operation, ground-truth step rule, eligible k range = the hook tool's act steps, predicted evidence per format, reachable flag). Row 7, sham: `FaultyTool` engaged at step k returns the identical output; byte-diff clean vs sham = 0 on every record file (only `truth.json` differs); scored like a clean run.
9. `analysis/schema.md`: results row = run_id, task_id, fault_type, fault_class, k, k_bin, format, arm, sample_id, is_control, is_development, pred_step, true_step, exact, within3, pred_cat, true_cat, false_alarm, pointer_ok, parse_ok, tokens_in, tokens_out, bytes_record, prompt_hash, render_hash, model_id (as returned), api_path (batch or sync).
10. Reading kit: Gupta PDF to `papers/untrusted/`; `do-not-cite.md` (Gupta no results; GraphTracer 2510.10581 withdrawn 2025-12-22; IETF draft is individual; Who&When Pro repo is eval harness only); `references.bib` with venue and status fields, provisional until week 11; `injection-recipe-notes.md` citing arXiv 2607.09996 Sec. 3 and App. C Table 5 (18 modes) and HF `taxonomy.yaml` (17 released), never the repo.
11. Friday: 5-line status entry in `DECISIONS.md`.

## 2. Decisions to lock before spending money

Record each in `DECISIONS.md` and `prereg/preregistration.md`:
- Dataset: MuSiQue-Ans 3/4-hop, 120 candidates in seed-0 order. Gate: normalized exact match against `answer_aliases`, finish within the step cap, one cited passage. Two pools: the first 5 gate-passers (found in week 2 by running candidates in seed order until 5 pass) are development tasks (pilot and validation runs, never in the sweep); the next 50 (minimum 40) are the sweep pool, so 55 passers are needed (45 at the minimum). The week-2 pass rate, projected to 120, decides early: if below 45, first loosen to "reaches finish with a cited answer", keep correctness as a covariate; if still below 45, escalate the agent model (D-003b). Log the gate before week 2. Corpus: pooled (D-002).
- Agent model (D-003, log this week): `claude-haiku-4-5-20251001`, temperature 0, no thinking, `max_tokens` 1024 per step: verified price (1 / 5 USD per MTok), temperature 0 accepted, one retirement date to track. Same model as the auditor, so the auditor judges its own model's traces: a confound, stated in limitations; a 60-run re-audit with the fallback auditor is cut-order item 3 (stretch). D-003b: if fewer than 45 pass even the loosened gate, escalate to `claude-sonnet-5` at default sampling and follow the re-generation plan in D-003c.
- Auditor: `claude-haiku-4-5-20251001` (the alias target), temperature 0 (never with top_p), `max_tokens` 1024; only input length is uncapped. One sample unless the probe shows below 95 percent agreement, then 3 samples on a 60-run subsample. Store the returned model string per response.
- Fallback auditor, named in prereg: `claude-sonnet-5` at default sampling (Sonnet 5 and Opus 5 reject non-default temperature; SDK 1.x raises TypeError); at 2 / 10 USD per MTok it about doubles the audit line.
- Retirement rule (D-003c, log this week): 2026-10-15 falls in week 5, so generation (week 6), a week-6 sweep and the week-7 sweep all fall after it; moving the sweep shortens exposure but does not remove it. Checks: week 1, go/no-go, before `prereg-v1`, the day before generation, the day before the sweep. Trigger: a posted retirement date before the end of week 8, or a model-not-found error. Action: switch agent and auditor together to `claude-sonnet-5`; re-generate the development runs on the new agent (the 10 pilot runs, which include the 5 clean runs, plus 21 validation runs = 31 runs; cost = measured USD per run x 31, expected under 10 USD, to be measured in section 3, steps 3 and 6; 6 h buffered). If the trigger fires after week-6 generation is complete, keep the Haiku-generated sweep runs, switch only the auditor to Sonnet, and log in `results/deviations.md` that agent and auditor now differ (this removes the shared-model confound rather than adding one); re-run the 30-call probe; re-hash the prompts; log the change in prereg if before `prereg-v1`, else in `results/deviations.md`. Old runs stay in `cache/` under their model key. A sweep is never split across models: if the primary fails mid-batch, the whole sweep is re-submitted on the fallback (about double the audit line, inside the 50 USD headroom). Cached prefixes replay without the model; every continuation after k and every audit need it live.
- Prompt: one shared instruction plus one format-reading note per format, four notes (three lossless plus the fourth arm), lengths matched within 20 percent; all four hashes stored and shown in `prereg-v1`, so the fourth-arm renderer is built in week 4. Output JSON {step_id or null, fault_class incl. `none`, fault_type, pointer} via structured outputs. Parse failures count as wrong, never dropped. Pilot audits are exploratory and excluded; the 10 pilot runs are re-audited with the frozen prompt after `prereg-v1`, reported separately.
- Step id: 1-based LangGraph state channel, present in log, checkpoints and PROV activities.
- Diff arm: per step, a header (step_id, node_kind) plus the jsonpatch of application state only; no message list. Lossless because tool I/O sits in `calls[step_id]` and think output in `scratch` (section 1, item 6); the round trip (section 3, step 5) proves it. State keys are dicts keyed by id; tool returns inside `calls[step_id]` may hold lists (search handles), but that key is write-once, so its patch is one `add` op and its lists are never diffed. `render/diff.py` still asserts `patch.apply(prev) == curr` per step and falls back to whole-value `replace` (section 8, row 5). Token overlap with the log is expected to be high because both carry the same content; the pilot check is structural (section 4), not a threshold.
- Fourth arm (built week 4): Jaccard token overlap >= 0.3 between output(i) and input(j), never handle matching; edges labelled inferred. Secondary contrast only: graph vs inferred-edge log on evidence faults.
- Runs (sweep pool, N tasks): N x 6 faulty, 25 clean, 20 sham. N = 50 gives 300 + 25 + 20 = 345 runs; the 40-task minimum gives 285. Live continuations: N x 6 = 300 (240 at the minimum); the 25 clean controls are existing runs and the 20 sham runs replay from cache at zero API cost. Development runs (10 pilot, 21 validation) are outside this count. k stratified early/middle/late within the hook tool's act steps; eligible k ranges differ by fault type, so report k per fault type.
- Primary test, three lossless formats only: `glmer(correct ~ format*fault_class + (1|task_id) + (1|run_id), binomial)` in R lme4 (installed week 4; fallback (1|task_id) only, then glmmTMB); cluster bootstrap over tasks (2,000) for paired margins.
- Secondary models: log(tokens_in) covariate (length); k_bin covariate (position); accuracy vs record length plot per format.
- Controls, pre-registered: false-alarm rate on sham equals the clean rate (bootstrap CI); position-only and structure-only guessers near chance.
- Smallest effect of interest: 10 points paired margin. Confirm: significant interaction, each format's margin on its predicted class >= 10 with CI excluding zero, controls near chance. Refute: one format dominates every class, or interaction not significant and every predicted margin's 95 percent CI inside +/-10 (TOST; section 10).
- Native arm: the evidence-present matrix is the deliverable; LLM audits only if budget and time remain at week 7.
- Pre-registration: git tag `prereg-v1` at the end of week 4, after the full injector, the fourth-arm renderer and the power file, before generation in week 6; emailed to the supervisor. No OSF.
- Cut order in section 5. Never cut: three lossless formats, controls, 40-task minimum, primary test.

## 3. Build order (weeks 1-3, to the 10-run pilot)

Hours listed are buffered (base x 1.5, rounded); actuals go in `hours.csv`.

0. Admin, prereg v0, catalogue, analysis schema, reading kit (section 1 items 1, 2, 8-11; weeks 1-3, 9 h, 6 h base). Deliverable: those files committed, Friday status entries.
1. Toolchain, task slice, data statement (week 1, 6 h). Items 3-6 above. Deliverable: `uv.lock`, `tasks.jsonl` (120 lines, hop counts), `gold.jsonl`, D-002, `docs/data-statement.md`.
2. Decision zero: schema (week 1, 7 h). One event per node execution; node kinds exactly `think` and `act` (section 1, item 6); tools search, read, write_note, finish; ids `ent:passage:<pid>`, `ent:note:<key>@<step>`; `truth.json` outside the stream; pointer grammar per format. Deliverable: `schema.py`, `tests/test_schema.py` green, incl. tests that `calls[step_id]` equals (tool_call, tool_return) on every act event and that think events have null tool fields.
3. Agent, tools, cached LLM wrapper, clean runs (week 2, 15 h). Strictly sequential StateGraph on the pinned agent model; step cap 30 (35 if 4-hop runs approach it); the four tools return handles; content-addressed LLM cache (sha256 of model+params+messages) so warm-start prefixes replay byte-identically; recorder writes `events.jsonl`; `test_no_leak.py` green. Deliverable: clean runs in seed order until 5 candidates pass the gate (expected 5-15 runs, all cached and costed); pass rate projected to 120; mean steps (expected 20-26, first measured here), cap-hit rate (cap-hit = fails the gate), answer accuracy, tokens and USD per clean run in `docs/cost.md`.
4. Methods while building (week 2, 4 h). Deliverable: `paper/methods.md` headings; family-to-system table (callback JSONL; SqliteSaver, characterisation provisional until its `checkpoints` and `writes` tables are inspected; prov library with PROV-AGENT as representative); tag `methods-v0`.
5. Three lossless renderers and round trip (week 3, 9 h). `render/log.py`; `render/diff.py` (jsonpatch; assert `patch.apply(prev) == curr`, else whole-value replace); `render/prov.py` (you add wasDerivedFrom; PROV-AGENT does not). `roundtrip.py` asserts `parsed_events == events` (deep equality, tool_call and tool_return included) for all three formats. Deliverable: `results/roundtrip.csv` all ok; structural check (diff rendering = header plus jsonpatch ops, no message list; three distinct `render_hash` values per run); Jaccard overlap log vs diff and log vs PROV per run, descriptive only.
6. Minimal injector, 2 faults plus sham (week 3, 6 h). `FaultyTool(tool, fault, k)` for tool.wrong_argument, evidence.wrong_source, sham; k drawn from the hook tool's act steps; prefix from cache in strict mode. Deliverable: 4 faulty and 1 sham run; byte-diff clean vs faulty = 0 lines before k; clean vs sham = 0 on every record file (only `truth.json` differs); tokens and USD per continuation (steps k to finish) in `docs/cost.md`.
7. Determinism probe (week 3, 2 h). 6 faulty records (2 per format) x 5 repeats = 30 calls through the Batch API (same path as the sweep). Agreement = pairwise step-id agreement across repeats; rule pre-written in `prereg/auditor_protocol.md`. Deliverable: agreement rate, reported as noise floor whatever the sampling decision; decision logged.
8. Auditor, scorer, pilot (week 3, 7 h). 10 runs (5 clean, 4 faulty, 1 sham) x 3 forms = 30 exploratory calls; `score/metrics.py` incl. false_alarm and pointer_ok; position-only guesser. Deliverable: `results/pilot-w3/side_by_side.md` (steps k-2..k+2 in all three renderings for 3 runs, auditor answers, tokens and bytes per format), `scores.csv`.

Total to pilot: items 1-8 = 56 h (about 37 h base), item 0 = 9 h, reading capped at 9 h (3 weeks x 3 h): expected about 74 h with buffer, about 25 h a week, to be measured in `hours.csv`. Weeks 4-12 are estimated in section 5.

## 4. Go / no-go after the pilot (end of week 3)

By eye:
- Diff arm shows no message list and reads differently from the log.
- Step ids identical across the three forms for the same event.
- PROV listing readable at the measured run length; auditor pointers resolve to real items.

Hard conditions (one fix attempt each; a second failure is NO-GO):
- Round trip (deep equality) ok on all 10 runs, all three formats.
- `test_no_leak.py` green on all 10 runs and renderings.
- Spend to date plus projected remaining at most 100 USD. Terms: generation (measured USD per clean run x candidates still to run, at most 120 minus those run in week 2, plus USD per continuation x 300 live continuations, 240 at 40 tasks; the 25 clean controls exist and the 20 sham runs replay from cache); sweep audits (mean input and output tokens x 3 formats x 345 runs plus 345 fourth-arm requests, batched prices); contingency (3-sample rule: 60 runs x 3 formats x 2 extra samples = 360 requests); development (18 live continuations of the 21 week-4 validation runs, the 3 sham validation runs replay from cache; 30 pilot re-audits; 31 D-003c re-generation runs). If over 100: apply the cut order, re-project once; still over is NO-GO. The 50 USD up to the 150 USD cap is headroom for re-runs and the Sonnet fallback, never planned spend.

Conditions with a defined action, not NO-GO by themselves:
- Structural check of section 3, step 5 passes; token overlap log vs diff and log vs PROV reported as numbers (expected high by design; no threshold).
- Auditor JSON parses on at least 90 percent of calls and returns `none` on most clean and sham runs. If not: one prompt or schema fix (still exploratory), re-run the 30 calls; if still below, activate the fallback auditor and re-run the cost gate; if the fallback also fails, NO-GO.
- Hours logged at most 74 (section 3 total, admin and reading included). Over 74: apply the cut order now and tell the supervisor. Over 100 (one extra week gone): NO-GO.
- Deprecations re-checked: Haiku 4.5 available with no retirement date before the end of week 8. Otherwise D-003c fires (switch both models, re-generate the development runs, re-run the probe) and the cost gate is re-run with Sonnet prices.

Sanity check, not a GO condition: one format beats the position-only guesser on the 4 faulty runs (n = 4 proves nothing).

NO-GO: switch to Idea C on the same harness (bytes per step, rebuild ms, interval sweep), tell the supervisor, log it. On GO: update prereg with pilot fixes; the `prereg-v1` tag comes at the end of week 4, not here.

## 5. Weeks 4-12

Hours per week are buffered (base x 1.5) plus capped reading; to be measured in `hours.csv`. Whole plan: expected about 226 h buffered (about 155 h base), about 19 h a week. Hour gates: cumulative at most 102 h at `prereg-v1`, 151 h at the end of week 7, 169 h at `analysis-frozen`; more than 15 percent over the line at any Friday status triggers the next cut.

- Week 4 (28 h; 17 h base plus 2 h reading), the densest week: complete injector (7 rows incl. sham x 3 k strata = 21 validation runs on the 5 development tasks; byte-diff rule of section 3, step 6 on all 21; 6 h base); fourth-arm renderer `render/inferred.py` with its format note and hash (3 h); R and lme4 (`which brew` first, Homebrew was not checked; if present `brew install r`, else the CRAN macOS installer; `install.packages("lme4")`; save R and lme4 versions), `analysis/simulate.py` writing `analysis/sim_null.csv` and `analysis/sim_effect.csv` (same columns as `analysis/schema.md`, 50 tasks, 10-point planted margins), then `analysis/primary.R` with the exact formula run on both CSVs, convergence and fallback rule recorded in prereg (4 h); `prereg/power.md` for 40 and 50 tasks (2 h); prereg final with all four prompt hashes and the three outcome branches as bullets (2 h); deprecations check; tag `prereg-v1`, email the tag.
- Week 5 (25 h; 16 h base plus 1 h reading): `analysis/analyze.py` end-to-end on the simulated CSVs (3 h); native recorders (callback handler per section 8, row 7: prompt hash by joining `on_chat_model_start` and `on_llm_end` on run_id, tool inputs from `on_tool_start`, results linked by tool_call_id; SqliteSaver export with table inspection; inline PROV; 6 h); sha256 check of tool I/O; `evidence_present.csv` (7 x 3; 2 h); log rule auditor (2 h), diff and PROV rule auditors go to the cut list; structure-only guesser, both guessers run on the 21 validation runs (2 h); `paper/outcomes.md` written out from the prereg bullets (1 h). 2026-10-15 falls in this week: re-check deprecations.
- Week 6 (12 h; 8 h base, plus unattended machine time): deprecations check the day before; generate the sweep pool overnight with resume: clean runs in seed order from the first candidate not yet run until 55 have passed in total (5 development from week 2 plus 50 sweep; minimum 45 = 5 + 40), then 300 continuations (240 at the minimum) and 20 sham replays, 345 runs in all (285); bytes per step and rebuild ms; back up `cache/` and `results/` (zip or git-lfs); `docs/progress-week6.md` to supervisor. If generation finishes early, start the sweep here; this shortens exposure, but week 6 is also after 2026-10-15, so D-003c stays the real mitigation.
- Week 7 (12 h; 8 h base): deprecations check the day before; Batch sweep, expected 1,380 requests at 50 tasks (1,035 primary, 345 fourth arm; 1,140 at 40 tasks), `custom_id = run_id|format`, one model for the whole sweep; plus 30 pilot re-audits with the frozen prompt, flagged is_development, reported separately; shuffled labels scored offline; back up `cache/` and `results/`; stretch items only if on schedule.
- Week 8 (18 h; 12 h base): primary analysis in R over three formats, bootstrap, secondary models (length, k_bin, fourth-arm contrast), controls table incl. false-alarm comparison, k distribution per fault type, accuracy vs length plot; tag `analysis-frozen`; `results/deviations.md`.
- Week 9 (15 h; 10 h base): results and discussion drafts along the outcome branch of section 10; TraceElephant paragraph reused.
- Week 10 (21 h; 14 h base): full draft; related work from `related-work-table.csv`; limitations (single agent, agent and auditor share a model, renderings not architectures, judge noise, preprint dependence, length confound); data statement and AI-tool declaration inserted.
- Week 11 (12 h; 8 h base): citation audit (arXiv id resolves to title, venues confirmed, every quoted number checked); November arXiv watch; draft to supervisor.
- Week 12 (9 h; 6 h base): buffer; supervisor comments; fresh-clone reproducibility pass; tag `v1.0-submitted`.

Cut order if behind: (1) native-arm LLM audits, (2) diff and PROV rule auditors, (3) second-family auditor (the 60-run fallback re-audit), (4) rebuild-timing extras, (5) fourth arm reduced to evidence-fault runs plus controls. Never cut: three lossless formats, controls, 40 tasks, the primary test.

## 6. Supervisor meeting

Questions, in order:
1. Deadline, page limit, template, language (German or English)?
2. Must code and data be released? May the pre-registration tag be public?
3. Is an LLM-auditor accuracy study "NLP enough", or do you prefer a deterministic measurement study (Idea C)?
4. Do three lossless renderings of one LangGraph run, plus as-shipped recorders as a secondary arm, count as "controlled workflow applied consistently"?
5. Is a clean, well-controlled null result acceptable for a good grade?
6. Is one headline audit task (failure localization) plus short sections on the others acceptable?
7. Will you read the one-page pre-registration before the full run? Are check-ins in weeks 3, 6 and 11 fine?
8. What are the rules on declaring AI tools used in research and writing?
9. Which citation style, and may arXiv preprints be primary sources?
10. May the 40-step tier and the privacy axis shrink to a discussion paragraph, given the exposé promised six audit tasks, four axes and a 40-step tier?
11. Is a formal ethics or data declaration required for public benchmark text?

Two options to present:
- Option D (primary): Record Format x Fault Type. Expected 40-100 USD total spend (generation with Haiku 4.5 as agent plus audits, input and output); the go/no-go gate holds spend to date plus projection to the same 100 USD bound; 150 USD hard cap, the 50 USD between is headroom for re-runs and the Sonnet fallback; per-run cost measured in section 3, steps 3 and 6; 12 weeks; real NLP via the LLM auditor; medium risk.
- Option C (fallback, same harness): Snapshot Interval Dial. Expected 10-40 USD (generation only), to be measured in section 3, step 3; 6-8 weeks; no LLM auditor; lowest risk. Chosen if the deadline is nearer or the pilot fails.

If no meeting by Friday: email the brief, state assumptions (English, about 20 pages, deadline end of week 12, code released) and the date you proceed on them.

## 7. Reading list

Venue labels are provisional until the week-11 citation audit.

| Paper | Read | Extract |
|---|---|---|
| TraceElephant (ACL 2026, unverified; 2604.22708) | Sec. 3.3-3.4, Tables 2-3 | Step accuracies 16 / 28.1 / 33.3; what varied, what was fixed; positioning paragraph (max 180 words) |
| Who&When Pro (2607.09996) | Sec. 3, App. C Table 5 | Warm-start recipe as numbered steps; 18-mode taxonomy (17 in released yaml); length-degradation confound |
| Who&When (ICML 2025, unverified; 2505.00212) | Sec. 2-3 | Decisive-step definition; step-accuracy metric |
| GRADE (2606.22741) | Sec. 2.1, README | Edge grades; cite execution-layer results only; withdrawn dependency claim |
| PROV-AGENT (e-Science 2025, unverified; 2508.02866) | Sec. III | Node/edge vocabulary; state wasDerivedFrom is your addition |
| CatchBench (2608.22808) | Controls section | Position-only leak; guesser and shuffled labels |
| TRAIL (2505.08638) | Sec. 3 | Category F1 and joint metric |
| LongRCA (2608.15242) | Metric only | +/-k window; +/-3 for the expected 20-26 step runs, confirmed at the measured length |
| The Replay Gap (2608.08239) | Abstract, metrics | Noise floor for rebuild extras |
| Elnozahy 2002 | Taxonomy, comparison | Log-based vs checkpoint-based framing |
| From Agent Traces to Trust (2606.04990) | Skim | Three-family vocabulary |

Cap reading at 3 hours a week in weeks 1-3, 2 h in week 4, 1 h in week 5. Defer other skims until results exist.

## 8. Fact-check results (10 claims)

| # | Claim | Status | Corrected fact | Source |
|---|---|---|---|---|
| 1 | Python >= 3.10 needed; Mac default 3.9.6 | Verified | uv already has CPython 3.13.14; use it, skip the 3.12 install | `uv python list --only-installed`; https://pypi.org/pypi/langgraph/json |
| 2 | SqliteSaver.from_conn_string is a context manager; StateSnapshot fields | Verified | Docs construct `SqliteSaver(sqlite3.connect(...))`; context-manager form is in the source docstring; metadata = {source, step, parents}, no 'writes' | https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py; live run 1.2.11 |
| 3 | dgslibisey/MuSiQue, about 2,417 validation rows | Verified | Exactly 2,417 (2hop 1,252; 3hop 760; 4hop 405); sub-prefixes 3hop1/2, 4hop1/2/3; no dataset card, split inferred from filename; Ans only | https://huggingface.co/datasets/dgslibisey/MuSiQue/resolve/main/musique_ans_v1.0_dev.jsonl |
| 4 | prov 2.x has wasDerivedFrom and JSON; prov_to_dot needs pydot plus Graphviz | Corrected | Current prov is 3.2.1 (2.x legacy ends at 2.5.3; both need Python >= 3.10); bare JSON only from 2.4.0; 3.x needs `prov[dot]`; Graphviz only for write_png/pdf/svg | https://pypi.org/pypi/prov/json; live tests 2.2.0, 2.5.3, 3.2.1 |
| 5 | jsonpatch.make_patch round-trips exactly | Corrected | About 0.7 percent of nested dict+list diffs fail or apply wrongly (move-op reindexing, issue #138, PR #175 open); dict-only: 0 failures; assert and fall back | https://github.com/stefankoegl/python-json-patch/issues/138; fuzz, jsonpatch 1.33 |
| 6 | Haiku 4.5 at 1/5 USD per MTok, temperature ok, Batch halves price; 1,260 audits about 13 USD | Verified | 13 USD is input only; output 5 USD per MTok (2.50 batched) adds about 6.30 USD per pass at 1k output tokens; temperature or top_p, not both; Sonnet 5 and Opus 5 reject non-default sampling (SDK 1.x TypeError); alias = claude-haiku-4-5-20251001; retirement not sooner than 2026-10-15; live usage check not run | https://platform.claude.com/docs/en/about-claude/pricing; https://platform.claude.com/docs/en/models/haiku-4-5/overview |
| 7 | on_tool_end and on_llm_end suffice for the native log | Verified signatures; use corrected | Prompt only in on_chat_model_start (join by run_id); tool inputs only in on_tool_start; link tool results by tool_call_id, not parent_run_id; output is a ToolMessage inside ToolNode; usage in llm_output or usage_metadata | https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/callbacks/base.py; live run |
| 8 | Who&When Pro repo documents warm-start injection, 18 modes | Corrected | github.com/ag2ai/whowhen_pro (whowhenpro/whowhen_pro redirects) is the eval harness only; injection pipeline unreleased; HF taxonomy.yaml has 17 modes; 18 is from the paper App. C Table 5 | https://github.com/ag2ai/whowhen_pro; https://huggingface.co/datasets/Leoxx/whowhen_pro/resolve/main/taxonomy.yaml |
| 9 | lme4::glmer fits binomial GLMM; statsmodels only Bayesian | Verified | R not installed (`which R Rscript`); Homebrew not checked; statsmodels BinomialBayesMixedGLM allows crossed intercepts via vc_formulas but no frequentist p-values or LRT; glmmTMB is an alternative | https://rdrr.io/cran/lme4/man/glmer.html; https://www.statsmodels.org/stable/mixed_glm.html |
| 10 | MuSiQue 3/4-hop gives 18-24 steps, HotpotQA 12 | Corrected | Unmeasured projection, no agent or runs exist; arithmetic gives 20 (3-hop), 26 (4-hop), 14 (HotpotQA); depends on node design; dev set is 52 percent 2-hop; measure in the 5 clean runs | `find /Users/ahmad/Downloads/term-paper -name "*.py"` (empty); research/README-research-directions.md line 52 |

## 9. Risks and the one control that answers each

- Injection leaks position or shape: position-only and structure-only guessers (built before the sweep) near chance; k distribution per fault type reported.
- Gold labels leak: `test_no_leak.py` on every run and rendering.
- Diff arm collapses into the log: structural check (header plus jsonpatch ops only, no message list, distinct `render_hash` per format) in the pilot; token overlap reported, not gated, because lossless renderings share content by design.
- A rendering is not lossless: deep-equality round trip, all three formats, tool I/O carried in `calls[step_id]`.
- Record lacks evidence: log rule auditor plus the 7 x 3 evidence-present matrix.
- Something other than the fault differs: faulty runs, byte-diff clean vs faulty = 0 lines before k (from k on the record differs by design); sham runs, byte-diff 0 on every record file, only `truth.json` differs, false-alarm rate equal to clean.
- Auditor noise at temperature 0: 30-call Batch probe, pre-set 95 percent rule, agreement reported as noise floor.
- Format effect is a length effect: log(tokens_in) covariate, accuracy-vs-length plot.
- Post-hoc analysis choices: `prereg-v1` at end of week 4 with all four prompt hashes, before generation and sweep; pilot audits excluded; development runs flagged; `results/deviations.md`.
- Too few runs or tasks: paired design, one interaction test over three formats, cluster bootstrap, power file for 40 and 50 tasks; 120 candidates, a defined gate, pass rate projected in week 2, logged fallback.
- Budget overrun: 150 USD cap, gate at 100 USD total (spent plus projected), Batch API, `max_tokens` 1024, cost gate incl. the 3-sample contingency and D-003c re-generation.
- Model retired mid-project (2026-10-15 falls in week 5, before generation and both possible sweep weeks): pinned `claude-haiku-4-5-20251001` for agent and auditor, model string stored per response, deprecations checked at five dates, D-003c switch-and-regenerate rule (31 costed runs; sweep runs kept if already generated), fallback `claude-sonnet-5`, one model per sweep, every response cached.
- Auditor judges its own model's traces: stated in limitations; 60-run fallback re-audit as stretch item.
- Laptop loss or hours slip: private remote pushed at every tag, `cache/` and `results/` backed up after weeks 6 and 7; 50 percent buffer, `hours.csv`, 74 h gate at go/no-go, hour gates at 102 / 151 / 169 h, cut order.
- "Not real architectures": as-shipped recorders in the secondary arm, family-to-system table, limitation stated openly.
- Wrong or fabricated citations: `do-not-cite.md`, provisional venue labels, week-11 mechanical id audit.

## 10. What a null result means for the paper

- Definition: interaction not significant and every predicted paired margin's 95 percent CI inside +/-10 points (TOST equivalence against the smallest effect of interest). If CIs cross +/-10, the study is underpowered, not null; say so and cite the power file.
- Three outcome branches, half a page each, outlined as bullets in `prereg-v1` (week 4) and written out in week 5 in `paper/outcomes.md`: confirm (formats differ by fault class as predicted; choose record form by expected fault); one format dominates (structure matters, not as predicted; report which and why, e.g. length or pointer grammar); null (with information held equal, record form does not change a cheap auditor's accuracy; coverage matters).
- What carries the paper if null: the 7 x 3 evidence-present matrix, bytes per step and rebuild ms from the same harness, the false-alarm and guesser controls, the reusable injection harness with byte-diff proof.
- Framing for question 5: a pre-registered null with equivalence bounds is a finding, not a failure.