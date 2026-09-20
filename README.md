# Term paper: Comparing Auditable Architectures for LLM Agents

Does the best audit-record format (event log, state diffs, PROV graph) depend on the kind of fault?

- Plan: `research/next-steps.md`. Decisions: `DECISIONS.md`. Event format: `docs/schema.md`.
- All models run locally on Ollama (`glm-4.7-flash:q8_0`). No API key is needed.

```bash
uv sync                                       # install the environment
uv run pytest                                 # all tests; no model needed
uv run python code/scripts/make_tasks.py      # needs data/raw/musique_ans_v1.0_dev.jsonl (see DECISIONS.md, D-002)
uv run python code/scripts/bm25_recall.py     # search quality on the task pool; no model needed
uv run python code/scripts/smoke_test.py      # calls the model: Ollama must be running
uv run python code/scripts/run_clean.py       # calls the model: clean agent runs until 55 tasks pass the gate
uv run python code/scripts/roundtrip.py       # checks the three record formats on every saved run; no model needed
```

Where to read: `docs/schema.md` (the event format), `code/auditarch/agent.py` (the agent), `code/auditarch/render/` (the three formats),
`prereg/` (pre-registration and fault catalogue), `DECISIONS.md` (every decision, in order).
