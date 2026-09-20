# Decisions log

One entry per decision. Never edit an old entry; add a new one that replaces it.
The plan these entries refer to is `research/next-steps.md`.

Remote: https://github.com/ahmadbinshafiq/nlp-term-paper (private). Push at every tag.

## D-001 (2026-09-15) Research idea

Primary: Idea D, "Record Format x Fault Type". Fallback: Idea C, "Snapshot Interval Dial", on the same harness.
The fallback is taken if the week-3 go/no-go check fails or the deadline turns out to be close.

## D-003 (2026-09-20) Models: local only, no paid API

- Runtime: Ollama 0.33.2 (desktop app) on an Apple M4 Pro with 48 GB RAM.
- Agent and primary auditor: `glm-4.7-flash:q8_0`,
  digest `a035bf4bc812e1408631c2d2b14581b99dfe39f71d895aceb269b4a886080196` (31.8 GB, Q8_0, 29.9B parameters, MIT).
- Options for every call: temperature 0, seed 0, `think: false`, `num_predict` 1024, `num_ctx` 16384
  (to be fixed for good in week 3, after the longest rendering is measured), one request at a time.
- Second auditor: `qwen3.8:27b` (download was still running when this was logged; digest and smoke test to be added as D-003d).
- D-003b (if too few tasks pass the gate): thinking on for the agent, then `qwen3.8:27b` as agent. GLM stays the primary auditor.
- D-003c (version freeze): no Ollama update and no re-pull of a pinned model until the tag `analysis-frozen`.
  Every model response is stored with the Ollama version and the model digest, so a silent change is visible.
- Planned API spend: 0 USD.

Why: no budget for cloud models right now; pinned open weights cannot be retired and anyone can re-run them.

## D-002 (2026-09-20) Corpus and retrieval, logged BEFORE recall was measured

- Source file: `musique_ans_v1.0_dev.jsonl` from the Hugging Face dataset `dgslibisey/MuSiQue`,
  sha256 `15fa63794d18a94ce12411aca6e2327e65b6e83b0b1490efab3f1962e48abf3b`, 2,417 rows.
  Downloaded with `hf download`; the `datasets` package is not used (one plain JSONL file is enough).
- Candidates: ids that start with `3hop` or `4hop` (1,165 rows). Sample: `random.Random(0).sample(sorted(ids), 120)`.
  The order of that sample is the "seed order" used everywhere else. The result is saved in `data/tasks.jsonl`, so it stays fixed.
- Split: `data/tasks.jsonl` holds only what the agent may see (id, question, paragraphs with idx, pid, title, text).
  `data/gold.jsonl` holds everything else (answer, aliases, supporting paragraphs, decomposition).
- Pooled corpus: all paragraphs of the 120 sampled tasks in one pool (about 20 x 120). Paragraphs with the same title and text are merged.
  Passage id: `pid` = first 12 hex characters of sha1(title + newline + text). Entity id in records: `ent:passage:<pid>`.
- Retriever: BM25Okapi from `rank-bm25` 0.2.2 with its default settings. Document = title + space + text.
  Tokens: lowercase, accents stripped, split on anything that is not a letter or digit. No stop-word list, no stemming.
- Recall measure: for each sub-question in the gold decomposition, every `#n` is replaced by the gold answer of sub-question n.
  That text is the query. A hit means the gold supporting passage is in the top 3. Top 5 and top 10 are reported too, for information only.
  This is an upper-bound style check: a real agent writes its own queries, which may be better or worse.
- Gate (from the plan): top-3 recall over sub-questions above 0.8 means MuSiQue stays. Otherwise the choice of dataset is discussed again (HotpotQA is the named alternative).

## D-004 (2026-09-20) Calendar (proposed, change it if your deadline says otherwise)

The plan was written with week 1 starting on 2026-09-15, but no work started that week.
Week 1 now starts on Monday 2026-09-21. Week 3 (pilot and go/no-go) ends on 2026-10-11, week 4 (`prereg-v1`) on 2026-10-18, week 12 on 2026-12-13.

## D-002 result (2026-09-20) BM25 recall, measured after D-002 was logged

Command: `uv run python code/scripts/bm25_recall.py`. 120 tasks (81 with 3 hops, 39 with 4 hops), 2,400 paragraphs, 1,673 unique passages in the pool, 399 sub-questions.

| Measure | Value |
|---|---|
| recall at top 3 (the gate) | 0.870 (347/399) |
| recall at top 5 | 0.912 (364/399) |
| recall at top 10 | 0.940 (375/399) |
| recall at top 3, 3-hop tasks | 0.885 (215/243) |
| recall at top 3, 4-hop tasks | 0.846 (132/156) |
| tasks where every sub-question is a top-3 hit | 77 of 120 |

Decision: 0.870 is above 0.8, so MuSiQue stays. HotpotQA is not needed.
Watch in week 2: only 77 of 120 tasks have every hop in the top 3 with these gold-style queries, and 55 tasks must pass the gate.
An agent can search again with other words, so 77 is not a hard ceiling, but the week-2 pass rate is the number that decides.
Open option, not taken: let `search` return the top 5 (recall 0.912). It would have to be decided before the clean runs in week 2.

## Status 2026-09-20 (before week 1)

- Done: repo skeleton, `uv` environment with `uv.lock`, smoke test (StateSnapshot, PROV-JSON with wasDerivedFrom, tool call, auditor JSON), 120-task slice, leak test, BM25 recall gate passed, `docs/schema.md`, `docs/data-statement.md`, `docs/compute.md`, `docs/supervisor-brief.md`, `code/auditarch/schema.py` with fold/unfold tests (11 tests green).
- Not done yet from week 1: supervisor email (yours to send), `prereg/preregistration.md` v0, `prereg/fault_catalogue.md`, `analysis/schema.md`, reading kit, Qwen smoke test (download still running).
- Hours: `hours.csv` is empty; fill in your own hours.

## D-003d (2026-09-20) Second auditor pinned

`qwen3.8:27b`, digest `22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643` (17.7 GB, Q4_K_M, 27.3B dense, Apache 2.0).
Probe passed: two correct tool-call turns, auditor JSON parsed and named the planted step, 3 repeats byte-identical.
Speed: about 110 tokens per second reading and 8-12 writing, so 4 to 5 times slower than GLM. Fine for the 180 second-auditor calls (about 5 hours), too slow to be the primary auditor for 1,380 calls unless GLM fails.
`gpt-oss:20b` is no longer needed as a stand-in.

## D-005 (2026-09-20) Tool behaviour (must hold before the first clean run in week 2)

- `search` returns a list of `{handle, title}`, not bare handles. Titles are already visible to the agent in `tasks.jsonl`, so nothing leaks. Without titles, a corrupted search result could not be seen at step k in any format.
- The tools never raise. `finish` is always the last step. If the named note does not exist, `finish` returns `ok` and writes `cited_pid: null`. An error line at the last step would be a loud position cue and would point the auditor at the symptom, not the cause.

## D-006 (2026-09-20) Gate for clean runs (proposed; confirm before week 2, because it changes the pass rate)

The plan's gate (correct answer, finished within the step cap, one cited passage) plus mechanical checks:
the `note_key` given to `finish` exists; the final `cited_pid` is a gold supporting passage; no note key is written twice; no `source_pid` is null; every `source_pid` was read before its note; and all six faults can be built in the run (catalogue, rule 5).
Why: a "clean" run that already holds one of our fault patterns would break the ground truth. An auditor that flags it would be right and still be scored wrong.
If fewer than 45 tasks are projected to pass: drop "correct answer" and "cited_pid is gold" from the gate and keep them as covariates; then D-003b.
Week 2 must report how many correct runs fail only the new checks.

## D-007 (2026-09-20) Outcome labels and the equivalence bound (proposed; discuss with the supervisor, question 5)

- The plan's three outcome branches overlapped and left gaps (example: one format best everywhere by 1 point was both "null" and "refuted"). The pre-registration now has seven labels walked in a fixed order: not interpretable, one format dominates, confirmed, partly confirmed, another interaction, null, underpowered.
- A margin "meets the rule" only if it is at least 10 points, its 95 percent interval is above zero, and the predicted format is the best one in its class.
- Power problem found by two reviewers and re-checked by simulation: with 50 tasks one margin has a standard error of about 5.5 points, so a 95 percent interval is about +/-11 points wide. "All intervals inside +/-10" can then almost never happen, and the plan's promise of a reportable null result could not be kept. The chance that all three margins pass is about 0.08 if the true margins are 10 points, 0.46 at 15, 0.85 at 20.
- Rule adopted: `prereg/power.md` (week 4) simulates the whole decision tree. The bound B is the smallest of 10, 15, 20 points that gives at least 0.80 chance of "Null" when the true margins are 0; else B = 20 with the chance printed. The Null label uses 90 percent intervals (the usual equivalence test). This departs from sections 2 and 10 of the plan.
- Open option, not taken yet: compute is free now, so the number of faulty runs could be doubled (two k per task and fault, 600 runs, 1,800 primary audits, about twice the machine time). That would shrink the intervals by up to about 30 percent. To be decided with the power file in week 4, before the tag.

## D-008 (2026-09-20) Selection rules and new result columns

- k and the hook tool are set by a formula from the task position and the fault row (catalogue, rule 5). Nothing is drawn at random.
- Clean controls: the first 25 sweep tasks in seed order. Sham controls: the last 20. The sham check is a hash check; the false-alarm rate is reported over all distinct no-fault tasks.
- The 60-run subsample (second auditor, 3-repeat rule, thinking-on re-audit) = the 6 faulty runs of the first 10 sweep tasks in seed order.
- New columns in `analysis/schema.md`: `hook_tool`, `n_steps`, `rel_pos`, `auditor_role`.

## Status 2026-09-20, evening (week-1 items 8 to 10 done)

- Done: `prereg/preregistration.md` v0.1 and `prereg/fault_catalogue.md` v0.1 (both revised after a four-reviewer check), `analysis/schema.md`, reading kit (`paper/references.bib` with 36 entries read from their primary sources and re-checked, `papers/do-not-cite.md`, `papers/injection-recipe-notes.md`, Gupta PDF moved to `papers/untrusted/`).
- Found while checking: Ollama's newest release is 0.34.2 (2026-09-15). The study is pinned to 0.33.2, so the desktop app will offer an update. Do not accept it before the tag `analysis-frozen` (rule D-003c). `code/auditarch/llm.py` stops every run if the version differs.
- Still open from week 1: supervisor email (yours), `OLLAMA_NUM_PARALLEL=1` and auto-update off (your machine), your hours in `hours.csv`, your reading (3 h), Friday status entry.
- To confirm before week 2 starts: D-005 (tool behaviour), D-006 (gate). To discuss with the supervisor: D-007 (outcome labels, power).

## D-005 and D-006 confirmed (2026-09-20)

Confirmed by Ahmad after reading the plain-English explanation. D-006 is no longer "proposed": it is the gate for week 2. D-007 stays open until the supervisor meeting.

## D-009 (2026-09-20) Week-2 build choices (one entry, because they came out of one round of trials on the first 40 tasks)

- **JSON actions and rounds.** Each act is one JSON action, and Ollama forces it to fit a schema of the tools allowed at that point. Native tool calling failed too often (the model named tools that were not offered, or wrote broken call markup). The agent works in rounds: search, read, write_note; after a note it may search or finish; after a refused read it may read another result or search again.
- **Tools refuse repeats.** A repeated query, a second read of the same passage and an existing note key return `{"error": ...}` and change nothing. This replaces the search part of D-005. Effect on the gate: a note key can no longer be written twice in a clean run.
- **Search returns 5 results** as `{handle, title, snippet}` (first 200 characters). D-002 listed top 5 as an option; it is now taken. Titles alone were not enough to choose a passage.
- **Step cap 38** = six rounds of six steps plus think and finish. With 30, a 4-hop task with one wasted round was cut off one step before `finish`.
- **Answer check of the gate:** equal after normalization, or one answer is a run of whole words inside the other; number words count as digits ("two" = "2"). MuSiQue gold answers are often long phrases ("usually in the summer or fall").
- **Think turns** carry stop strings (`THINK_STOP` in `llm.py`) so that a think text cannot run on into the next action. Act turns carry the JSON schema. All other options are as in D-003.
- **PROV ids** are `step:4`, `passage:<pid>`, `note:<key>@<step>`, `thought:<step>`, `answer:<step>`. The PROV rendering is PROV-N text, and the round trip reads that text back.
- A four-reviewer code check (38 confirmed points) was applied: refused calls are never eligible for a fault, the event validator checks the exact copy of the call, the diff parser splits at line starts only, note keys with `/` or `~` work in PROV, a cut-off action ends the run instead of crashing the batch.

## D-010 (2026-09-20) The agent gets MuSiQue's sub-questions as a plan (confirmed by Ahmad)

- What: with each question the agent sees the dataset's own breakdown into sub-questions, without answers. Field `plan` in `data/tasks.jsonl`. Answers, aliases and supporting-passage labels stay in `data/gold.jsonl` and are never shown to a model.
- Why: on the same first 40 tasks the agent passed the gate 5 times without the plan (12 percent) and 12 times with it (30 percent). Without the plan, 4 of the 5 passing runs had fewer search rounds than the question has hops. The paper tests auditors, not question answering, and it needs regular runs.
- Honest note on the comparison: the two trial folders also differed in the think-turn stop strings, so the 12 against 30 percent is not a perfectly clean comparison. The gap is large, and the first trials without the plan (0 to 2 of 12) point the same way.
- To say in the paper (limitations): the agent is given the question decomposition; only tasks it solves cleanly enter the study.

## D-011 (2026-09-20) 250 candidate tasks instead of 120 (proposed by me; waiting for Ahmad's OK on the number)

- What: the first 120 tasks stay exactly as they were (D-002). 130 more are drawn with seed 0 from the remaining 3- and 4-hop tasks. The passage pool now covers all 250 tasks (2,795 unique passages).
- Why: at about 30 percent pass rate, 120 candidates give about 36 passing tasks; 55 are needed (5 development, 50 sweep). The cap of 120 came from the time when each run cost money. A run now costs about 55 seconds.
- BM25 recall on the larger pool (gold-style queries): 0.833 at top 3, 0.898 at top 5 (the agent gets 5), 0.939 at top 10.
- The pass rate over all candidates that were run is reported in the paper.

## D-011 confirmed (2026-09-20)

Ahmad confirmed 250 candidate tasks. D-011 is no longer "proposed".
