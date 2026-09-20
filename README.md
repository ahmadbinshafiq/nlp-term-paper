# Term paper: Comparing Auditable Architectures for LLM Agents

Does the best audit-record format (event log, state diffs, PROV graph) depend on the kind of fault?

- Plan: `research/next-steps.md`. Decisions: `DECISIONS.md`. Event format: `docs/schema.md`.
- All models run locally on Ollama (`glm-4.7-flash:q8_0`). No API key is needed.

```bash
uv sync                                     # install the environment
uv run pytest                               # tests, including the gold-label leak check
uv run python code/scripts/smoke_test.py    # needs Ollama running
uv run python code/scripts/make_tasks.py    # needs data/raw/musique_ans_v1.0_dev.jsonl (see DECISIONS.md, D-002)
uv run python code/scripts/bm25_recall.py
```
