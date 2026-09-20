# What one audit record actually looks like, paper by paper

Compiled 2026-09-09 from the primary sources (arXiv HTML/PDF, GitHub repos, official docs).
Purpose: show the concrete record shape each system uses, so the three shapes chosen for the
term paper (event log, snapshot diff, provenance graph) can be compared against what exists.

Rules used: verbatim quotes kept under 40 words; longer samples reproduce the STRUCTURE
(field names, value types) with paraphrased values. Every image URL was checked HTTP 200 on 2026-09-09.
Where a paper has no figure image (inline SVG/vector), the PDF page is given instead.

Contents
1. Log family: Agent Flight Recorder, ActiveGraph, Who&When, AuditWeave
2. Span-tree and multi-resolution family: OpenInference, TRAIL, ECHO, TrajDebug, Deepchecks
3. Checkpoint / snapshot family: LangGraph checkpointer, AgentRewind, Crab, TraceElephant, Safe to Resume?
4. Graph family: PROV-AGENT/Flowcept, LEDGER, GRADE, AgentRx, Adaptive Influence Graphs, W3C PROV minimal example

---



<!-- ===== log-family ===== -->

# Log-family papers: what ONE audit record actually looks like

Scope note: only concrete artefacts (schemas, JSON, table rows, figures) are listed. Verbatim quotes are kept under 40 words; longer samples reproduce the structure with paraphrased values. All image URLs were checked with `curl -sI` on 2026-09-09 (status noted per item).

---

## 1. Agent Flight Recorder

- **Title:** Agent Flight Recorder: Tamper-Evident Audit Trails with On-Chain Anchoring for Long-Horizon Tool-Using Agents (Bindschaedler, Botha, Siebenbrunner)
- **arXiv:** 2609.01931 — https://arxiv.org/abs/2609.01931 — HTML: https://arxiv.org/html/2609.01931v1 — code: https://github.com/mpi-dsg/agent-flight-recorder

### Exact schema (as the paper names it)
Section III-B "Agent-Semantic Event Schema" (PDF p. 2) lists eight numbered fields per event:

| # | Field (paper name) | What it holds (paper's description, condensed) |
|---|---|---|
| 1 | Intent | proposed tool name + structured arguments; raw chain-of-thought deliberately excluded |
| 2 | Policy evaluation | which guardrail(s) ran, verdict (allow / deny / escalate), policy version |
| 3 | Human approval | whether a human approved, approver identity, approval prompt shown, timestamp |
| 4 | Execution | the concrete command / API call / mutation as dispatched |
| 5 | Effects | return value, state diff, external response, or error |
| 6 | Context provenance | retrieval sources consumed (with content hashes), upstream tool outputs, environment (dev / staging / prod) |
| 7 | Code provenance | agent binary hash, tool-wrapper hashes, skill/package hashes |
| 8 | Delegation provenance | requesting agent identity, parent event hash in requester's log, scope of delegated authority |

The paper also separates an **event payload** (the eight fields above) from an **event record** (fixed-size metadata: event ID, sequence number, payload hash, predecessor digest, cleartext tool name, timestamp, recorder identity) — Section III-C, p. 2-3. Serialization is deterministic CBOR (RFC 8949 §4.2), not JSON.

### Sample record
**The paper contains no JSON example event.** The closest thing in the paper is the eight-field list above plus the forensic-query field paths used in Section VI-F (p. 7): `policy_eval.rule == "destructive_command_check"`, `delegation.parent_event`, `context_provenance.environment`.

The concrete record structure is in the repo's `afr/schema.py` (dataclass `AgentEvent`, "One agent action in the tamper-evident log"). Field names and types, with paraphrased example values:

```
AgentEvent
  event_id:            str    # e.g. "0192ab...f3" (UUIDv7-style hex)
  timestamp_ms:        int    # e.g. 1757400000123
  sequence_number:     int    # e.g. 42
  session_id:          str    # e.g. "sess-7c1"
  intent:              dict   # e.g. {"tool": "shell", "args": {"cmd": "rm -rf /data"}}
  policy_eval:         dict   # e.g. {"rule": "destructive_command_check", "verdict": "escalate", "policy_version": "v3"}
  approval:            dict   # e.g. {"approved": true, "approver": "alice", "prompt": "...", "ts": ...}
  execution:           dict   # e.g. {"cmd": "rm -rf /data", "env": "production"}
  effects:             dict   # e.g. {"exit_code": 0, "stdout": "", "state_diff": ...}
  context_provenance:  dict   # e.g. {"sources": [{"uri": ..., "sha256": ...}], "environment": "production"}
  code_provenance:     dict   # e.g. {"agent_hash": ..., "tool_wrapper_hashes": {...}}
  delegation:          dict   # e.g. {"requesting_agent": "orgB/agent-2", "parent_event": "<hash>", "scope": "read-only"}
  prev_hash:           bytes  # SHA-256 of predecessor; 32 zero bytes for genesis
  logical_clock:       int    # monotonic counter
  concurrency_group:   str    # optional tag for co-issued calls
```
Hash = SHA-256 over canonical CBOR of the sorted dict (`event_hash()`).

### Figure
- **Fig. 1** (Section III-C, PDF p. 3): "Agent Flight Recorder architecture" — Agent → Flight Recorder [1. Event Schema → 2. Hash Chain → 3. Merkle Epoch] → On-Chain (anchor, 32-byte root) → Verifier outputs verified / tampered / incomplete.
- **Image URL:** none exists. The figure is TikZ rendered as inline SVG in the HTML (element `#S3.F1`), not a PNG. `https://arxiv.org/html/2609.01931v1/x1.png` → **HTTP 404**. Use the page anchor instead: https://arxiv.org/html/2609.01931v1#S3.F1 (page → **HTTP 200**), or the PDF p. 3.
- Field-table alternative: the numbered list in III-B (p. 2); comparison Table I (p. 4) is about anchoring mechanisms, not the record.

### Where
- Schema: Section III-B, PDF p. 2. Record-vs-payload split: III-C, pp. 2-3. Fig. 1: p. 3. Forensic field paths: VI-F, p. 7. Limitations: VIII-A, p. 8.

### What the record CANNOT show (paper's own words, VIII-A p. 8 and III-B p. 2)
- No raw model reasoning / chain-of-thought (excluded by design).
- Completeness: "If an action bypasses the instrumented gateway, the recorder never sees it." Missing events *within* an epoch are undetectable; only missing epochs are.
- Post-compromise entries cannot be trusted; captures "tool-call semantics, not model internals or out-of-band agent communication."

---

## 2. The Log is the Agent (ActiveGraph)

- **Title:** The Log is the Agent: Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems (Yohei Nakajima)
- **arXiv:** 2605.21997 — https://arxiv.org/abs/2605.21997 — HTML: https://arxiv.org/html/2605.21997v1 — code: https://github.com/yoheinakajima/activegraph
- Local PDF: `/Users/ahmad/Downloads/term-paper/papers/The Log is the Agent Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems.pdf` (11 pages)

### Exact event schema
Section 3 "Architecture", para "Events" (PDF p. 4): every event carries **`id`, `type`, `payload`, `actor`, an optional `caused_by` pointer, and a timestamp**.

Event **types** that appear in the paper (Listings 1-2, Fig. 1, §4):
`pack.loaded`, `goal.created`, `behavior.started`, `behavior.completed`, `object.created`, `llm.requested`, `llm.responded`, `tool.requested`, `tool.responded`, plus `relation` and `patch` events (Fig. 1 log strip: "goal object llm.req llm.resp object relation tool.req patch object …").

Objects created by events carry a **`provenance`** block with `created_by` (behavior name) and `caused_by_event`.

### Sample record (Listing 1, PDF pp. 4-5, "abridged from the captured 671-event log")
Structure reproduced; values paraphrased from the Northwind Robotics run:

```json
{
  "id": "evt_004",
  "type": "object.created",
  "actor": "diligence.company_planner",
  "caused_by": "evt_002",
  "payload": {
    "object": {
      "id": "company#1",
      "type": "company",
      "data": { "name": "<company name>" },
      "provenance": {
        "created_by": "diligence.company_planner",
        "caused_by_event": "evt_002"
      }
    }
  }
}
```
Listing 2 (p. 7) shows an `llm.requested` event whose payload has: `behavior`, `model`, `prompt_hash`, `deterministic: true`, `cache_hit: false`, `prompt {temperature 0.0, top_p 1.0, deterministic, output_schema_name}`, `estimated_cost_usd`. The response is stored under the same `prompt_hash` so replay serves it from cache.

### Worked example (diligence pack), §6 pp. 8-9
`activegraph quickstart` on three companies produces **671 events → 93 objects** (3 companies, 24 questions, 9 documents, 25 claims, 25 evidence, 1 contradiction, 3 risks, 3 memos) **and 76 relations via 103 model calls and 48 tool calls**, with no orchestration code. A claim object (e.g. a revenue-growth claim) carries a provenance block naming the behavior (`document_researcher`), the causing event, and the model-request event; typed relations `addresses` (question), `derived_from` (document), `supports` (evidence).

### Figure
- **Figure 1** (PDF p. 3): "The ActiveGraph runtime as a cycle." Bottom strip = append-only EVENT LOG (goal, object, llm.req, llm.resp, relation, tool.req, patch…); replay folds log → GRAPH (goal, company, question, claim, evidence, document with edges addresses / supports / derived_from); BEHAVIORS match graph patterns and emit events; side panel lists Replay, Fork + structural diff, Lineage.
- **Image URL:** none. In the PDF the figure is a vector Form XObject; the arXiv HTML `figure#S3.F1` contains only the caption (no `<img>`/`<svg>`). Link the page: https://arxiv.org/html/2605.21997v1#S3.F1 (HTTP 200) or PDF p. 3. Best "what a record looks like" artefacts are actually **Listing 1 (pp. 4-5) and Listing 2 (p. 7)**.

### Where
Events definition: §3, p. 4. Listing 1: pp. 4-5. Listing 2: §4, p. 7. Diligence example: §6, pp. 8-9. Table 1 (property comparison): p. 6. Limitations: §9, pp. 10-11.

### What the record CANNOT show (§3 p. 6, §9 pp. 10-11)
- Determinism is "never a claim that running the agent is reproducible"; a live model call is not reproducible, only its recorded response is.
- "a tool that mutates the outside world still mutates it on first execution, and only the record of that mutation replays deterministically."
- Determinism contract is not statically enforced; violations surface only at strict replay. Concurrent / distributed writers and multi-agent contention are unresolved; no hash chain or tamper-evidence is claimed.

---

## 3. Who&When (Agents_Failure_Attribution)

- **Title:** Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems (Zhang et al., ICML 2025 spotlight)
- **arXiv:** 2505.00212 — https://arxiv.org/abs/2505.00212 — HTML: https://arxiv.org/html/2505.00212v3 — code/data: https://github.com/mingyin1/Agents_Failure_Attribution ; HF: Kevin355/Who_and_When

### Exact record structure
§3 (PDF pp. 3-4) says each instance has four entries: **(1) Query, (2) Failure log** ("full conversation log of a specific system as it fails"), **(3) Agentic system information** (system prompts, tools, agent names — algorithm-generated only), **(4) Annotations** (responsible agent, failure step, plain-language reason).

Actual JSON keys in the repo (`Who&When/Algorithm-Generated/1.json`, `Who&When/Hand-Crafted/1.json`):

| Key | Type | Algorithm-Generated | Hand-Crafted (Magentic-One) |
|---|---|---|---|
| `question` | str | GAIA query | AssistantBench / GAIA query |
| `question_ID` | str | UUID | sha256 hex |
| `level` | str / null | "2" | null |
| `ground_truth` | str | "8" | "Renzo Gracie Jiu-Jitsu Wall Street" |
| `is_correct` / `is_corrected` | bool / null | false | null |
| `history` | list of turns | 6 turns; keys `content`, `name`, `role` | 29 turns; keys `content`, `role` |
| `system_prompt` | dict agent→prompt | present | absent |
| **`mistake_agent`** | str | "Excel_Expert" | "WebSurfer" |
| **`mistake_step`** | str (index into history) | "0" | "12" |
| **`mistake_reason`** | str | free text | free text |

### Sample log entry (one `history` turn) + annotation
Structure with paraphrased content (Hand-Crafted/1.json):
```json
"history": [
  {"role": "human",                  "content": "<user query: martial-arts classes near NYSE, 7-9 pm>"},
  {"role": "Orchestrator (thought)", "content": "Initial plan: ... Ask WebSurfer to search ..."},
  {"role": "Orchestrator (thought)", "content": "Updated Ledger: {\"is_request_satisfied\": {...}, ...}"},
  ...
],
"mistake_agent":  "WebSurfer",
"mistake_step":   "12",
"mistake_reason": "WebSurfer clicks on an irrelevant website and disrupts the task-solving process."
```
Algorithm-generated turns additionally carry `name` (e.g. `"Computer_terminal"`) and role `user`, with content like "exitcode: 0 (execution succeeded) Code output: ...".

### Figure
- **Figure 9** (Appendix C.3 "Data Example", PDF p. 14): "A task example from Who&When, where we annotate failure-responsible agents and their corresponding error steps ... Each annotation includes a natural language explanation." Two panels under one user query: (a) Algorithm-Generated — `DataManipulation_Expert:` / `Computer_terminal:` / `DataAnalysis_Expert:` speaker-prefixed transcript, decisive error highlighted red, green box with `"Failure_responsible_agent": "DataAnalysis_Expert"`, `"Decisive_error_step": "7"`, `"Reason": ...`; (b) Hand-Crafted — `Orchestrator:` / `Assistant:` transcript, green box `"Failure_responsible_agent": "Assistant"`, `"Decisive_error_step": "82"`.
- **Image URL:** https://arxiv.org/html/2505.00212v3/fig/data_example.png — **HTTP 200** (2406x1424 PNG).
- Also: annotation guideline Figure 10 (p. 15) https://arxiv.org/html/2505.00212v3/fig/guideline.png (200); overview Figure 1 https://arxiv.org/html/2505.00212v3/fig/overview.png (200).
- Note the figure's key names (`Failure_responsible_agent`, `Decisive_error_step`, `Reason`) differ from the dataset's actual keys (`mistake_agent`, `mistake_step`, `mistake_reason`).

### Where
Instance definition: §3, pp. 3-4. Annotation procedure (3 rounds, 3 experts): §3.2, p. 4. Formal definition of decisive error (i*, t*) = earliest (i,t) with Δ=1: §2, p. 3. Figure 9: Appendix C.3, p. 14. Annotation guideline: Appendix F, p. 15.

### What the record CANNOT show (§3.2 p. 4; §2 p. 3)
- The log is a plain chat transcript: no tool-call structure, no hashes, no timestamps, no integrity. Annotators had to "check the browser history and visit each website" manually because the log alone cannot tell whether information was unavailable or not retrieved.
- Annotation picks a single earliest decisive error even when "several agents" make mistakes; severity is "subtle and even subjective"; 15-30% of annotations were flagged uncertain.

---

## 4. AuditWeave

- **Title:** AuditWeave: A Tamper-Evident, Auditor-Navigable Evidence Layer for AI-Assisted and Data-Transformation Workflows (Vimal Nakrani)
- **arXiv:** 2607.09682 — https://arxiv.org/abs/2607.09682 — HTML: https://arxiv.org/html/2607.09682v1 — code: https://github.com/vimalnakrani08/auditweave ; PyPI `auditweave` 0.1.0

### Exact event vocabulary (§3.2 "Event model", PDF p. 3)
Six event types: **Source, Retrieval, Transformation, Inference, Decision, Attestation** (attestation = "a human reviewing and signing off on a prior event"). Each event records: **actor** (human / model / system component), **payload** (type-specific), optional **labels**, and **links** to upstream events (forms a provenance DAG). A source event may bind to the **SHA-256 hash** of a document instead of its contents.

Ledger fields (§3.3, pp. 3-4): each event stores the **hash of the previous event** and **its own hash**, computed over content including predecessor hash and **sequence position**.

Actual on-disk record (repo `src/auditweave/core/events.py`, `Event.to_dict()`; persisted one-per-line as JSONL by `store/jsonl.py`):

```
id          str   uuid4 hex
type        str   one of source|retrieval|transformation|inference|decision|attestation
timestamp   str   ISO-8601 UTC, second precision
sequence    int   position in trail (0-based)
actor       {name: str, kind: human|model|system, identifier?: str}
payload     dict  type-specific
links       [str] sorted upstream event ids
labels      {str: str}
prev_hash   str   sha256 hex of previous event; 64 zeros for genesis
hash        str   sha256 over canonical JSON of all fields above
```

### Sample ledger entry
**The paper has no JSON ledger entry.** Its only concrete record example is the code snippet in §3.3 (p. 4):
```python
rec = Recorder()
s = rec.source("ledger.csv", content_hash=...)
t = rec.transformation("aggregate by quarter", [s.id])
d = rec.decision("Q3 revenue = $4.2M", [t.id])
assert rec.trail.verify().ok
```
Reconstructed JSONL line for the `decision` event, following `to_dict()` (paraphrased values):
```json
{"actor":{"kind":"system","name":"pipeline"},"hash":"<sha256 of this line minus hash>",
 "id":"9f3c...","labels":{},"links":["<id of transformation t>"],
 "payload":{"statement":"Q3 revenue = $4.2M"},"prev_hash":"<hash of event t>",
 "sequence":2,"timestamp":"2026-06-14T10:00:00+00:00","type":"decision"}
```

### Figure
- No figure shows a record. Figures 1-3 (pp. 6-7) are performance/detection plots: Fig. 1 per-event cost vs trail size — https://arxiv.org/html/2607.09682v1/fig_scalability.png (200); Fig. 2 verify/trace time — https://arxiv.org/html/2607.09682v1/fig_verify_trace.png (200); Fig. 3 detection rate by mutation class (field edit / reorder / delete / insert, 500 trials each, 100%) — https://arxiv.org/html/2607.09682v1/fig_tamper.png (200).
- Closest schema artefact: the bulleted six-type list in §3.2 (p. 3) and Table 1 capability matrix (p. 2).

### Where
Definitions: §3.1, p. 3. Event model: §3.2, p. 3. Ledger + code snippet: §3.3, pp. 3-4. Threat model: §3.6, p. 4. Tamper table (Table 3): §4.3, p. 7. Limitations: §5, p. 7.

### What the record CANNOT show (§3.6 p. 4; §5 p. 7)
- "the trail attests to what was recorded, not to whether the recording faithfully reflected the world."
- Tamper-*evidence*, not tamper-*resistance*: an actor controlling storage can recompute the whole chain; external anchoring of the chain head is future work. No signatures on attestations yet (planned). Not a compliance determination.

---

## Cross-paper quick comparison (record granularity)

| Paper | Unit of record | Integrity | Human-approval field | Reasoning/CoT stored? |
|---|---|---|---|---|
| Flight Recorder | one tool call, 8 semantic fields, CBOR | SHA-256 chain + Merkle + on-chain root | yes (`approval`) | no, by design |
| ActiveGraph | one event (`id,type,actor,caused_by,payload`), many types | none (append-only, replayable) | no explicit field (goal/user actor) | prompt hash + cached response |
| Who&When | one chat turn (`role`,`content`[,`name`]) + 3 annotation keys | none | no | yes, as free-text "thought" turns |
| AuditWeave | one event, 6 types, JSONL | SHA-256 chain, `prev_hash`/`hash`/`sequence` | yes (`attestation` type) | inference payload only |


<!-- ===== span-hierarchy-family ===== -->

# Span-tree and multi-resolution family: what ONE audit record looks like

Scope: five sources, each reduced to (a) the exact field/level names, (b) one sample record, (c) the figure that shows the record shape, (d) section/page, (e) what the record cannot show. Verbatim quotes are kept under 40 words; longer examples are reproduced as STRUCTURE with paraphrased values.

All figure image URLs below returned HTTP 200 on 2026-09-09.

---

## 1. OpenInference Semantic Conventions (Arize)

- **Title:** OpenInference Specification - Semantic Conventions (plus `traces.md`, `llm_spans.md`, `tool_calling.md`)
- **Id:** GitHub `Arize-ai/openinference`, folder `spec/`
- **Links:**
  - https://raw.githubusercontent.com/Arize-ai/openinference/main/spec/semantic_conventions.md
  - https://raw.githubusercontent.com/Arize-ai/openinference/main/spec/traces.md
  - https://raw.githubusercontent.com/Arize-ai/openinference/main/spec/llm_spans.md
  - https://raw.githubusercontent.com/Arize-ai/openinference/main/spec/tool_calling.md
  - Spec folder listing: https://api.github.com/repos/Arize-ai/openinference/contents/spec (files: README.md, annotations.md, configuration.md, embedding_spans.md, llm_spans.md, multimodal_attributes.md, semantic_conventions.md, tool_calling.md, traces.md)

### Exact names

**`openinference.span.kind`** (required on every span). Values, in the spec's order (semantic_conventions.md, "Span Kinds" table):
`LLM`, `EMBEDDING`, `CHAIN`, `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`.

**Every span carries** (README.md "Spans" table): Name; Start/end time; `openinference.span.kind`; Attributes; Status (`OK`, `ERROR`, `UNSET`). traces.md adds: parent span ID (empty for root), span context (trace_id + span_id), span events.

**Key attributes for an LLM span** (name | type | spec example):

| Attribute | Type | Example in spec |
|---|---|---|
| `llm.system` | String | `openai`, `anthropic` |
| `llm.provider` | String | `openai`, `azure` |
| `llm.model_name` | String | `"gpt-3.5-turbo"` |
| `llm.request.model_name` / `llm.response.model_name` | String | `"claude-opus-5"` / `"claude-opus-4-8"` |
| `llm.invocation_parameters` | JSON string | `"{model_name: 'gpt-3', temperature: 0.7}"` |
| `llm.input_messages` | List of objects (flattened as `llm.input_messages.<i>.message.*`) | `[{"message.role": "user", "message.content": "hello"}]` |
| `llm.output_messages` | List of objects | `[{"message.role": "assistant", "message.content": "hello"}]` |
| `message.role`, `message.content`, `message.contents`, `message.name`, `message.tool_call_id`, `message.tool_calls` | String / list | see below |
| `message_content.type` | String | `"text"`, `"image"`, `"audio"`, `"reasoning"`, `"tool_use"` |
| `llm.tools` | List of objects (`llm.tools.<i>.tool.name / tool.description / tool.json_schema`) | `[{"tool.name": "get_weather", ...}]` |
| `llm.token_count.prompt`, `.completion`, `.total` | Integer | `10`, `15`, `20` |
| `llm.token_count.prompt_details.cache_read` / `.cache_write` / `.audio`; `llm.token_count.completion_details.reasoning` / `.audio` | Integer | `5`, `0`, `10` |
| `llm.cost.prompt`, `.completion`, `.total` (+ `prompt_details.*`, `completion_details.*`) | Float | `0.0021`, `0.0045`, `0.0066` |
| `llm.finish_reason` | String | `"stop"`, `"length"` |
| `llm.prompt_template.template` / `.variables` / `.version` | String / JSON | `"Weather forecast for {city} on {date}"` |
| `input.value`, `input.mime_type`, `output.value`, `output.mime_type` | String | `"text/plain"` or `"application/json"` |

**Key attributes for a TOOL span:**

| Attribute | Type | Example in spec |
|---|---|---|
| `tool.name` | String | `"WeatherAPI"` |
| `tool.description` | String | `"An API to get weather data."` |
| `tool.parameters` | JSON string | `"{ 'a': 'int' }"` |
| `tool.json_schema` | JSON string | `"{'type': 'function', 'function': {'name': 'get_weather'}}"` |
| `tool.id` | String | `"call_62136355"` |
| `input.value` / `output.value` (+ mime types) | String | tool input / tool result |

**Tool call inside an LLM output message** (tool_calling.md pattern `llm.output_messages.<m>.message.tool_calls.<t>.tool_call.<attr>`): `tool_call.id`, `tool_call.function.name`, `tool_call.function.arguments`, `tool_call.reasoning_signature`. Tool results come back as an input message with `message.role: "tool"`, `message.content`, `message.tool_call_id`, `message.name`.

**Audit-relevant extras:** `annotation.*` / `evaluation.*` (name, label, score, explanation, annotator_kind, identifier), `exception.type/message/stacktrace/escaped`, `session.id`, `user.id`, `agent.name`, `graph.node.id/name/parent_id`, `metadata`, `tag.tags`.

### Sample record (structure of the spec's own LLM span example, `llm_spans.md`; values paraphrased)

```json
{
  "name": "ChatCompletion",
  "context": {"trace_id": "<uuid>", "span_id": "<uuid>"},
  "span_kind": "SPAN_KIND_INTERNAL",
  "parent_id": "<uuid of parent CHAIN/AGENT span>",
  "start_time": "2024-01-11T16:45:17.98-07:00",
  "end_time":   "2024-01-11T16:45:18.51-07:00",
  "status_code": "OK",
  "status_message": "",
  "attributes": {
    "openinference.span.kind": "LLM",
    "llm.system": "openai",
    "llm.model_name": "gpt-3.5-turbo-0613",
    "llm.invocation_parameters": "{\"model\": \"gpt-3.5-turbo-0613\", \"temperature\": 0.1}",
    "llm.input_messages": [
      {"message.role": "system", "message.content": "<system prompt>"},
      {"message.role": "user",   "message.content": "what is 23 times 87"}
    ],
    "llm.output_messages": [
      {"message.role": "assistant",
       "message.tool_calls": [
         {"tool_call.function.name": "multiply",
          "tool_call.function.arguments": "{\"a\": 23, \"b\": 87}"}]}
    ],
    "output.value": "<raw provider JSON>", "output.mime_type": "application/json",
    "llm.token_count.prompt": 229, "llm.token_count.completion": 21, "llm.token_count.total": 250
  },
  "events": []
}
```

Tool-result message record (llm_spans.md, verbatim, 4 fields):
```json
{"message.role": "tool", "message.content": "2001", "message.name": "multiply", "message.tool_call_id": "call_62136355"}
```

Flattened (OTLP wire) form of a tool call (tool_calling.md "Example Tool Call", structure):
```
llm.output_messages.0.message.role = "assistant"
llm.output_messages.0.message.tool_calls.0.tool_call.id = "call_abc123"
llm.output_messages.0.message.tool_calls.0.tool_call.function.name = "get_weather"
llm.output_messages.0.message.tool_calls.0.tool_call.function.arguments = "{\"location\": \"San Francisco, CA\"}"
```

### Figure
No figures in the spec; the record shape is given as JSON listings. Best "figure" = the two JSON blocks in `traces.md` ("query span" = root `CHAIN`, `parent_id: null`; "LLM span" = child sharing the same `trace_id`). No image URL exists.

### Section / page
Web markdown, no pages. `semantic_conventions.md` §"Span Kinds" (lines 6-21), §"Reserved Attributes" (lines 23-146), §"Attribute Naming Conventions" (line 271+). `traces.md` §"Spans" (sample span JSON), §"Span Kind". `llm_spans.md` full-span examples. `tool_calling.md` §"Tool Calls in Messages", §"Tool Results".

### What this record cannot show
The spec itself says the convention records *what happened*, not whether it was right: quality signals must be attached separately via `annotation.*` / `evaluation.*` attributes (README "Quality feedback"; semantic_conventions.md annotations section). There is no field for "why" a step was taken beyond `message_content.type: "reasoning"` text if the provider returns it. Also note the naming clash: OTel's `span_kind` (INTERNAL/CLIENT...) is different from `openinference.span.kind` (traces.md §"Span Kind").

---

## 2. TRAIL: Trace Reasoning and Agentic Issue Localization

- **Id:** arXiv 2505.08638 (v3). Deshpande et al., Patronus AI.
- **Links:** https://arxiv.org/abs/2505.08638 ; HTML https://arxiv.org/html/2505.08638v3 ; code https://github.com/patronus-ai/trail-benchmark ; data https://huggingface.co/datasets/PatronusAI/TRAIL (gated: HTTP 401 without login).
- Repo layout (verified via GitHub API): `benchmarking/run_eval.py`, `benchmarking/calculate_scores.py`, `benchmarking/data/{GAIA, SWE Bench}/` (raw traces, empty in GitHub mirror), `benchmarking/processed_annotations_gaia/*.json` (117 files), `benchmarking/processed_annotations_swe_bench/`.

### Exact names

**Input record = one OpenTelemetry/OpenInference trace JSON.** `run_eval.py` reads each `*.json` file as a raw string and pastes it into the judge prompt (`get_prompt(trace)`), so the model sees the raw span JSON. Figure 2 (p.3) shows one span's attribute block under the key **`span_attributes`**, with OpenInference names: `openinference.span.kind`, `input.value`, `input.mime_type`, `llm.input_messages.<i>.message.role/.content`, `llm.invocation_parameters`, `llm.model_name`, `llm.token_count.prompt/.completion/.total`, `output.value`, `output.mime_type`, plus vendor keys `pat.app`, `pat.project.id`, `pat.project.name`. The paper says "all traces are collected via opentelemetry ... the openinference standard" (§4.1, p.5).

**Output record = one annotated error.** Five fields, named exactly (Appendix prompt, p.20; §A.7, p.15):
`category`, `location`, `evidence`, `description`, `impact`
- `category`: leaf of the taxonomy (e.g. `Formatting Errors`, `Language-only`, `Tool-related`, `Goal Deviation`, `Resource Abuse`, `Rate Limiting`, `Tool Selection Error`, `Context Handling Failures`, `Instruction Non-compliance`).
- `location`: the span id (16-hex string).
- `evidence`: text copied from the span.
- `description`: annotator's explanation.
- `impact`: `HIGH` | `MEDIUM` | `LOW`.

Plus per-trace `scores`: `reliability_score`, `reliability_reasoning`, `security_score`, `security_reasoning`, `instruction_adherence_score`, `instruction_adherence_reasoning`, `plan_opt_score`, `plan_opt_reasoning`, `overall` (0-5 Likert; rubric in §A.7.1, p.15).

Localization rule (prompt, p.20-21): mark the *first* span where the error appears, except `Resource Abuse` -> mark the *last* instance.

### Sample record (actual gold file `processed_annotations_gaia/0035f455b3ff2295167a844f04d85d34.json`, structure with lightly shortened values)

```json
{
  "errors": [
    {
      "category": "Instruction Non-compliance",
      "location": "98fa1dda65ab168b",
      "evidence": "The output plan ends with '6. Verify all steps ...' instead of ending with '<end_plan>'.",
      "description": "The system failed to append the required <end_plan> tag ... violating an explicit formatting instruction.",
      "impact": "LOW"
    },
    {
      "category": "Tool-related",
      "location": "bc20feefb97e11e5",
      "evidence": "I have verified that the report came from the USGS ... database ...",
      "description": "Claimed to have obtained information that required a search_agent tool call, but no such call or observation exists in preceding spans.",
      "impact": "HIGH"
    }
  ],
  "scores": [
    {"reliability_score": 1, "reliability_reasoning": "...",
     "security_score": 5, "security_reasoning": "No security issues were detected.",
     "instruction_adherence_score": 2, "instruction_adherence_reasoning": "...",
     "plan_opt_score": 0, "plan_opt_reasoning": "...", "overall": 0.0}
  ]
}
```

Note: two errors can point to the same `location` (span `bc20feefb97e11e5` carries both `Tool-related` and `Goal Deviation`).

### Taxonomy figure and record-shape figure
- **Figure 1** (p.1): "Illustration of the TRAIL taxonomy of errors" - three top branches Reasoning / System Execution / Planning & Coordination with leaf categories.
  Image: https://arxiv.org/html/2505.08638v3/figures/diagrams/trail_taxonomy.png (HTTP 200)
- **Figure 2** (p.3): "TRAIL trace's span structure and error examples" - left: one span's `span_attributes` block (OpenInference keys, `openinference.span.kind: "LLM"`, `llm.model_name: "anthropic/claude-3-7-sonnet-latest"`, token counts 5131/259/5390); right: seven `{category, location, evidence, description, impact}` records (e.g. `Rate Limiting` with evidence `status_message: "RateLimitError: ..."`, impact `HIGH`). In the HTML version this figure is rendered as text, not an image; no PNG exists. Read it from the PDF p.3.
- **Figure 3** (p.6): dataset statistics; (a) https://arxiv.org/html/2505.08638v3/figures/plots/Annotation_Errors_By_Category.png
- Figure 6 (p.16): impact-level distributions (`impact_dist.png`, `error_impact_distribution.png` under the same base URL).

### Section / page
§3 taxonomy p.3-5; §4.1 (OpenInference/OTel format) p.5; §4.2 annotation p.6; §A.7 annotation protocol + A.7.1 rubric p.15; judge prompt with JSON template and example p.20-21; Figure 2 p.3; Figure 1 p.1.

### What this record cannot show
Paper's own limitations (§6, p.9): text-only; multimodal tool use is not covered; many tail categories have very few examples. The annotation protocol did not verify anything outside the trace (footnote 5, p.15: external web facts were not checked). `location` is a single span id, so an error that spans several steps is pinned to one span (first or last by rule), and the Deepchecks paper (below) shows the LLM-vs-Tool span choice is applied inconsistently.

---

## 3. ECHO: "Where Did It All Go Wrong? A Hierarchical Look into Multi-Agent Error Attribution"

- **Id:** arXiv 2510.04886 (v2).
- **Links:** https://arxiv.org/abs/2510.04886 ; HTML https://arxiv.org/html/2510.04886v2

### Exact names (§3.1 "Hierarchical Context Representation", p.2-3)

Trace = interaction trace τ of n agents; target step/agent index i. Hierarchical context C_i = {L1, L2, L3, L4}:

| Level | Paper's name | Window | What is kept (paper's words, paraphrased) | Regex extractor (Alg. A.1 / code A.3) | `detail_level` string in code |
|---|---|---|---|---|---|
| L1 | Immediate Context layer | τ_{i±1} | full agent content: reasoning chain, inputs/outputs, intermediate computations | `ExtractFullContext` | `"full"` |
| L2 | Local Context Layer | τ_{i±2,3} | key decisions: conclusive statements, logical transitions; routine operations filtered | `ExtractKeyDecisions` | `"key_decisions"` |
| L3 | Distant Context Layer | τ_{i±4,5,6} | compressed outcome summaries: state changes, error conditions, handoff info | `CompressSummaries` | `"summary"` |
| L4 | Global Context Layer | τ_remainder (distance > 6) | milestones only: error-propagation signals, major state transitions, cross-agent dependencies | `ExtractMilestones` | `"milestones"` |

Illustrative content per level given in §3.1 (p.3), each a short quoted example: L1 raw terminal output; L2 "I conclude the optimal parameters are ..."; L3 "Model training failed: insufficient data"; L4 "Switched from classification to regression".

### Sample record (what the auditor actually receives)

The paper gives no rendered prompt dump. The closest concrete artefact is the Python dict built in Appendix A.3 (p.17, `extract_agent_contexts_hierarchical`). Structure, with paraphrased values:

```json
{
  "current_agent": {"index": 7, "name": "DataAnalyst", "role": "assistant", "content": "<full text>"},
  "context_levels": {
    "immediate":  [ {"index": 6, "name": "Planner", "role": "...", "distance": 1, "detail_level": "full",          "content": "<entire message>"} ,
                    {"index": 8, "...": "..."} ],
    "nearby":     [ {"index": 5, "distance": 2, "detail_level": "key_decisions", "content": "Therefore, we should use gradient descent."} ,
                    {"index": 9, "distance": 2, "...": "..."} ],
    "distant":    [ {"index": 2, "distance": 5, "detail_level": "summary",       "content": "Received dataset with normalized features."} ],
    "milestones": [ {"index": 0, "distance": 7, "detail_level": "milestones",    "content": "Persistent data quality errors..."} ]
  }
}
```
Each level list is sorted by original `index`. Extractors cap output (`max_words`, e.g. 15 for milestones) and return a fixed fallback string such as "No milestones available" when no regex fires.

The analyst prompt (A.4, p.18-19) then tells the LLM, in a bullet list, that it sees: Immediate context = full details of adjacent agents; Nearby = key decisions 2-3 steps away; Distant = brief summaries 4+ steps away; and asks for sections **Purpose, Assumptions and Information, Errors, Evidence**. Analyst outputs carry `evidence`, `confidence` (σ_j) and `hypotheses` (Fig. 1 caption).

### Figure
- **Figure 1** (p.3): "ECHO Architecture. The system comprises: (1) Hierarchical Context - processes traces through 4 compression layers (L1-L4: full content -> milestones) ... (2) Decoupled Analysis - 6 specialized agents ... structured outputs with evidence, confidence scores, and hypotheses; (3) Consensus Voting ..."
  Image: https://arxiv.org/html/2510.04886v2/svgviewer-png-output_latest_2.png (HTTP 200). This is the only image in the paper.

### Section / page
§3.1 p.2-3 (level definitions); Fig. 1 p.3; Alg. 1 in A.1 p.12-13 (`ExtractFullContext`/`ExtractKeyDecisions`/`CompressSummaries`/`ExtractMilestones`); A.3 p.13-17 (regex code; `context_levels` dict p.17); A.4 analyst prompt p.18.

### What this record cannot show
The paper says extraction is regex-based, so anything not matching a keyword pattern is dropped at L2-L4; LLM-based extraction was more accurate but "computationally intractable" (§4.3, p.9). Attribution is restricted to steps with explicit reasoning (§3.2, p.3). Step-level exact accuracy is only 27-28% (§4.2, p.7), i.e. the compressed view often loses the exact step.

---

## 4. TrajDebug: Tracing Error Lifecycle to Identify Critical Failures in Long-Horizon Agent Trajectories

- **Id:** arXiv 2608.06346 (v1). THU-KEG. Findings of EMNLP 2026.
- **Links:** https://arxiv.org/abs/2608.06346 ; HTML https://arxiv.org/html/2608.06346v1 ; code+data https://github.com/THU-KEG/TrajDebug

### Exact names

**Input record (unified trajectory schema, `data_processing/README.md`):**
```json
{
  "messages": [ {"step": 0, "role": "system|user|assistant|tool", "name": "...", "content": "..."} ],
  "metadata": {
    "dataset": "...", "task_id": "...", "task_description": "...", "reward": 0,
    "annotation": {"critical_error_step": 17, "critical_error_type": "plan.WrongOrder"},
    "extra": {}
  }
}
```
Invariant: `messages[i].step == i`; critical step never points at a `user` message. Released files add per-message `"judgable": true|false` and `"compress_role": "preserve"|"default"|"compress"` (seen in `data/trajerrbench/en/tau2bench/airline_failed_deepseek-reasoner_00c9f923-....json`, 29 steps, critical step 17, type `plan.WrongOrder`). Error modules: `plan`, `reason`, `act`, `obs`, `verify`.

**Three granularities (§3.1 "Multi-Granularity Compression", p.3; caps in App. D, p.17):**

| Paper name | Code name | Keeps | Char cap per field |
|---|---|---|---|
| high-detail view | `th1` | original instruction, action, observation, locally relevant reasoning snippets needed for evidence verification | <= 3000 |
| medium-detail view | `th2` | the step's main intent, action, and state update | <= 1200 |
| low-detail view | `th3` | coarse progress, salient entities, unresolved commitments | <= 600 |

Distance rule for trigger detection (App. D, p.17): current step + history within 2 steps -> `th1`; 3-5 steps away -> `th2`; farther -> `th3`. Fallback order when a tier is missing: `th1 -> th2 -> th3 -> raw`. Stage A output file `<stem>_stage_a.json` holds a `step_compressions` pool with `th1/th2/th3` per step (`detector/stage_a_diagnosis.py` docstring).

**Error record (§3.2, p.3):** trigger e = (t, c, p, q_w, q_r): step `t`, reference category `c` (Task Conflict / History Conflict / ...), execution phase `p`, wrong commitment `q_w`, violated reference `q_r`. Both `q_w` and `q_r` must be verbatim-citable or the trigger is discarded. Instances then carry: `ID`, `Origin` step, `Triggers` (step list), `Reference category`, `State label` (e.g. Clean Resolution, Costly Resolution (budget debt), Manifest Active), `Description`.

### Sample record: one step at each level

The paper does not print one step side-by-side at th1/th2/th3. Closest: the compression prompt (App. D, "Stage A - Trajectory Compression", p.18) defines the tiers, and the case study (App. C, p.15-17) shows step 25 at high detail plus its trigger. Reconstructed from those, for the case-study step 25 (airline, qwen3-max):

- **th1 (high):** full assistant text: upgrade only outbound HAT072 to business costs $282; current outbound $130 so extra $152; within the $200 budget; gold member keeps two free checked bags on both flights ... (verbatim in App. C.2).
- **th2 (medium):** intent = propose partial upgrade; action = quote $152 upgrade for outbound only; state = plan committed, within $200 budget.
- **th3 (low):** "commit: upgrade outbound HAT072 only; $152; budget $200".
- **Trigger on this step** (as the paper states it): category `Task Conflict`, phase `planning`, q_w = "upgrade only the outbound flight to business", q_r = policy "all flights in the same reservation must share the same cabin class"; state `Manifest Active`; kept in candidate set F(τ); selected as critical step 25 = human label 25.

The prompt additionally requires that constraints, plans, IDs, numbers with units, dates, URLs, tool names/argument keys and error messages be copied **verbatim** in all three tiers.

Table 7 row (p.16, structure): `ID | Origin | Triggers | Reference category | State label | Description`, e.g. `1* | 13 | 13, 19, 23 | History Conflict | Costly Resolution (budget debt) | financial computations omit the $30 non-refundable insurance fee ...`.

### Figures
- **Figure 3** (p.4): "An overview of the framework of TrajDebug." - multi-granularity views feeding three stages (trigger detection -> state classification -> causal attribution).
  Image: https://arxiv.org/html/2608.06346v1/pipeline.png (HTTP 200). Repo copy: https://raw.githubusercontent.com/THU-KEG/TrajDebug/main/assets/%20pipeline.png (HTTP 200; note the leading space in the filename).
- **Figure 1** (p.1): "Critical error detection requires grounding errors in long-range context and distinguishing the failure-responsible error from multiple coexisting errors."
  Image: https://arxiv.org/html/2608.06346v1/fig1.png (HTTP 200)

### Section / page
§3.1 p.3 (three views); §3.2 p.3 (trigger tuple); Fig. 3 p.4; App. C case study Tables 6-7 p.15-17; App. D char caps + distance rule p.17; Stage A compression prompt p.18; §9 Limitations p.9; failure decomposition Table 13 p.23.

### What this record cannot show
§9 Limitations (p.9): still LLM-dependent for interpretation and attribution; as a staged pipeline it can inherit false negatives - if the trigger stage misses the error the final candidate set lacks it. Table 13 (p.23): "Trigger Misses" are 42.1% of failures. The compressed th2/th3 views deliberately drop everything except constraints, decisions, outcomes and errors, so a subtle deviation in distant history may not be visible.

---

## 5. Deepchecks: "Holistic Evaluation and Failure Diagnosis of AI Agents"

- **Id:** arXiv 2605.14865 (v1).
- **Links:** https://arxiv.org/abs/2605.14865 ; HTML https://arxiv.org/html/2605.14865v1

### Exact names

Trace = hierarchical tree of spans (OpenTelemetry GenAI conventions, §2, p.3). Span types evaluated: **Agent**, **LLM**, **Tool**.

**Per-span assessment (§3.1 "Bottom-Up Evaluation", p.3):** metric p on span s yields verdict v_p(s) ∈ {pass, fail}; semantic metrics produce score σ ∈ {1,2,3,4,5} **plus a natural-language rationale**; pass iff σ_p(s) >= τ_p. Other metrics give a label or a number.

**Table 1 (p.4) - leaf-span metrics, exact names:**

| Span type | Metric | Output |
|---|---|---|
| LLM | Instruction Following | 1-5 |
| LLM | Reasoning Integrity | 1-5 |
| LLM | Avoidance (subtypes: missing knowledge, policy restrictions, other) | label |
| LLM | Error Detection | label |
| LLM | Latency / Tokens | numeric |
| Tool | Tool Completeness | 1-5 |
| Tool | Error Detection | label |

**Table 2 (p.5) - agent-level (top-down) metrics:** e.g. Tool Coverage, Plan Efficiency, and final-output completeness; each also 1-5 + rationale.

**Aggregation (§3.1 "Hierarchical Aggregation", p.4):** default = existential failure propagation: a parent fails if any child has a failing metric. Alternatives: threshold-based, type-filtered, conjunctive. Error localization exposes S_fail (failing leaf spans), P_fail(s) (failing metrics per span), and the judge's rationales.

### Sample record: the span-level rationale format (Figure 3, App. A.1, p.12-14)

The framework renders a trace as an indented tree where each span node is followed by `Metric Name (score): "rationale"`. Structure, values paraphrased from Fig. 3 (GAIA task: CFM values from a YouTube video; final answer hallucinated):

```
[Agent] CodeAgent.run
 +-- Plan Efficiency (2.0): "agent reported CFM values with no supporting tool evidence, skipped verification, did not adapt after repeated errors"
 +-- Tool Coverage (1.0): "no information about the CFM values or their provenance found in child spans"
 +-- [Agent] ToolCallingAgent.run
 |    +-- Tool Coverage (1.0): "..."
 |    +-- [Steps 1-5] ...                       <- spans with no issue are collapsed
 |    +-- [Step 7]
 |    |    +-- [LLM] LiteLLMModel
 |    |    |    \-- Reasoning Integrity (3.0): "tool call issued with wrong arguments for page_down, violating the function signature"
 |    |    \-- [Tool] PageDownTool
 |    |         \-- Tool Completeness (1.0): "tool response is an explicit error traceback; no content returned"
 \-- [LLM] LiteLLMModel (Final)
      \-- Reasoning Integrity (2.0): "..."
```
So one per-span record = `{span_type, span_name, metric, score 1.0-5.0, rationale}`; scores 1.0 = critical failure, 5.0 = no issue.

Figure 4 (App. B.1, p.15) uses the same tree but hangs TRAIL gold records off spans: `[Tool] PageDownTool (fa421073...)` -> `Formatting Errors (MEDIUM): "..."`, with `(no error annotated)` on the sibling LLM span.

Table 3 (p.6) is the compact form: rows = 4 ground-truth issues (Poor Information Retrieval, Resource Abuse, Formatting Error, Hallucination); columns = which top-down / bottom-up metric caught it, with severity score in parentheses; "-" = missed.

### Figures
- **Fig. 1** (p.2): "Overview of the holistic agent evaluation framework. Top-down evaluation assesses agent-level metrics by reasoning over an agent span's descendants, while bottom-up evaluation localizes and categorizes failures at individual LLM and tool spans."
  Image: https://arxiv.org/html/2605.14865v1/figures/framework_vizualization.png (HTTP 200)
- **Fig. 2** (p.8): per-category F1 heatmap on TRAIL. Image: https://arxiv.org/html/2605.14865v1/figures/error_categories.png (HTTP 200)
- **Fig. 3** (p.12-14) and **Fig. 4** (p.15): the annotated trace trees above; rendered as monospace text in both HTML and PDF, no PNG.

### Section / page
§2 p.3 (trace substrate); §3.1 p.3-4 (verdict definition, Table 1, aggregation, localization); §3.2 p.4-5 (Table 2); §3.3 + Table 3 p.5-6; §5 Discussion p.9; App. A.1 Fig. 3 p.12-14; App. B.1 Fig. 4 p.15; App. C aggregation limits p.17.

### What this record cannot show
§5 "The Need for Better Aggregation" (p.9) and App. C (p.17): with existential propagation a single low-impact formatting miss marks the whole trace as failed, indistinguishable from a critical reasoning failure; 44 TRAIL traces with Overall >= 3.5 (three with 5.0) still carry span-level errors. The per-span record has no severity weighting or outcome-relevance field. §5 also notes the framework emits metric scores + rationales, not TRAIL categories; a separate LLM "mapper" must translate them (§4.2 footnote, p.6-7).

---

## Quick comparison of the five record shapes

| Source | Unit of record | Where "why" lives | Multi-resolution? |
|---|---|---|---|
| OpenInference | one span (`openinference.span.kind` + `llm.*`/`tool.*` attrs) | none (add `annotation.*`) | no - flat tree of full spans |
| TRAIL | one error `{category, location=span id, evidence, description, impact}` over an OTel trace | `description` | no - judge sees raw full JSON |
| ECHO | one target step with L1 full / L2 key decisions / L3 summary / L4 milestones | analyst sections Purpose/Assumptions/Errors/Evidence + confidence | yes - by distance from target (±1, ±2-3, ±4-6, rest) |
| TrajDebug | one message step with th1/th2/th3 views; error = (t, c, p, q_w, q_r) + state label | verbatim `q_w` vs `q_r` | yes - by distance (0-2 th1, 3-5 th2, rest th3) and by role |
| Deepchecks | one span + `Metric (score): "rationale"`; parents aggregate | rationale string | yes - leaf verdicts vs agent-level metrics over descendants |


<!-- ===== checkpoint-family ===== -->

# Audit-record shapes: the checkpoint / snapshot family

Concrete records only. Verbatim quotes are kept under 40 words; everything else reproduces the *structure* (field names, value types) with paraphrased example values. Image URLs were checked with `curl -sI` (HTTP 200) on 2026-09-09.

---

## 1. LangGraph checkpointer (`StateSnapshot` / `Checkpoint`)

- **Id / links**
  - Docs (checkpoint structure now lives here): https://docs.langchain.com/oss/python/langgraph/checkpointers
  - Docs overview page: https://docs.langchain.com/oss/python/langgraph/persistence (short overview only; the `StateSnapshot` example moved to the Checkpointers page)
  - `https://langchain-ai.github.io/langgraph/concepts/persistence/` now just redirects (555-byte stub).
  - Source, `Checkpoint` TypedDict: https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/checkpoint/langgraph/checkpoint/base/__init__.py
  - Source, `StateSnapshot` NamedTuple: https://raw.githubusercontent.com/langchain-ai/langgraph/main/libs/langgraph/langgraph/types.py (line ~683)
  - Size numbers: GitHub issue #7714, https://github.com/langchain-ai/langgraph/issues/7714 (open, created 2026-05-05)

- **Exact field names**
  - `StateSnapshot` (what `graph.get_state(config)` returns; docs table "StateSnapshot fields"):
    | Field | Type | Meaning (docs) |
    |---|---|---|
    | `values` | `dict` | state channel values at this checkpoint |
    | `next` | `tuple[str, ...]` | node names to run next; `()` = graph finished |
    | `config` | `dict` | `thread_id`, `checkpoint_ns`, `checkpoint_id` |
    | `metadata` | `dict` | `source` (`"input"` / `"loop"` / `"update"`), `writes` (node outputs), `step` (super-step counter) |
    | `created_at` | `str` | ISO-8601 timestamp |
    | `parent_config` | `dict \| None` | config of previous checkpoint; `None` for the first |
    | `tasks` | `tuple[PregelTask, ...]` | each task has `id`, `name`, `error`, `interrupts`, optionally `state` |
    | `interrupts` | `tuple[Interrupt, ...]` | (source only, not in the docs table) pending interrupts |
  - `Checkpoint` TypedDict (the row actually written by a checkpointer; source docstring: "State snapshot at a given point in time"):
    - `v: int` — format version, currently `1`
    - `id: str` — unique and monotonically increasing (sortable)
    - `ts: str` — ISO-8601 timestamp
    - `channel_values: dict[str, Any]` — channel name → value
    - `channel_versions: ChannelVersions` (`dict[str, str|int|float]`) — per-channel monotonically increasing version
    - `versions_seen: dict[str, ChannelVersions]` — node id → channel → version seen; "Used to determine which nodes to execute next"
    - `updated_channels: list[str] | None`
    - (`pending_sends` is still copied in `copy_checkpoint`, but is no longer a declared key)
  - `CheckpointMetadata` TypedDict (source): `source: Literal["input","loop","update","fork"]`, `step: int` (`-1` = first input checkpoint, `0` = first loop checkpoint), `parents: dict[str,str]` (namespace → checkpoint id), `run_id: str`, `counters_since_delta_snapshot` (beta, for `DeltaChannel`). Note: the docs' printed example shows a `writes` key in metadata, but `writes` is not in the current TypedDict.
  - Storage layout implied by the "Build a custom checkpointer" section: one **checkpoint row** keyed by `(thread_id, checkpoint_ns, checkpoint_id, parent_id)` plus **`checkpoint_writes` rows** (one per node/task output within a super-step) linked by `(thread_id, checkpoint_ns, checkpoint_id)`.

- **Sample record (docs' own printed `get_state` output; structure reproduced, values abbreviated)**
  ```
  StateSnapshot(
      values={'foo': 'b', 'bar': ['a', 'b']},
      next=(),
      config={'configurable': {'thread_id': '1', 'checkpoint_ns': '',
                               'checkpoint_id': '1ef663ba-28fe-6528-8002-...'}},
      metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},
      created_at='2024-08-29T19:19:38.821749+00:00',
      parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '',
                                      'checkpoint_id': '1ef663ba-28f9-6ec4-8001-...'}},
      tasks=()
  )
  ```
  `get_state_history(config)` returns a list of these, newest first. In the docs' 4-entry example the chain is: `step=2` (done, `next=()`) → `step=1` (`next=('node_b',)`, one `PregelTask(id=..., name='node_b', error=None, interrupts=())`) → `step=0` (`next=('node_a',)`) → `step=-1` (`source='input'`, `next=('__start__',)`, `parent_config=None`). Each entry's `parent_config.checkpoint_id` equals the next-older entry's `config.checkpoint_id` — that is the audit chain.

- **Figure**: docs image "State" (the `get_state`/history diagram), 2692×1056 JPEG — HTTP 200:
  `https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/get_state.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=38ffff52be4d8806b287836295a3c058`

- **Section / page**: Checkpointers page → "Core concepts › Checkpoints › Super-steps", "Get and update state › Get state › StateSnapshot fields", "Get state history", "Replay", "Optimize checkpoint storage", "Build a custom checkpointer › put / put_writes / get_tuple". Web docs, no page numbers.

- **Size numbers (issue #7714, reporter's own measurements, not maintainer-verified)**
  - 16-turn ReAct agent, 65 messages: **21,850 bytes** under default `MemorySaver` vs 3,217 bytes with a binary pooled serializer → "85.3% storage overhead (6.79x)".
  - Same 16-turn state as context: 5,764 tokens (20,516 chars) vs 3,587 tokens (10,703 chars) of semantic content → 37.8% token overhead.
  - 4-turn, 13-message repro: ~6,800 bytes, ~1,450 tokens.
  - Also: 4 structurally corrupt payloads (orphaned tool result, backward step counter, invalid record type, missing fields) all "Silent pass" — no validation on write.
  - Docs corroborate the growth: "By default, LangGraph checkpoints write the full value of every state channel at each super-step" (Optimize checkpoint storage); troubleshooting entry "Checkpoints growing unboundedly" recommends pruning/retention.

- **What it cannot show**: the checkpoint holds graph-channel state only. The docs' Replay section says nodes after a checkpoint "re-execute, including any LLM calls, API requests" — side effects are not recorded and fire again. Crab's Table 1 rates LangGraph as capturing "Conversation" only, Correct = ✗; Safe-to-Resume's Table I scopes it as "Graph state, including messages, intermediate results, pending execution state" (Framework scope; workspace and runtime outside the boundary).

---

## 2. AgentRewind (arXiv 2608.14380) + `replay-agent-recorder`

- **Id / links**
  - Paper: https://arxiv.org/abs/2608.14380 — HTML https://arxiv.org/html/2608.14380v1 — PDF https://arxiv.org/pdf/2608.14380 (19 pages)
  - Recorder repo: https://github.com/Futuresis/replay-agent-recorder (alpha; JSONL traces under `.replay/runs/*.jsonl`)
  - Repo docs with the field vocabulary: `docs/concepts.md`, `docs/tool-adapter-protocol.md`, `docs/limitations.md` (raw.githubusercontent.com/Futuresis/replay-agent-recorder/main/…). No standalone JSON-schema or example-trace file was found in the repo listing; the paper's Figure 9 is the only published record example.

- **Exact names**
  - Checkpoint (Sec. 3 "Long-Horizon Execution with Rewind", Eq. 3): `d_t = (c_t, s_t)` — `c_t` = agent context, `s_t` = controlled-environment state; recorded "at each LLM decision boundary". Checkpoint metadata `η_t` describes the segment between `d_t` and `d_{t+1}`; rewind memory `m` accumulates in set `M`.
  - Trace record (Appendix C, "one record per node, as a line of JSON"): envelope = `record_uid`, `kind` ∈ {`llm`, `tool`}, `input_id` (sha256 of canonicalized input), `input`, `output`, `error`, `metadata`.
    - `llm` record: `input{model, temperature, messages[], tools[]}`, `output{content, tool_calls[], usage{}}`
    - `tool` record: `input{tool_name, arguments{}}`, `output{value{...}}`, `error`
    - `metadata{latency_ms, filesystem{workspaces{<ws>{before_commit, after_commit, changed, diff_summary[{status, path}]}}}}`
  - Path classes at restore (Table 14): `tracked` (snapshot yes / reverted), `excluded` (no / left as is — `.git`, `.env`, secrets), `volatile` (no / deleted).
  - Repo terms (`docs/concepts.md` "Core terms"): Run, Trace (the JSONL file), Record mode, Replay mode, Fork, Breakpoint (an LLM record uid such as `rec_000003`), Git workspace, Workspace boundary, Path id, Semantic provenance, Graph IR. Agent-facing tools: `backtrack_candidates`, `backtrack_commit` (Fig. 8).

- **Sample record (structure of Figure 9, values paraphrased)**
  ```json
  {"record_uid":"rec_000007","kind":"tool",
   "input":{"tool_name":"bash","arguments":{"command":"pytest -q"}},
   "output":{"value":{"output":"...","returncode":0}},
   "error":null,
   "metadata":{"latency_ms":812,
     "filesystem":{"workspaces":{"ws0":{
        "before_commit":"a1b2...","after_commit":"c3d4...",
        "changed":true,
        "diff_summary":[{"status":"M","path":"crm/reports.py"}]}}}}}
  ```
  The preceding `llm` line (`rec_000006`) has the same envelope with `input{model,temperature,messages,tools}` and `output{content,tool_calls,usage}`. An llm node plus its `before_commit` *is* the checkpoint `d_t`; the tool records between two llm nodes supply `η_t`. One JSONL file per run; each rewind adds a file whose header names the forked run and node.

- **Figures**
  - Fig. 1 "Overview of AgentRewind" — (a) context recorder + environment-state recorder create "aligned checkpoints d_t=(c_t,s_t)"; rewind executor restores both and injects rewind memory; (b) example trajectory returning to `d_k`. Image (HTTP 200): https://arxiv.org/html/2608.14380v1/Figures/fig1.png — PDF p. 3.
  - Fig. 9 "One llm record and one tool record, abridged." — code listing, no image; PDF p. 15 (Appendix C).
  - Table 14 path classes — PDF p. 16.

- **Section / page**: Sec. 3 checkpoint definition (p. 3); "External Environment Recovery Boundary" (p. 4); Appendix C.3 "Rewind Execution", C.4 "Workspace Snapshot and Restore" (pp. 15–16).

- **What it cannot show**: paper, p. 4: "Effects outside the workspace filesystem, such as network requests, external-service calls, and external runtime state, cannot be undone." Repo README limitations: local tools are recorded only if routed through the tool protocol/adapter; tool I/O must be JSON-like; breakpoints target LLM records only. `docs/concepts.md`: file IO outside the Workspace boundary "is not restored or compared."

---

## 3. Crab (arXiv 2604.28138)

- **Id / links**: https://arxiv.org/abs/2604.28138 — HTML https://arxiv.org/html/2604.28138v1 — PDF https://arxiv.org/pdf/2604.28138 (15 pages). "Crab: A Semantics-Aware Checkpoint/Restore Runtime for Agent Sandboxes."

- **Three checkpoint scopes (baseline names as the paper uses them)**
  | Scope | Paper's name | What is restored |
  |---|---|---|
  | chat only | **Chat-only** | conversation/messages only (app/framework level) |
  | chat + filesystem | **Chat+FS** | messages + filesystem snapshot |
  | full FS + process | **FullCkpt** (every-turn full checkpoint) / **Crab** (selective) | filesystem + process state (ZFS snapshot + CRIU) |
  | (control) | **Restart** | re-run task from scratch |

- **Recovery-correctness numbers**
  - Motivation study, Sec. 3.1 / Fig. 1 (p. 3), one crash per task: Chat-only **6%** (deterministic replay) / 28% (live LLM); Chat+FS 48% (replay) / 34% (live); Restart 100% but 1.81× / 1.55× median time-to-solve.
  - Evaluation, Sec. 7.2 / Fig. 12 "Recovery correctness under sandbox crashes" (pp. 9–10): Crab, Restart, FullCkpt = **100%** in all settings; Chat+FS = **100% on SWE-bench** but only **28% and 42% on Terminal-Bench** (Claude-code, iFlow-cli); abstract/intro summarize chat-only as **8–13%** and chat+FS as **28–42%** on Terminal-Bench.
  - Table 1 (p. 2) "Comparison of C/R approaches", columns `System | Layer | State Captured | Correct | Cost`:
    `Claude | App | Chat + Git/FS | ✗ | Low` · `LangGraph | Framework | Conversation | ✗ | Low` · `Docker | OS | Full Container | ✓ | Med` · `E2B | VM | Full VM | ✓ | High` · `Crab | Cross-layer | Adaptive | ✓ | Low`.

- **How a turn's OS effects are classified (the semantic classes)**
  - Inspector output → one of four checkpoint classes per turn (Sec. 4.2, p. 2; Sec. 5.2): **no checkpoint**, **filesystem-only checkpoint**, **process-only checkpoint**, **full checkpoint**.
  - Decision rule = **net-change semantics** (Sec. 5.2 "Inspector: The State Tracker", p. 6, Fig. 7): "change" is the net difference between the last checkpoint and the inspection point; transient effects (forked short-lived shells, temp files removed within the turn) are ignored; only persistent effects count — a file that remains created/modified, a process that remains alive, memory pages dirtied by a long-running process.
  - Sparsity: >75% of turns produce no recovery-relevant state; skip ratio >70% (Fig. 13); up to 87% of turns need no checkpoint.
  - Inspector accuracy, Table 4 (p. 10), 2,063 manually labeled turns: process changes 100% accurate; filesystem 98.3% accuracy, 2.3% FPR, zero false negatives.

- **Sample record**: Crab publishes no checkpoint JSON. Closest things: (a) a Table 1 row (above); (b) Fig. 8 (p. 6–7): the Checkpoint Manager keeps "versioned recoverable manifests over partial filesystem and process checkpoints" with transactional publication — i.e. one manifest per turn pointing at a ZFS snapshot id and/or a CRIU image, versioned by turn.

- **Figures**
  - Fig. 7 "Examples of net filesystem / process changes." — https://arxiv.org/html/2604.28138v1/net_change_semantics.png (HTTP 200), PDF p. 6.
  - Fig. 5 architecture — https://arxiv.org/html/2604.28138v1/sys_overview_v3.png (HTTP 200).
  - Fig. 12 recovery correctness — no raster image in the HTML (inline vector); use PDF p. 10.

- **Section / page**: Sec. 3.1 "Lightweight Recovery Is Often Incorrect" (p. 3); Sec. 3.3 "The Agent–OS Semantic Gap"; Sec. 5.2 Inspector (p. 6); Sec. 7.2 (pp. 9–10).

- **What it cannot show**: R1 (p. 2): a restore point must reconstruct "filesystem and process effects of prior tool calls—not merely chat history." Chat-only and Chat+FS records cannot represent live processes/services; Crab treats the agent as a black box, so its checkpoints show OS state, not the agent's reasoning.

---

## 4. TraceElephant — "Seeing the Whole Elephant" (arXiv 2604.22708)

- **Id / links**: https://arxiv.org/abs/2604.22708 — HTML https://arxiv.org/html/2604.22708v1 — PDF https://arxiv.org/pdf/2604.22708 (17 pages). Repo https://github.com/TraceElephant/TraceElephant (`code/agent_system`, `code/llm_api_middleware`, `code/trace_locate`, `assets/overview.png`). 220 failure traces from Captain-Agent, Magentic-One, SWE-Agent.

- **Three observability levels (paper's names)**
  1. **Output-only** — "All-at-Once w/o metadata & input", only `output_content`; the paper says this "is exactly the case as Who&When".
  2. **Static** (full static trace) — "the complete execution trace (including metadata, inputs, and outputs fields as shown in Section 3.3)". Ablation variants: *Static w/o metadata*, *Static w/o input*, *Static w/o metadata&input*.
  3. **Dynamic** — static trace + "a replayable execution environment", allowing controlled re-execution and counterfactual probing.

- **Full static trace fields (Sec. 3.3 "Trace Schema and Recorded Fields", p. 4; stored as one JSON object per trace)**
  - `trace_metadata`: `task_id`, `task_instruction`, `system_name`, `agent_configuration` (agent roster, prompts, toolset), `system_architecture` (design docs + implementation code).
  - step records (ordered list), input fields: `step_id`, `agent_id`, `agent_name`, `input_context` (task instruction + inter-agent messages + system-constructed context); output fields: `output_content`, `tool_logs` (tool name, input arguments, outputs, execution status).

- **Sample record (Appendix A.4, p. 13; structure kept, values paraphrased)**
  ```json
  {"trace_metadata":{
     "task_id":"TRIP-001","task_instruction":"Plan a 3-day theme-park visit...",
     "system_name":"Magentic-One",
     "agent_configuration":{"agents":["PlannerAgent","SearchAgent","..."],
                            "prompts":["..."],"tools":["web_search"]},
     "system_architecture":{"description":"centrally orchestrated, role-specialized",
                            "code":["orchestrator.py","agents/*.py"]}},
   "steps":[
     {"step_id":1,"agent_id":0,"agent_name":"PlannerAgent",
      "input_context":"Task: ...","output_content":"I will split this into ..."},
     {"step_id":2,"agent_id":1,"agent_name":"SearchAgent",
      "input_context":"...","output_content":"...","tool_logs":[{"tool":"web_search","args":{},"output":"...","status":"ok"}]}]}
  ```

- **Annotation format (Sec. 3.4 p. 5; App. A.5 p. 14)**: two labels per failed trace — (1) the **responsible agent/component**, (2) the **decisive failure step** (`step_id`). Three annotators with ≥1 yr MAS experience, three rounds (independent → joint review of uncertain cases → cross-check); first-round Krippendorff's α = 0.72 (agent), 0.64 (step); final labels unanimous.

- **Results table (Table 2, p. 6, "All-avg, w/ Ground Truth", agent-level / step-level accuracy %)**
  | Technique | Agent | Step |
  |---|---|---|
  | All-at-Once | 62.2 | **28.1** |
  | Binary Search | 38.9 | 12.9 |
  | Step-by-Step | 60.9 | 16.7 |
  | Static Agentic | 65.9 | 30.3 |
  | Dynamic | 66.7 | **33.3** |

  Table 3 (p. 6) ablation: All-at-Once 0.62/0.28 → w/o metadata 0.55/0.21 → w/o input 0.54/0.18 → w/o metadata&input 0.51/**0.16**; Static Agentic 0.66/0.30 → … → 0.54/0.17. Text: going output-only drops step-level accuracy "from 28% to 16%" and agent-level 62%→51%; full traces improve attribution by up to 76%.

- **Figures**
  - Fig. 2 "Overview of TraceElephant." — https://arxiv.org/html/2604.22708v1/figures/overview.png (HTTP 200), PDF p. 4.
  - Fig. 1 partial-observability failure case — https://arxiv.org/html/2604.22708v1/figures/show_case_v3.png (HTTP 200).

- **Section / page**: Sec. 3.3 (p. 4), Sec. 3.4 (p. 5), Sec. 4.1 (p. 5), Tables 2–3 (p. 6), Sec. 4.2.3 output-only analysis, App. A.4 (p. 13), A.5 (p. 14), A.6.2 (p. 15).

- **What it cannot show**: output-only logs — "in at least 21% of instances, developers cannot reliably perform failure attribution using output-only logs." Who&When-style traces lack the role-specific prompt, exact visible history, system-constructed context, agent configuration and tool/environment info, so they show order but not what each component actually observed. Limitations (Sec. 7): only three MASs.

---

## 5. Safe to Resume? (arXiv 2608.29381)

- **Id / links**: https://arxiv.org/abs/2608.29381 — HTML https://arxiv.org/html/2608.29381v1 — PDF https://arxiv.org/pdf/2608.29381 (16 pages). "Breaking Execution Continuity of Agent Execution via Rollback."

- **Table I (p. 3) "Checkpoint and rollback mechanisms in representative agent systems"**, columns `System | State Scope | Captured State | Checkpoint Creation | Restoration` — 5 representative rows:
  | System | Scope | Captured state | Created | Restored |
  |---|---|---|---|---|
  | LangGraph | Framework | graph state: messages, intermediate results, pending execution state | automatic at each superstep once persistence enabled | resume latest or pick earlier checkpoint for replay/branching |
  | CrewAI | Framework | crew/flow/agent state: task progress, outputs, memory | event-driven; task completion default trigger | restore selected checkpoint, skip completed tasks |
  | Hermes | Workspace | project files; rollback also adjusts last conversation turn | automatic before file mutations / destructive commands | `/rollback` to a workspace checkpoint or single file |
  | Cline | Workspace | project files tied to task-history position | automatic after file edits and terminal commands (default on) | restore files, task history, or both |
  | E2B | OS/VM | sandbox filesystem + memory incl. running processes | explicit `create_snapshot()` | new sandbox from snapshot |

  The 12 systems classified in Sec. II (p. 2): **Framework-state** — LangGraph, CrewAI, LlamaIndex Workflows, Google ADK, Microsoft Agent Framework; **Workspace-state** — Hermes, Cline, Gemini CLI, Claude Code; **OS/VM-state** — E2B, CRAB, DeltaBox.

- **Five failure modes SF1–SF5 (Sec. IV, pp. 5–7; one figure each, Figs. 2–6)**
  - **SF1 Incomplete internal state coverage** — a checkpoint omits internal state required to safely resume.
  - **SF2 Inconsistent checkpoint state** — captured states are individually present but mutually inconsistent (e.g. workspace and conversation captured at different points).
  - **SF3 External state mismatch** — restored internal state encodes assumptions about an outside world that no longer holds.
  - **SF4 Unbound nondeterministic replay** — re-executed post-checkpoint operations yield a different outcome not bound to the carried-over security decision.
  - **SF5 Unrecorded external effects** — an action after the checkpoint had an effect outside the boundary, but rollback erases the internal record that it happened (e.g. duplicate payment).

- **Sample record**: the paper defines no record format; the unit is a Table I row (above) and the trace-based detector's per-event `In_i` / `Out_i` dependency sets (Sec. VI-A2). Closest "record": a checkpoint `C_K = (s_i^{k_i})` — a tuple of per-component state versions.

- **Figures**: Fig. 1 "System model for agent checkpoint and rollback" (p. 3–4); Figs. 2–6 one per SF (pp. 5–7); Fig. 7 methodology. The HTML has **no raster images** for these (inline vector), so cite the PDF pages.

- **Section / page**: Sec. II-A/B/C (pp. 2–3), Table I (p. 3), Sec. III system model (pp. 3–4), Sec. IV SF1–SF5 (pp. 5–7), Sec. V attacks on Hermes / Cline / LangGraph, Sec. VI empirical study (347 traces, 1,735 executions, five C/R systems).

- **What it cannot show**: Sec. II-B — workspace checkpoints "generally exclude runtime state such as process memory, installed system state, active services, and files outside the selected workspace"; framework checkpoints leave workspace and runtime state outside the boundary. Core claim (Intro): "Correct rollback does not imply secure recovery" — a faithful checkpoint can't record whether the facts it carries (validated, authorized, not-yet-sent) are still true.


<!-- ===== graph-family ===== -->

# Provenance-graph family: how each paper concretely represents an agent-run audit record as a graph

All arXiv HTML versions checked 2026-09-09. Image URLs verified HTTP 200 with `curl -sI`. Page numbers are PDF page numbers from `arxiv.org/pdf/<id>` via pypdf.

---

## 1. PROV-AGENT (Flowcept)

- **Title:** PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows
- **id:** arXiv:2508.02866 (v3, e-Science 2025). HTML: https://arxiv.org/html/2508.02866v3 . Code: https://github.com/ORNL/flowcept
- **Where:** Sec. III "A Provenance Model for Agentic Workflows", p.3; implementation Sec. IV-A, p.4; example graph Sec. IV-B "End-to-end Provenance Graph", p.5.

### Node / edge vocabulary (as named in the paper, Sec. III)
Everything is a subclass of one of the three W3C PROV core classes:

| PROV core | PROV-AGENT subclasses (node types) |
|---|---|
| `prov:Activity` | `Campaign`, `Workflow`, `Task`, `AgentTool` (one tool execution, MCP terminology), `AIModelInvocation` (one prompt->response call) |
| `prov:Entity` | `DataObject` and its subclasses `DomainData`, `SchedulingData`, `TelemetryData`, `Prompt`, `ResponseData`, `AIModel` (model metadata: name, provider, temperature...) |
| `prov:Agent` | `AIAgent` (plus standard `Person` / `Organization` for campaigns) |

Edges are plain PROV relations, no new edge types:
- `used` (Task/AgentTool/AIModelInvocation -> input entity; AIModelInvocation `used` `Prompt` and `used` `AIModel`)
- `wasGeneratedBy` (output entity -> activity; `ResponseData wasGeneratedBy AIModelInvocation`)
- `wasAssociatedWith` (AgentTool / AIModelInvocation -> `AIAgent`; Campaign -> Person/Org)
- `wasInformedBy` (AgentTool -> AIModelInvocation: "tool depends on LLM results")
- `wasAttributedTo` (ResponseData / agent-generated DomainData -> `AIAgent`)
- `wasDerivedFrom` is part of the PROV base (Fig. 2) but the paper's own examples use `used`/`wasGeneratedBy` chains rather than explicit derivation edges.
- `subClassOf` (dashed, in the data-model figure only)

### One sample record (Flowcept JSONL, structure from the repo; paper itself shows no JSON)
The paper prints no JSON. The Flowcept implementation stores every activity as one `TaskObject` line in a JSONL buffer / MongoDB. The PROV-AGENT class is carried in the `subtype` field (`flowcept/commons/vocabulary.py`, enum `PROV_AGENT`). Structure with paraphrased values:

```jsonc
{ "type": "task",
  "subtype": "ai_model_invocation",        // or "agent_tool"  (PROV-AGENT Activity class)
  "task_id": "uuid",
  "activity_id": "llm_interaction",        // for agent_tool: the tool function name
  "agent_id": "agent-uuid",                // -> AIAgent (wasAssociatedWith)
  "parent_task_id": "uuid-of-agent_tool",  // -> the AgentTool that wasInformedBy this call
  "workflow_id": "uuid", "campaign_id": "uuid",
  "used":      { "prompt": "Which control result is best for layer 12?" },   // Prompt entity
  "generated": { "response": "Result B; scores 0.91 vs 0.74" },               // ResponseData entity
  "custom_metadata": { "llm_usage": { "input_tokens": 812, "output_tokens": 55 },
                       "response_metadata": { "model_name": "gpt-4o" } },     // AIModel entity
  "started_at": 1.72e9, "ended_at": 1.72e9, "status": "FINISHED",
  "telemetry_at_end": { "cpu": {}, "gpu": {} },    // TelemetryData
  "hostname": "frontier-node-0123"                  // SchedulingData
}
```
Recorded fields per the code docstrings: `ai_model_invocation` -> `used.prompt`, `generated.response`, `custom_metadata.llm_usage`, `custom_metadata.response_metadata`; `agent_tool` -> `used` = tool input args, `generated` = tool return value. Paper Fig. 4 (p.4) shows the capture code: `@mcp.tool() @flowcept_agent_tool def evaluate_scores(...)` with `llm = FlowceptLLM(ChatOpenAI(model="gpt-4o"))`.

### Figures
- **Data model:** Fig. 3, p.3 — "PROV-AGENT: A W3C PROV Extension for Agentic Workflows. Dashed arrows represent subClassOf." SVG: https://arxiv.org/html/2508.02866v3/PROV-AGENT.svg (200)
- **Concrete example graph (best):** Fig. 5(A), p.5 — instantiation for an additive-manufacturing loop: `Sensor_Driver_i` -> `Sensor_Data_i` -> `Physics_Model_i` -> `Model_Evaluation_i` -> `Scores_i` -> `Agent_Tool_i` (AgentTool, associated with `Analysis_Agent_i`) -> `LLM_Invocation_i` uses `Prompt_i`, generates `Response_i` -> `Agent_Decision_i`; decision at layer i feeds layer i+1. Caption notes arrows are drawn reversed from PROV convention for top-down reading. PNG: https://arxiv.org/html/2508.02866v3/instantiation_am.png (200)
- Base PROV model reproduced as Fig. 2, p.2: https://arxiv.org/html/2508.02866v3/w3c_prov.png (200)

### What it cannot show
Not stated as a limitation section. Fig. 5 text notes `Campaign`, `Workflow`, `TelemetryData`, `SchedulingData` and PROV `Location` are recorded in the DB but omitted from the drawn graph; the implementation "records only the agent's ID and name" (no model/tool version state yet).

---

## 2. LEDGER

- **Title:** LEDGER: Claim-to-Evidence Trace Graphs for Auditing LLM Agents (Layered Evidence and Decision Graphs for Execution Review)
- **id:** arXiv:2608.18398 (v1). HTML: https://arxiv.org/html/2608.18398v1 . No public code link in the paper (LLNL).
- **Where:** Sec. 3.1 "Capturing and Structuring Trace Records", p.3; Sec. 3.2 "Constructing Layered Review Structure", pp.4-5 (Tables 1-2); Sec. 3.3 "Linking Artifacts and Audit Paths", p.6 (Table 3); limitations Sec. 6 "Discussion", p.10.

### Three layers (bottom-up)
1. **Trace Records** — deterministic, from Codex hooks (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PermissionRequest`, `Stop`) plus the copied transcript JSONL. Normalized into `trace.json` with record families: session/turn context, visible messages, tool calls and results, lifecycle events, reasoning summaries, parse errors, coverage records.
2. **Evidence Nodes** — LLM-grouped units of work (Table 1, p.5):

| type | category | meaning |
|---|---|---|
| `action` | `control` | session/turn/task lifecycle record |
| `action` | `user_message` | user request, correction, approval |
| `action` | `assistant_message` | plan, update, reasoning note, answer |
| `action` | `tool_call` | one tool invocation + its result, grouped by shared id |
| `artifact` | n/a | inspectable object used/produced/referenced (file, patch, plot, table) |

3. **Workflow Nodes** — phases grouping Evidence Nodes (Table 2, p.5): `context`, `plan`, `inspect`, `execute`, `validate`, `claim`.

### Edge types (Table 3, p.6) — directed in trace order, both layers plus cross-layer
`frames`, `uses`, `produces`, `informs`, `checked_by`, `supports`.
(uses = work unit takes artifact as input; produces = creates/changes artifact; checked_by = change is checked by a validation step; supports = evidence justifies a claim.) Cross-layer edges link each Workflow Node back to its Evidence Nodes and Trace Records.

### Sample record
The paper contains no JSON listing. Closest concrete thing: the node-detail panel (Sec. 4, Fig. 4, p.7) shows for a selected Evidence Node its category, status, description, evidence links, Trace Record links, related artifacts, plus the recorded tool call and tool result. Reconstructed structure (paraphrased, not verbatim):

```jsonc
// Evidence Node
{ "id": "ev_17", "type": "action", "category": "tool_call",
  "description": "ran pandas groupby on cleaned housing table",
  "trace_record_refs": ["tr_0412", "tr_0413"],      // PreToolUse + PostToolUse rows
  "workflow_node": "wf_execute_2",
  "artifacts": ["art_daily_pattern.png"] }
// Edge
{ "source": "ev_17", "target": "art_daily_pattern.png", "type": "produces" }
{ "source": "art_daily_pattern.png", "target": "wf_claim_1", "type": "supports" }
```

### Figures
- **Best single concrete graph:** Fig. 1, p.4 — Evidence-node view of a housing-recommendation data-analysis session; blue action nodes, orange artifact nodes, legend at left. https://arxiv.org/html/2608.18398v1/figures/low_node_example.png (200)
- Fig. 2, p.5 — Workflow-node view (phase level). https://arxiv.org/html/2608.18398v1/figures/High_node_examples.png (200)
- Fig. 7, p.14 — full Case Study 1 trace graph. https://arxiv.org/html/2608.18398v1/figures/Case1Graph.png (200)
- Fig. 4, p.7 — event-detail view (what one node's record looks like). https://arxiv.org/html/2608.18398v1/figures/EventView.png (200)

### What it cannot show (stated, Sec. 6, p.10)
Everything above the Trace Record layer is LLM-inferred, "not fully deterministic": grouping, node category and edge type "can be incomplete, unstable, or wrong", so the graph is "an audit aid rather than a source of truth". Edge boundaries (`uses`/`informs`/`supports`/`checked_by`) blur in long sessions; the graph does not encode uncertainty or missing support.

---

## 3. GRADE

- **Title:** Grade: Graph Representation of LLM Agent Dependency and Execution
- **id:** arXiv:2606.22741 (v1). HTML: https://arxiv.org/html/2606.22741v1 . Code: https://github.com/yzhao062/grade (package in `src/grade/__init__.py`)
- **Where:** Sec. 2.1 "Two Edge Layers, the Dependency Layer Graded by Source" and 2.2 "The Formal Class", p.3; formal tuple App. A.1, p.11; "Limitations" paragraph p.9; Fig. 1 p.1.

### Node types (4)
Paper: `agent`, `decision`, `tool call`, `external resource` ("the state a decision reads or writes, such as a database row or a source file").
Repo constant: `NODE_TYPES = ("agent", "decision", "tool_call", "dependency_resource")`.

### Two edge layers
- **Execution layer** E_X (observed, "free", read deterministically off the trace): `emits` (agent -> its decision/tool node), `handoff_to` (step -> next step). Repo: `EXECUTION_EDGES = ("emits", "handoff_to")`. Formal label κ ∈ {emit, handoff}.
- **Dependency layer** E_D (reliance, costly): `depends_on` (step -> earlier node whose state it used), `reads`, `writes` (step <-> resource). Repo: `DEPENDENCY_EDGES = ("depends_on", "reads", "writes")`. Constraint (u,v) ∈ E_D ⇒ t(u) < t(v).

### Edge grades (source map σ: E_D -> {observed, declared, inferred}), Sec. 2.1 p.3
- **observed** — the access already appears in the trace content (a coding step edits a named file; a DB step reads a named row).
- **declared** — added instrumentation logged the read/write events the raw trace omits.
- **inferred** — no access information; the edge is posited under a named assumption, weakest being A_0 "full prior history" (every earlier step), which makes |E_D| = C(n,2) and collapses the layer to run size (saturation ratio ρ = |E_D| / C(n,2)).
Grade is per edge, not per run. Formal object: G = (V, E_X, E_D, τ, t, σ) with τ: V -> {agent, decision, tool, resource}, t: V -> R≥0.

### Sample record (repo README quickstart; input step dicts, then networkx attrs)
```python
steps = [
  {"idx": 0, "agent": "a", "kind": "tool_call"},
  {"idx": 1, "agent": "a", "kind": "decision",  "deps": [0]},
  {"idx": 2, "agent": "a", "kind": "tool_call", "deps": [1]},
]
G = build_graph(steps, dependency="explicit", shared_resource=False)
```
Resulting nodes/edges (from `build_graph` source):
```
node "agent::a"   {ntype:"agent", name:"a"}
node "step::1"    {ntype:"decision", agent:"a", idx:1}
edge agent::a -> step::1   {etype:"emits"}         # execution layer
edge step::0  -> step::1   {etype:"handoff_to"}    # execution layer
edge step::1  -> step::0   {etype:"depends_on"}    # dependency layer
edge step::k  -> resource::shared_state {etype:"reads"} / {etype:"writes"}  # if shared_resource=True
```
Note: the repo does NOT store σ on the edge. The grade is chosen globally by the `dependency=` argument: `"explicit"` = observed (from logged `deps`), `"chain"` / `"full_context"` = inferred. There is no JSON schema file in the repo (root: `README.md`, `src/`, `experiment/`, `assets/`, `tests/`, `pyproject.toml`, `CITATION.cff`).

### Figure
- **Fig. 1, p.1** — a booking run (read -> hold -> confirm) as one two-layer graph: solid execution edges, coral dependency edge "confirm relies on the price read fetched earlier"; the run fails on a reliance the execution trace never records. https://arxiv.org/html/2606.22741v1/twolayer.png (200)
- Repo overview image: https://raw.githubusercontent.com/yzhao062/grade/main/assets/grade_overview.png

### What it cannot show (stated)
- Sec. 2.1: "Nothing in the trace states what a step relied on" — the dependency layer must be supplied, and under A_0 it degenerates to a function of step count (Sec. 5.1, p.6-7).
- Limitations, p.9: the observed grade is "a principled heuristic"; corpora are mostly coding/DB tasks; the claim is only above-chance transfer, not the size of the lift. README (revised 2026-09-08) withdraws the "dependency layer predicts failure" claim against nonlinear baselines; only execution-layer fault localization stands.
- Sec. 5.4: a single edge weight / generic message passing cannot represent the observed-vs-inferred distinction.

---

## 4. AgentRx

- **Title:** AgentRx: Diagnosing AI Agent Failures from Execution Trajectories
- **id:** arXiv:2602.02475 (v2). HTML: https://arxiv.org/html/2602.02475v2 . Code: https://github.com/microsoft/AgentRx
- **Where:** Sec. 3.1-3.3 (constraint synthesis, guarded constraints, "Validation Log"), p.5; constraint schema App. F.1-F.2, p.22; violation example App. G, p.23; Limitations Sec. 7, p.10.

### Not a graph — a step-indexed set of violations
Pipeline: `Raw logs -> Trajectory IR -> Invariants -> Checker -> Judge -> Reports`. Trajectory T = <s_1..s_n>, each step has substeps with fields agent/role name, tool name, step index, content. A constraint C = (guard G_C, assertion Φ_C); evaluation returns `(skip, ∅)` if guard false else `(sat|viol, evidence e)`. Validation log (Sec. 3.3):

  V := { (k, C, e) | C ∈ C_k, G_C(T≤k, s_k) = 1, (viol, e) = Eval_C(k) }

Constraint kinds (`constraint_type` / `invariant_type`): `SCHEMA | PROTOCOL | RELATIONAL_POST | PROVENANCE | TEMPORAL | CAPABILITY | ANY`; `check_type`: `python_check | nl_check`. Global constraints from tool schema + policy; dynamic per-step constraints from task instruction + prefix T≤k.

### Example constraint (App. F.2, p.22, semantic/NL; structure with values abridged)
```jsonc
{ "assertion_name": "explicit_user_confirmation_before_write_actions",
  "taxonomy_targets": ["Instruction/PlanAdherenceFailure", "IntentPlanMisalignment"],
  "invariant_type": "TEMPORAL",
  "event_trigger": { "role_name": "assistant", "content_regex": "*",
                     "tool_name": "cancel_pending_order|exchange_delivered_order_items|...|modify_user_address" },
  "check_hint": "before any write-action tool call, the assistant must have described the action + target id and the user must have explicitly confirmed",
  "check_type": "nl_check",
  "nl_check": { "judge_rubric": ["assistant earlier described the write action with same order_id", "user replied yes/confirm before the call", "..."],
                "output_format_template": "{verdict: pass|fail, rubric_results:[{criterion_index, evaluation: CLEAR_PASS|CLEAR_FAIL|UNCLEAR, reasoning}], final_reasoning}" } }
```
App. G (p.23) gives a programmatic one: `tshirt_available_options_match_variants_count`, `invariant_type: RELATIONAL_POST`, `event_trigger.step_index: 7`, taxonomy `MisinterpretationOfToolOutput`, with a `python_check.code_lines` function that counts `variants[*].available == true` in the last `get_product_details` result and compares to the number the assistant stated.

### Example violation entry (repo `agentrx/invariants/checker.py`, dataclass `Violation`; written to `runs/<run>/checker_results/violations_<domain>.json`)
```jsonc
{ "task_id": "tau_retail_0042",
  "step_index": 7,
  "assertion_name": "tshirt_available_options_match_variants_count",
  "invariant_type": "RELATIONAL_POST",
  "check_type": "python_check",            // or "nl_check"
  "severity": "medium",
  "check_hint": "count available variants in get_product_details and compare to assistant's stated count",
  "evidence": { "step_pos": 7, "step_index": 7,
                "matched_substeps": [ { "role": "assistant", "content": "There are 4 available T-shirt options..." } ],
                "judge_response": { "verdict": "fail", "rubric_results": [ /* nl_check only */ ] } },
  "taxonomy_targets": ["MisinterpretationOfToolOutput"] }
```
The judge then picks the first step whose violation evidence explains the failure and emits `(critical step, category, rationale)`. The shipped `out/checker_results/39/violations_tau.json` in the repo is empty (2 bytes); sample trajectories live in `trajectories/tau-retail/*.json` (e.g. `misinterpretation_tool_output.json`).

### Figure
- **Fig. 1, p.1** — pipeline: failed trajectory + domain policy + tool schema -> AgentRx -> critical failure step, root-cause category, auditable constraint violation. SVG: https://arxiv.org/html/2602.02475v2/fig1.svg (200)
- No graph rendering exists; the record is a list, not a graph.

### What it cannot show (stated, Sec. 7, p.10)
Taxonomy may not cover other domains; the judge "can be misled when validation signals are weak or contain false positives", i.e. downstream/noisy violations misdirect attribution. Constraints are LLM-generated, so the log inherits their coverage gaps.

---

## 5. Adaptive Influence Graphs (AIG)

- **Title:** Adaptive Influence Graphs for Failure Attribution in Multi-Agent Systems
- **id:** arXiv:2608.24361 (v1). HTML: https://arxiv.org/html/2608.24361v1 . No code link found in the paper (built on Strands Agents SDK).
- **Where:** Sec. 3 "Method" / 3.1 "Build: Constructing the Graph", p.4; node-type table App. B Table 7, p.12; builder tools App. A Table 6, p.11-12; IG example App. E Fig. 6, p.12-13; AIG example App. F Fig. 7, p.13.

### Graph definition
- Trajectory = sequence (a_t, s_t) of (agent, log content). Builder outputs directed graph G = (V, E).
- **Node boundaries:** each node is grounded in one or more raw-log steps via `step_refs`. Builder 1 (structured logs): consecutive steps by the same agent -> one node (deterministic). Builder 2 (Influence Graph, IG): same partition, LLM adds fields + edges. Builder 3 (AIG): the LLM builder "jointly determines the node boundaries and roles", so nodes may merge non-adjacent actions.
- **Node fields (IG / single-type AIG):** `summary`, `input`, `output`, `authorship` (+ `raw_content`, `step_refs`, `agent`).
- **Typed node vocabulary (AIG, Table 7):** `task` (root, fields `content`, `operative_brief`, `step_refs`), `orchestrator` (`agent_name`, `summary`, `authorship`, `step_refs`), `agent` (`agent_name`, `summary`, `input`, `output`, `authorship`, `defect_recorded`, `step_refs`), `conclusion` (sink, `content`, `step_refs`).
- **Influence / inheritance edges:** a directed edge earlier -> later is drawn only when the later node reused part of the earlier node's work in a way tied to the failure. Each edge carries two annotations: `inherited` (what was carried over) and `effect` (how it went wrong downstream). Edges may skip steps (non-adjacent). Edge set is sparse and may be empty. Builder tools name them `add_inheritance_note` (direct edge) and `add_skip_attribution` (non-adjacent), each carrying a <bias, anomaly> note.
- **Validity predicate Φ(G):** connected, acyclic, exactly one root (`task`) and one sink (`conclusion`); a critic-refiner loop (≤3 rounds) repairs structural and semantic violations.
- **Reader:** starts at the implicated node and walks backward along incoming inheritance edges, moving blame to the source only when the raw log confirms the `effect`; resolves to (agent, step) via `step_refs`.

### Sample record (App. F Fig. 7, p.13; the paper's own JSON, abridged/paraphrased)
```jsonc
{ "nodes": [
    { "id": "A", "step_refs": [0],    "agent": "Data_Extraction_Expert",
      "summary": "received manager's framing: count hep-lat arXiv papers from Jan 2020 with ps",
      "input": "general counting question", "output": "restated plan; carried forward a prior result of 0",
      "authorship": "relayed", "raw_content": "You are given: (1) a task ..." },
    { "id": "C", "step_refs": [2],    "agent": "Computer_terminal",
      "summary": "ran the script; exit 0; printed 0", "input": "script from step 1",
      "output": "exitcode 0; stdout: 0", "authorship": "executed" },
    { "id": "D", "step_refs": [3, 4], "agent": "Verification_Expert",
      "summary": "took 0 as confirmation and terminated", "authorship": "relayed" } ],
  "edges": [
    { "from": "B", "to": "C", "inherited": "ps-detection defined as substring 'ps' in entry_id (a URL field)",
                              "effect": "the flawed heuristic executed and produced 0" },
    { "from": "A", "to": "D", "inherited": "the prior '0 / nothing found' framing",
                              "effect": "used to justify terminating with 0 instead of probing the method" } ] }
```
`authorship` values seen: `authored`, `relayed`, `executed`.

### Figures
- **Builder/Reader pipeline:** Fig. 3, p.4 — builder uses log-inspection + graph-construction tools to produce G; critic-refiner audits validity; reader uses graph + log tools to attribute. SVG: https://arxiv.org/html/2608.24361v1/buildread.svg (200)
- **Best concrete graph rendering:** Fig. 4, p.7 — "The same trace encoded as an Influence Graph and as an Adaptive Influence Graph" (AIG has variable-granularity nodes). SVG: https://arxiv.org/html/2608.24361v1/graph_compare_v20.svg (200)
- Fig. 5, p.8 — reader walking inheritance chords to step 6. SVG: https://arxiv.org/html/2608.24361v1/reader_trajectory_l107_predgreen.svg (200)
- Fig. 1 teaser: https://arxiv.org/html/2608.24361v1/teaser_example.svg (200)

### What it cannot show
No explicit limitations section. By design edges exist only where the builder judged an inheritance relevant to the failure ("unsupported causal links can mislead the reader"), so the graph is query-specific and is not a complete dataflow/provenance record of the run. Node abstractions are LLM-written and must be re-checked against `step_refs`.

---

## 6. W3C PROV minimal example (PROV-N, from the PROV Primer)

- **Source:** W3C PROV Primer, https://www.w3.org/TR/prov-primer/ — Sec. 3.1 Entities, 3.2 Activities, 3.3 Usage and Generation, 3.6 Derivation and Revision (PROV-N tabs). Working-group note, 2013.
- The primer gives PROV-N, Turtle and XML tabs, not PROV-JSON. The Python `prov` library reads PROV-N-equivalent calls and can emit PROV-JSON via `doc.serialize(format='json')`.

Smallest illustrative snippet (verbatim PROV-N statements from the primer, assembled; `-` = unspecified optional argument such as time):
```
entity(exg:dataset1)
entity(exc:regionList)
entity(exc:composition1)
activity(exc:compose1)
used(exc:compose1, exg:dataset1, -)
used(exc:compose1, exc:regionList, -)
wasGeneratedBy(exc:composition1, exc:compose1, -)
entity(exg:dataset2)
wasDerivedFrom(exg:dataset2, exg:dataset1, [prov:type='prov:Revision'])
```
Agent/attribution part (Sec. 3.4) adds `agent(exc:derek, ...)`, `wasAssociatedWith(exc:compose1, exc:derek, -)`, `wasAttributedTo(exc:chart1, exc:derek)`, `actedOnBehalfOf(exc:derek, exc:chartgen)` — the same relations PROV-AGENT reuses for `AIAgent`.

Equivalent with the Python `prov` library:
```python
from prov.model import ProvDocument
d = ProvDocument(); d.add_namespace('ex', 'http://example.org/')
d.entity('ex:dataset1'); d.entity('ex:composition1')
a = d.activity('ex:compose1')
d.used('ex:compose1', 'ex:dataset1')
d.wasGeneratedBy('ex:composition1', 'ex:compose1')
d.wasDerivedFrom('ex:dataset2', 'ex:dataset1')
print(d.get_provn()); print(d.serialize(format='json'))
```

---

## Cross-paper cheat sheet

| Paper | Node types | Edge types | Extra label on edges | Deterministic? | Has JSON example? |
|---|---|---|---|---|---|
| PROV-AGENT | PROV Activity/Entity/Agent subclasses: Task, AgentTool, AIModelInvocation, Prompt, ResponseData, AIModel, DomainData, Telemetry/SchedulingData, AIAgent | used, wasGeneratedBy, wasAssociatedWith, wasInformedBy, wasAttributedTo | none | yes (instrumented) | only via Flowcept JSONL (repo), not in paper |
| LEDGER | Trace Record; Evidence Node (action: control/user_message/assistant_message/tool_call; artifact); Workflow Node (context/plan/inspect/execute/validate/claim) | frames, uses, produces, informs, checked_by, supports | none | records yes; nodes/edges LLM-inferred | no |
| GRADE | agent, decision, tool_call, resource | exec: emits, handoff_to; dep: depends_on, reads, writes | grade σ ∈ {observed, declared, inferred} | exec yes; dep depends on grade | Python dicts in README |
| AgentRx | (not a graph) steps s_k with substeps | violation tuple (k, C, e) | constraint_type, check_type, severity, taxonomy_targets | checks partly LLM | yes (App. F/G + checker.py) |
| AIG | task, orchestrator, agent, conclusion (each with step_refs) | inheritance edges | inherited, effect | LLM-built, validity-checked | yes (App. E/F) |
