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
