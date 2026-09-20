# Methods (outline, `methods-v0`)

Headings and one-line notes only. Text is written in weeks 9 and 10. Keys in [brackets] are from `paper/references.bib`.

## 1. Overview
One agent, one event stream, three record formats, one auditor, planted faults with known position.

## 2. The three record families and the systems that stand for them

| Family (exposé) | What it keeps | Real system we use in the native arm | Status |
|---|---|---|---|
| Log-primary | an append-only list of events; state is rebuilt by replay | LangGraph callback handler writing JSONL | design [logistheagent2026], recorder to be written in week 5 |
| Checkpoint-based | a snapshot of the state after each step | LangGraph `SqliteSaver` | provisional until its `checkpoints` and `writes` tables are inspected (week 5) |
| Provenance-overlay | a graph of what used and produced what (W3C PROV) | Python `prov` library, vocabulary of PROV-AGENT [provagent2025, provdm2013] | `wasDerivedFrom` between note and passage is our addition; PROV-AGENT does not record it |

Note for the text: the main study compares three *formats* of one recorded run with equal information. The native arm above is a separate coverage check. Say this early and plainly (pre-registration, section 11).

## 3. Task and data
MuSiQue-Ans, 3 and 4 hops, 120 candidates, seed 0 [musique2022]. Pooled passage corpus, BM25 [robertson2009bm25]. Recall at top 3 = 0.870 (`DECISIONS.md`, D-002). Data statement: `docs/data-statement.md`.

## 4. The agent
LangGraph loop of think and act steps. Rounds of search, read, write_note; then finish. Each act is one JSON action that Ollama forces to fit a schema of the allowed tools. Four tools and their state effects: `docs/schema.md`. Model, options, version freeze: `DECISIONS.md` D-003 [glm47flash, ollama, langgraph].

## 5. The canonical event stream
Five fields per event. Application state and JSON Patch. Why nothing lives only in chat messages. Content-addressed cache and byte-identical replay.

## 6. Clean runs and the gate
Gate checks (D-006). Development pool (5 tasks) and sweep pool (up to 50). Pass rate and reasons for failing.

## 7. Planting faults
Warm-start injection: replay to step k, plant one fault, continue live [whowhenpro2026; differences in `papers/injection-recipe-notes.md`]. Six faults in three classes plus sham: `prereg/fault_catalogue.md`. Formula for k and the hook tool. Proof that only the fault differs (byte-identical prefix).

## 8. The three renderings
Event log with effect lines; state diffs (JSON Patch per step); PROV graph. Round-trip test = the formats hold the same information. Fourth arm: log plus inferred edges [grade2026 for the idea of graded edges].

## 9. The auditor
Model and options. Shared prompt plus syntax-only reading notes. JSON answer. Second auditor on a 60-run subsample.

## 10. Measures
Exact step match (primary) [whowhen2025]; within 3 steps [longrca2026]; fault-class F1 [trail2025]; false alarms and misses; tokens, bytes, seconds.

## 11. Controls
Sham check, position-only guesser, structure-only guesser and rule baseline, shuffled labels [catchbench2026 for artifact controls]; leak test; round trip.

## 12. Analysis
Mixed-effects logistic regression [bates2015lme4]; likelihood-ratio test of the interaction; paired margins with task bootstrap; decision tree; equivalence bound from the power simulation [lakens2017tost]. Pre-registration and deviations.

## 13. Closest work and what differs
TraceElephant varies how complete a record is, not its form [traceelephant2026]. TelemetrySuffBench masks attributes on synthetic traces [telemetrysuffbench2026]. Adaptive Influence Graphs builds graphs after the fact [aig2026]. Survey that lists the comparison as open [tracestotrust2026].
