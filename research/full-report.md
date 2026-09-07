# Research-direction report: Comparing Auditable Architectures for LLM Agents

Prepared for: NLP master's student, Trier University (engineer, new to research).
Basis: 20 candidate hypotheses, each with a novelty, feasibility and validity review; a verified literature list of ~185 papers; a citation check of the four papers already in the folder.

## 0. How to read this report

- Plain English, short sentences. When a term is used the first time, a one-line gloss follows it.
- The 20 candidates collapsed into 6 distinct ideas. Many candidates were the same experiment written from a different angle. Section 1 shows the merges.
- Ranking is by the reviewers' combined score, but I moved things where a reviewer's reasons justified it. Section 2 explains every override.
- Sections 3 to 8 give the six ideas in full, each with the scoped-down version and the validity fixes the reviewers asked for. Do not run the original version of any of them.
- Section 9 names one default pick and one fallback. Section 10 lists papers to add. Section 11 is a warning about the Verifiability-First paper.

Glossary used throughout:
- **Record**: whatever the system stores about a run (log lines, snapshots, a graph).
- **Log-primary**: an append-only event log is the truth; state is rebuilt by folding the log (ActiveGraph, Temporal, event sourcing).
- **Checkpoint-based**: a snapshot of the state is saved every step or every few steps (LangGraph SqliteSaver, AutoGen save_state, CrewAI @persist).
- **Provenance overlay**: a separate graph of which thing came from which thing (W3C PROV, OpenTelemetry spans, claim-to-evidence graphs).
- **Audit tasks** (from the exposé): failure localization, evidence tracing, execution reconstruction, counterfactual analysis, policy compliance, decision review.
- **Trade-off axes** (from the exposé): storage, implementation complexity, privacy, computational cost.
- **Nian et al. metrics** ("Auditable Agents"): ACR/RF (are actions and their fields in the record), LPC (are lifecycle phases like retries visible), SPDR (share of policies a checker can decide), IS (integrity level 0-3).
- **AAR metrics** ("From Fluent to Verifiable"): PCov (share of claims with a path to a source), PSnd (share of claim-source pairs where the source really supports the claim), AEff (audit effort).
- **Warm-start injection**: replay a good run up to step k, plant one fault, let it continue. The faulty step is then known by construction.
- **By construction**: a result that follows from how you built the experiment, not from anything you discovered. Reviewers flagged this a lot. It is the main thing to design against.

---

## 1. Merges: 20 candidates into 6 ideas

| Merged idea | Source hypotheses | Formulation kept | Why merged |
|---|---|---|---|
| A. Redaction x architecture | H1, H4, H19, plus H7 as the raw-level baseline | H4 (validity "acceptable", cleanest 2x2 fix) | H1, H4, H19 are the same experiment: apply raw / field-masked / hash-only privacy levels to one run recorded three ways, measure which policies stay decidable. H7 (all Nian metrics on one run, no redaction) is exactly the raw level of that experiment. |
| B. Compaction curve | H3, H2 | H3 (validity "acceptable"; operator-based framing) | Both ask what audit tasks die when a log is compacted or snapshotted. H2 is tied to ActiveGraph and its premise ("ActiveGraph has no compaction") is stale since v1.5. H3's operator framing (keep-latest, prefix snapshot, LLM summary) covers H2's interval sweep as one operator. |
| C. Storage vs rebuild cost | H6, H10, H11 | H6 (feasibility "strong"), with H11's corrected cost model as a sub-part | All three measure how record size and rebuild cost move with snapshot interval. H10's headline (quadratic checkpoints vs linear logs) is already published (The Hidden Footprint; LangGraph DeltaChannel PR). H11's objective function was mis-specified. H6 keeps the still-open part: rebuild fidelity and cost as a function of interval. |
| D. Record format x fault type | H5, H13, H16, H14 | H5 (novelty "strong"), absorbing H13's state-diff arm, H16's controls and H14's format-vs-completeness split | All four give the same fixed LLM auditor the same faulty run in different record formats and ask which format helps on which fault. H13 is the checkpoint-diff sub-case; H16 is H5 with a length moderator; H14 is the control every reviewer demanded (is it structure or content?). |
| E. Overlay as a view of the log | H12, H9, H8, H20 | H12 (validity "acceptable"; dose-response reframe), with H9's tool-mediated vs in-call factor | All four ask whether a claim-to-evidence graph built after the run from the log matches one captured during the run. H8 and H20 were rated validity "weak" because their overlay arm wins by construction. H12's reframing (vary what the log contains) fixes that; H9's factor (did evidence enter via a tool call or inside one model call) is the mechanism. |
| F. Fork validity x recovery boundary | H18, H15, H17 | H18's reviewer fix (2x2 on one harness), with H15's dose-response in external writes | All three compare a cached-prefix fork (log) with a checkpoint-restore fork, with and without restoring external state. H17's "simulated counterfactual" arm was rated weak (base-rate problem). The three reviewers independently proposed the same 2x2 design. |

---

## 2. Ranking and overrides

| Rank | Idea | Combined score (best source) | Override notes |
|---|---|---|---|
| 1 | A. Redaction x architecture | 3.67 | Novelty rated **strong** by all three source reviews (H1, H4, H19). Cheapest to run (no LLM judge). Validity "acceptable" for H4 after the 2x2 fix. Kept at 1 because the fix is cheap and the privacy axis is otherwise uncovered. |
| 2 | D. Record format x fault type | 3.67 | Novelty **strong** (H5). Validity "acceptable" but every reviewer flagged power (too few runs per cell) and judge cost (about 4,000 calls, not 1,400). Ranked 2 not 1 because it is the hardest to run cleanly for a first-time researcher. |
| 3 | B. Compaction curve | 3.67 | Novelty **strong** (H3). Validity "acceptable" but the Kafka half is near-tautological; the empirical content is the schema-blind checker and the transient/terminal judge split. Ranked 3 because part of the result is by construction. |
| 4 | E. Overlay as a view | 3.33 | Novelty "acceptable": the inline-vs-post-hoc contrast already exists at answer level (Saxena et al. 2025 G-Cite vs P-Cite; ALCE PostCite). New only as a dose-response over log completeness on agent runs. |
| 5 | C. Storage vs rebuild cost | 3.33 | Feasibility **strong** (two reviewers). Novelty **weak** for H10: The Hidden Footprint (arXiv 2607.11149) already fits growth exponents for LangGraph checkpoints, and LangGraph now ships DeltaChannel. Sunk from a possible 2 to 5 for that reason. Still the safest to execute. |
| 6 | F. Fork validity | 3.00 | Novelty "acceptable": Shepherd, Crab and AgentCheck each cover one arm. Validity "weak" for H17. Most engineering (two fork mechanisms plus environment snapshots). |

Ties at 3.67 were broken by execution risk for a novice: A (deterministic, cheap) before D (LLM judge, power problems) before B (part by construction).

---

## 3. Idea A (rank 1): What survives redaction — which policies stay checkable in a log, a checkpoint, and a provenance graph

**Name.** Redaction x Architecture.

**Hypothesis in one sentence.** When the same privacy treatment (field-level PII masking, or hash-only content) is applied to one run recorded as an event log, a checkpoint store and a provenance graph, the set of audit questions that become unanswerable is decided by which typed fields survive in each record, so it differs by record format, and the checkpoint loses the most because it stores state as one blob.

**Why it matters.** Privacy is one of the exposé's four trade-off axes and no paper measures it for agent records: the IETF Agent Audit Trail draft says raw input and output MUST NOT be stored, but nobody has checked what that makes unauditable. Nian et al. state Proposition 1 (one missing field kills a policy class) and list privacy mechanisms as an open problem; this is the first measurement of that cost per record format.

**What would confirm / refute it.**
- Confirm: under hash-only, name/order and approval policies stay decidable in all three records (the IETF draft keeps tool_name and outcome in clear), content-dependent policies become undecidable everywhere, and the blob-serialized checkpoint loses at least 4 more of 20 policies than the typed log under field-level masking. Also: a typed-JSON checkpoint behaves like the log (so the driver is serialization granularity, not family).
- Refute: all three records lose the same policies at each level (privacy cost is architecture-independent), or the log loses most (NER over-masks structural strings like tool names).
- Either result is useful for the exposé. Pre-register both.

**The experiment, step by step (scoped-down, with validity fixes).**
1. Workflow (weeks 1-2): one LangGraph agent, 12-15 steps, 5-7 mock tools, an approval gate, a read of a "sensitive" data class followed by an external-looking call, a retry, a short cited summary. Seed tool outputs with synthetic PII via Faker. Drive the tool-call sequence by a script (fake ChatModel), so violating and approval-missing variants are guaranteed. 40 tasks x 3 variants = 120 runs. Zero or near-zero API cost.
2. Three recorders on the same run (week 3): (a) hash-chained JSONL event log from a callback handler, fields per the IETF draft schema; (b) LangGraph SqliteSaver checkpoints, as shipped; (c) PROV-JSON graph via the `prov` library built from the callback events. Assert byte-identical tool I/O across the three.
3. Add the serialization control, the key validity fix: run the checkpoint arm twice, once as shipped (msgpack blob) and once with a schema-aware JSON serializer. This gives a 2x2: family x serialization granularity. If typed checkpoint equals typed log, say so; that is the finding.
4. Privacy levels (week 4), applied by ONE schema-agnostic redactor to all records: raw; field-level (Presidio regex plus NER over every string leaf, regardless of key); hash-only (the IETF rule as a fixed key list: input, output, parameters, response, reasoning hashed; tool_name, action_type, timestamp, outcome, approval flag kept). Publish the field map before running. Optional fourth level: LangGraph EncryptedSerializer (encryption at rest), because that is the checkpoint family's real privacy mechanism and it preserves replay for key holders.
5. Policies (weeks 5-6): 20 structural rules in three classes, fixed and published before any run, derived from Nian's structural taxonomy and AgentPex's rule types: name/order ("tool X after tool Y"), approval ("X requires prior approval"), content-dependent (at least 10, diverse: data-class label, argument value, output value, error text). Verify SPDR = 1.0 for all three records at raw level first (information equivalence). A single deterministic checker runs over one intermediate representation produced by three published extractors; it returns comply / violate / undecidable and records which fields it consulted.
6. Ground truth: violations planted by the script (drop the approval, leak an email, cite an unfetched source). Gold verdicts known by construction.
7. Metrics: SPDR per record x level x policy class (report exact counts, k of 20); the field-dependency table (this is the honest Proposition 1 check); ACR/RF at each level; bytes per run raw and gzip, and bytes after stripping serializer metadata (control for LangGraph issue #7714's bloat); redaction wall-clock; NER false positives on structural strings (tool names, the label "PII", step ids), measured; structural replay (rebuild step-type sequence) and re-execution from step k with a raw-record control (Replay Gap style) for all three records; hash-chain verification after redaction using a salted content hash plus summary hash (Palantir redactable-log design), otherwise the chain trivially breaks.
8. Runs: 120 runs x 4 record variants x 3-4 levels = about 1,400-1,900 record instances, all mechanical. Optional LLM checker on a 100-instance subsample, reporting agreement with the deterministic checker and the rate of "hallucinated decidability".
9. Weeks 7-8: run and tables. Week 9: optional LLM-checker subsample. Weeks 10-11: writing. Week 12: buffer.

**Closest prior work and what is new.**
- Auditable Agents (Nian et al. 2026), https://arxiv.org/abs/2604.05485 — source of SPDR, ACR/RF, Proposition 1; runs no redaction experiment.
- DEMM-Bench (Solozobov 2026), https://arxiv.org/abs/2606.20634 — same-scenario-across-regimes design with structural degradations; no PII masking, no hashing, no checkpoint regime, synthetic cases. Position explicitly against it.
- RedAct (Xu, He, Fung 2026), https://arxiv.org/abs/2606.10813 — only quantitative redaction study; flat traces, skill leakage, no policies.
- IETF draft-sharif-agent-audit-trail-03, https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/ — hash-only mandate, no evaluation.
- TelemetrySuffBench (2026), https://arxiv.org/abs/2608.07899 — mask-and-measure template for diagnosis, not privacy.
- LangGraph checkpointers docs (EncryptedSerializer, DeltaChannel), https://docs.langchain.com/oss/python/langgraph/checkpointers.
- New: first same-run, three-record, three-level redaction comparison scored with policy decidability, with serialization separated from family, and the first measurement of what the IETF hash-only rule costs.

**Main risk and mitigation.** The result can be true by construction because the student writes the schemas, the field map and the checker. Mitigation: pre-register the field map and the 20 policies, use as-shipped implementations, prove SPDR = 1.0 at raw level, present the analytic decidability matrix and then put the empirical weight on the non-obvious rows: NER false positives, salted vs unsalted hashes, side channels (lengths, token counts), replay after redaction, and the typed-vs-blob checkpoint contrast. Second risk: "where is the NLP?" Answer: the redactor is an NER system and its false-positive rate on structured records is itself the NLP result; add the LLM-checker subsample.

**Effort.** 10-12 weeks part-time. Under 50 USD in API cost.

**Fit with the exposé.** Audit tasks: policy compliance (main), execution reconstruction (ACR/RF and replay under redaction), evidence tracing (PCov survival for the overlay), evidence integrity. Axes: privacy (main), storage (bytes per level), implementation complexity (one redactor per format), computational cost (redaction and verification time).

---

## 4. Idea D (rank 2): Same run, three records — which faults can a fixed auditor find in each?

**Name.** Record Format x Fault Type.

**Hypothesis in one sentence.** When the same faulty run is shown to the same LLM auditor as an event log, as per-step state diffs, or as a provenance graph with dependency edges, the format that localizes the fault best depends on the fault class (log for tool faults, diffs for state-corruption faults, graph for wrong-source faults), and the graph's edge grows with run length.

**Why it matters.** Failure localization is the first audit task in the exposé and the best-studied one, yet every existing benchmark (Who&When, TRAIL, TraceElephant) uses one log-shaped record. If the interaction exists, the choice of record architecture is a lever an auditor can pull; if it does not, structure matters less than content, which is an equally useful null result.

**What would confirm / refute it.**
- Confirm: a significant format x fault-class interaction in a mixed-effects logistic model (run as random effect), with each format's paired margin on its predicted class at least 10 points and a CI excluding zero; position-only and shuffled-label controls near chance.
- Refute: one format dominates on every class; or all formats within noise; or the gains vanish under the information-equivalent arm (then it was record coverage, not structure).

**The experiment, step by step (scoped-down, with validity fixes).**
1. Workflow (weeks 1-2): one plain LangGraph agent over a multi-hop QA set with fixed passages (HotpotQA, MuSiQue or FRAMES) so tools are offline lookups and evidence faults have well-defined sources. Tools pass output handles (ids), so dependency edges are recorded by construction. Two length tiers, about 20 and about 40 steps.
2. The key validity fix, one canonical event stream, three renderings: derive all three formats losslessly from ONE recorded event stream (event log; per-step state diffs of application state only, not the message list; PROV graph with used/wasDerivedFrom edges). Verify each rendering converts back to the stream. This is the "information-equivalent" arm and the primary test of format. Run the native recorders (SqliteSaver, callback log, inline PROV) as a secondary "coverage plus format" arm and publish a fault-type x record "evidence present?" matrix.
3. Add a fourth arm: log plus post-hoc inferred edges (a simple heuristic or a first judge pass, GRADE/CHIEF style). Without it the paper cannot support "observed edges beat inferred edges", which is the real novelty claim.
4. Ground truth (weeks 4-5): warm-start injection through the tool or model wrapper, never by text edits; three fault classes, two types each (tool: wrong argument, corrupted output; state: dropped note write, overwritten note; evidence: claim cited to wrong source, claim with no source). Stratify k over early/middle/late. Sham-injection arm (wrapper intercepts, passes through unchanged). Byte-diff clean vs faulty records to confirm only the fault differs. 40-50 tasks x 6 faults = 240-300 faulty runs plus 25 clean controls.
5. Auditor: one cheap fixed model, temperature 0, 3 samples, fixed prompt, must output (canonical step id, category, pointer). Assign one canonical step id to every log event, checkpoint and PROV activity, and score only at that level. A second auditor from a different model family on a subsample.
6. Metrics: step exact match and +/-3 (LongRCA style), category F1 (TRAIL style), tokens per audit, bytes per record, position-only baseline, a trivial non-LLM rule auditor per record (if the rule scores near 100% and the LLM 60%, the gap is judge parsing, not record content). PCov/PSnd only as a small descriptive add-on on evidence faults.
7. Token budget: report uncapped as primary at the short tier; cap only at the long tier with a published truncation rule.
8. Runs: about 300 runs x 4 formats x 3 samples = about 3,600 judge calls at one tier; budget 50-150 USD with a mini-class model. Do a 10-run x 4-format pilot in week 3 and inspect renderings side by side.
9. Weeks 6-7 full run and scoring; 8-9 analysis; 10-11 writing; 12 buffer.

**Closest prior work and what is new.**
- TraceElephant (ACL 2026), https://arxiv.org/abs/2604.22708 — varies record completeness (16% to 28.1% to 33.3% step accuracy); all conditions log-shaped.
- TelemetrySuffBench (2026), https://arxiv.org/abs/2608.07899 — masks provenance/dependency attributes; OTel views cripple localization; synthetic traces, no checkpoint arm.
- Adaptive Influence Graphs (2026), https://arxiv.org/abs/2608.24361 — representation ladder on Who&When (46.4 to 55.2 step accuracy); graph built post hoc.
- Reasoning Provenance for Autonomous AI Agents (2026), https://arxiv.org/abs/2603.21692 — states the checkpoint vs trace vs provenance distinction; no experiment.
- CatchBench (2026), https://arxiv.org/abs/2608.22808 — artifact controls.
- Who&When Pro (2026), https://arxiv.org/abs/2607.09996 — injection recipe.
- New: the record is the manipulated variable with identical content; the fault-class interaction; runtime-captured vs post-hoc edges on the same runs; the checkpoint-diff arm has no precedent.

**Main risk and mitigation.** Power and cost: 25 items per cell cannot show a 10-point effect. Mitigation: paired design, cluster bootstrap over tasks, mixed-effects interaction as the single primary test, 40-50 tasks, one auditor as primary. Second risk: a LangGraph checkpoint diff that includes the message list collapses into the log. Mitigation: render application state only; check in the pilot.

**Effort.** 10-12 weeks part-time, tight. 50-150 USD API.

**Fit with the exposé.** Audit tasks: failure localization (main), evidence tracing (secondary), decision review (category naming). Axes: computational cost (tokens per audit), storage (bytes per record), implementation complexity (emitting edges inline touches every prompt-assembly site).

---

## 5. Idea B (rank 3): What compaction keeps and what it kills

**Name.** Compaction Curve.

**Hypothesis in one sentence.** Compacting an agent record so that only the latest value per object survives (Kafka-style), or only a snapshot of the prefix survives (Raft-style), or only an LLM summary of the prefix survives, preserves audits over the final state but destroys audits over the lifecycle, so lifecycle coverage, sequence-policy decidability and localization of transient faults fall with the share of retries and overwrites, while final-state checks stay near 1.0.

**Why it matters.** Every production log-primary system compacts (Temporal's 51,200-event cap, Kafka compaction, LangGraph's per-step snapshot growth), and every checkpoint system that keeps only the latest state (AutoGen, CrewAI) is the endpoint of compaction. Nobody has measured what audit tasks a given compaction operator kills; this turns "log versus checkpoint" into one measured curve.

**What would confirm / refute it.**
- Confirm: under keep-latest at overwrite share rho = 0.3, LPC and sequence-policy decidability drop roughly with rho while final-state SPDR and ACR stay near 1.0; a schema-blind checker returns wrong "comply" verdicts (not "undecidable") at a measurable rate; a fixed judge loses transient-fault localization by a large margin while terminal-fault localization changes little, relative to the uncompacted baseline.
- Refute: LPC and sequence-policy SPDR stay high (retries create new keys, nothing is lost); or transient and terminal faults degrade equally; or the structured fold (Parsing the Stream style) keeps audits intact, meaning the claim holds only for lossy operators.

**The experiment, step by step (scoped-down, with validity fixes).**
1. Simulator (weeks 1-2): a 300-line Python generator emitting a JSON-lines event log for one scripted workflow (plan, tool calls, scratch-memory writes, approval, execute) with knobs for length n (50, 100), overwrite share rho (0, 0.1, 0.3, 0.5) and seed. No LLM in the loop. Inject lifecycle events through the tool wrapper (timeouts that trigger the retry path, forced fallbacks, real scratch-key writes), never by editing text. Optionally run one real LangGraph agent once to copy the exact shape of its checkpoint record.
2. Record variants (week 3), four not six: full log (reference); keep-latest-per-key (Kafka); prefix snapshot at n/2 plus suffix log (this IS the checkpoint case, so do not list it twice); latest-state-only (AutoGen/CrewAI). Optional fifth: LLM prefix summary at rho = 0.3 only, one fixed model and prompt, forced JSON output schema.
3. Pre-register the key schema per operator, taken from real frameworks (AutoGen save_state, CrewAI @persist row, LangGraph channel values). State the analytic expectation up front: LPC under keep-latest tracks 1 - rho almost mechanically. Put the empirical weight elsewhere.
4. Policies (weeks 4-5): 5 final-state and 5 sequence policies with known verdicts on the full log. Run TWO checkers: schema-aware (knows what was compacted, returns undecidable) and schema-blind (returns whatever the record shows). Report comply / violate / undecidable / wrong-verdict. The blind checker's false-comply rate is the interesting number.
5. Faults with known positions: transient (wrong tool result at step j, corrected at j+2, side effect already fired) and terminal (propagates to the end), 5 positions per base run. Adopt TrajDebug's resolved vs terminal-footprint definitions.
6. Judge (week 6): one fixed LLM judge, 3 repeats, on cached records; measure the uncompacted-log baseline first, and if it is below about 60% simplify the workflow. Control record length by evaluating every record at the same token budget (drop random non-fault events from the full log to match compacted size). Add a position-only baseline and a shuffled-label control.
7. Metrics: LPC, SPDR split by class with four-way verdicts, transient vs terminal localization accuracy, storage reduction, ACR under both definitions of "policy-relevant" (superseded attempts included and excluded). Drop GB, RF.
8. Runs: 2 lengths x 4 rho x 10 seeds = 80 base runs x 4-5 variants = 320-400 records; about 1,000 judge calls at 10k tokens each, 20-40 USD.
9. Weeks 7-8 sweep and analysis (regress each metric on rho with slopes and CIs, not a single threshold); 9-10 writing; 11-12 buffer.

**Closest prior work and what is new.**
- TraceElephant (ACL 2026), https://arxiv.org/abs/2604.22708 — record completeness vs attribution; outputs-only, not compaction operators.
- LogDx-CI (2026), https://arxiv.org/abs/2605.28876 — benchmarks log-reduction operators by downstream LLM diagnosis on CI logs; same design shape, different domain.
- Parsing the Stream (2026), https://arxiv.org/abs/2609.01466 — a typed fold raised monitor accuracy (0.85 vs 0.48); shows structured folding can help, so scope the claim to lossy operators.
- Beyond Compaction (2026), https://arxiv.org/abs/2606.11213 — says summarization destroys causal structure; measures only task accuracy.
- Kafka log compaction, https://docs.confluent.io/kafka/design/log_compaction.html and Raft Section 7, https://raft.github.io/raft.pdf — qualitative loss statements.
- Auditable Agents, https://arxiv.org/abs/2604.05485 — LPC/SPDR; never computed under compaction; its own caveat (cannot distinguish "did not occur" from "not recorded") is the schema-blind checker finding.
- ActiveGraph compaction phase 1 (v1.5, July 2026), https://github.com/yoheinakajima/activegraph/blob/main/compaction-design.md — mechanism exists, unmeasured; do not claim ActiveGraph has no compaction.
- New: first measurement of which audit tasks survive which compaction operator, with the wrong-verdict rate of a schema-blind checker and the transient/terminal split.

**Main risk and mitigation.** The Kafka half is near-tautological. Mitigation: state the analytic expectation, measure what is not fixed by construction (real framework key schemas, blind-checker false verdicts, judge asymmetry), and control record length. Second risk: overlap with idea C (both claim first compaction measurement). Mitigation: C is about cost and fidelity of rebuild; B is about which audit questions survive; cite each other and pick one.

**Effort.** 10-12 weeks part-time. Under 50 USD.

**Fit with the exposé.** Audit tasks: execution reconstruction (lifecycle phases), policy compliance (final-state vs sequence), failure localization (transient vs terminal). Axes: storage (main), computational cost (replay), implementation complexity (what a snapshot must contain).

---

## 6. Idea E (rank 4): Can the provenance graph be rebuilt from the log?

**Name.** Overlay as a View.

**Hypothesis in one sentence.** A claim-to-evidence graph rebuilt after the run from the event log matches one captured during the run when the log stores full model input and output and evidence entered through its own tool call, and falls apart as the log is thinned (prompts stripped, payloads hashed, final state only) or as more sources are combined inside one model call, so the overlay is a derived view of a complete log and a separate architecture only for an incomplete one.

**Why it matters.** Rasheed et al. assert that post-hoc verification cannot recover reasoning chains and measure nothing; the "From Agent Traces to Trust" survey lists inline vs post-hoc as an open axis. If the graph is a view, the overlay family costs nothing at run time and the real question becomes what the log must retain; if not, the overlay earns its run-time cost.

**What would confirm / refute it.**
- Confirm: post-hoc edge recall against planted-fact ground truth is near the inline overlay for the full log and tool-mediated mode, and the recall curve drops monotonically with log thinning and with documents combined per call; the deterministic parser recovers observed and declared edges at zero model calls and the LLM extractor only adds inferred ones.
- Refute: recall is uniformly high across thinning levels (the log's intermediate content adds nothing); or uniformly low even for the full log (the log lacks what the overlay has, supporting Rasheed et al.).
- Pre-register the paired difference with a cluster bootstrap over questions; do not use 80%/50% absolute thresholds.

**The experiment, step by step (scoped-down, with validity fixes).**
1. Corpus and agent (weeks 1-2): 20-30 ALCE-ASQA questions with their shipped top-5 passages as the corpus. Plant facts: build the corpus so that a set of atomic facts appears in exactly one document, and some deliberately in two, so any claim stating a planted fact has a known true source set. A LangGraph research-QA agent writes a 5-10 sentence cited answer at temperature 0 with all I/O cached.
2. Two writing modes (the mechanism factor): tool-mediated (every fact must be fetched with a quote(doc, span) tool before use, with batched fetches so temporal adjacency does not give the answer away) and synthesis (3 vs 8 documents in one call).
3. Three records of the same run (week 3): (A) log-primary JSONL with full prompts, responses, tool payloads; (B) inline overlay: a hook records, at each generation call, which passages were in context and which were cited (observed and declared edges); (C) final state only: answer plus retrieved-doc ids.
4. Log completeness as the manipulated variable (the key reframe): run the post-hoc extractor over (i) full log, (ii) prompts stripped, (iii) tool payloads replaced by hashes, (iv) final state only.
5. Two post-hoc reconstructors: a deterministic parser (claim to generation event to prompt passages) and an LLM extractor from a different model family than the agent. Scrub citation markers from the report before the post-hoc model sees it; treat the final-state-only arm as the leakage floor.
6. Ground truth and judge (weeks 4-5): planted-fact edges as primary; 150 claims hand-labelled blind to record and edge type, 50 double-labelled by a classmate (kappa); a local NLI judge (DeBERTa) calibrated on 300-500 AttributionBench items with accuracy reported. Fix the claim set as the numbered sentences of the answer so no claim matching is needed.
7. Metrics: edge recall and precision at document and span level (pre-registered match rule), PCov defined as a path to a human-judged supporting source, PSnd, extractor tokens and seconds as a fraction of generation cost, bytes per run per record. Drop AEff path length (constant here).
8. Runs: 20-30 questions x 2 modes x 2-3 dose levels; 600-900 extraction calls; tens of dollars.
9. Weeks 6-7 analysis; 8-9 writing; 10-12 buffer.

**Closest prior work and what is new.**
- Generation-Time vs Post-hoc Citation (Saxena et al. 2025), https://openreview.net/forum?id=iQyfHmqRJR — G-Cite vs P-Cite at answer level; no agent log.
- ALCE (Gao et al. 2023), https://arxiv.org/abs/2305.14627 — PostCite baseline (26.7 vs 72.5 citation precision on ASQA).
- The Extractive-Abstractive Spectrum (Worledge et al. 2024), https://arxiv.org/abs/2411.17375 — quote-vs-synthesis verifiability drop.
- ContextCite (2024), https://arxiv.org/abs/2409.00729 — ablation-based "used" edges; the right definition of an observed edge.
- GRADE (2026), https://arxiv.org/abs/2606.22741 — observed/declared/inferred vocabulary; no recall measured.
- From Fluent to Verifiable (2026), https://arxiv.org/abs/2602.13855 — the claim under test.
- Provenance from log files (Ghoshal and Plale 2013), https://doi.org/10.1145/2457317.2457366 — the idea is old; this is the LLM-agent instance.
- New: same-run inline vs post-hoc on an agent event log, log completeness as a dose-response, planted-fact ground truth, parser vs LLM decomposition.

**Main risk and mitigation.** With a full log and claim-by-claim writing, the inline edges are a deterministic function of the log, so "no gap" is guaranteed. Mitigation: that is now the null of the dose-response, not the headline; the finding is where the curve breaks. Second risk: the synthesis arm collapses to standard attribution evaluation (AttributionBench, about 80% for LLM judges). Mitigation: score set-level recovery for multi-source claims and report the parser baseline.

**Effort.** 10-12 weeks part-time. Under 100 USD. About 15-20 hours of labelling.

**Fit with the exposé.** Audit tasks: evidence tracing (main), decision review (which source drove which claim). Axes: storage (bytes per record, what the log must retain), computational cost (run-time hook vs audit-time extraction), implementation complexity, privacy (hashed-payload level).

---

## 7. Idea C (rank 5): Storage versus exact rebuild — the snapshot-interval dial

**Name.** Snapshot Interval Dial.

**Hypothesis in one sentence.** For the same run, the append-only log with a cached response store is the cheapest record that rebuilds the state at any step exactly; per-step full-state checkpoints cost several times more because each snapshot repeats the history; checkpoints every n > 1 steps save storage only by re-executing model calls in between, which costs money and may return a different state; and a span overlay either stores as much as the checkpoints (full prompt per span) or cannot rebuild state at all (hashed payloads).

**Why it matters.** Storage and computational cost are two of the exposé's four axes and this is the only idea that measures both with no LLM judge at all. The headline growth curves are partly published already, but the rebuild-fidelity and interval-sweep half is not, and it directly prices the counterfactual-analysis task (you must rebuild step k before you can fork it).

**What would confirm / refute it.**
- Confirm: marginal bytes per step grow linearly with k for SqliteSaver (so the store is quadratic), are flat for the log, DeltaChannel and Postgres blob-dedup; log fold is byte-identical at every k; re-execution from the nearest checkpoint diverges with a per-call probability p estimated with CIs, and P(exact) falls as (1-p)^gap; the faithful OpenInference span tree is quadratic because llm.input_messages carries the full prompt.
- Refute: SqliteSaver storage within 1.5x of the log (it de-duplicates); re-execution reproduces the original almost always on the chosen serving stack (then interval n > 1 loses nothing there); or fold time is so small at all tested lengths that no compute trade-off exists (already reported by OpenHands SDK for logs; treat as expected).
- Note: predictions 1 and the hashed-overlay case are true by arithmetic. Say so. The empirical content is the constants, the divergence model, and the cost curves.

**The experiment, step by step (scoped-down, with validity fixes).**
1. Workflow (week 1): one LangGraph ReAct agent with fixture-based deterministic tools, a step counter in state, a config-driven stop-at-k edge. Cap tool outputs at about 400 tokens. Three seeds x 200 steps; sizes at every smaller n come for free by measuring after every superstep. Add a second workflow variant with trimmed context (last W messages) to show where the quadratic result stops.
2. Recorders attached to the same run (week 2): (L) callback JSONL log writing only new messages plus prompt hash and response hash, with a custom hash-keyed BaseCache (not LangChain's SQLiteCache, which keys on full prompt text); (C) SqliteSaver, durability='sync'; also LangGraph DeltaChannel and, if convenient, PostgresSaver (per-channel blob dedup); (O) OpenInference spans to a 30-line SQLite exporter, once with full payloads and once with hashed payloads.
3. Measure logical size, not file size: sum of blob lengths per table; break down by column (checkpoint blob is the quadratic part; metadata and writes are linear, which is the mechanism). Report raw, gzip per record, whole-file zstd --long, and a content-addressed dedup variant, so the "just gzip it" objection is answered with data.
4. Interval sweep (week 3): derive C_n storage for n in {1, 2, 4, 8, 16} by filtering the n = 1 database. Re-execute live only for n in {4, 16} at k = 25/50/75/100%, via time-travel from the nearest kept checkpoint on a copied database, 2 repeats each. Rebuild from the log by re-invoking with the cache; define "byte-identical" on a canonical projection (ordered messages, tool outputs, scratch-file hashes) that drops ids, timestamps and response metadata.
5. Divergence model: estimate the per-call divergence probability p with 95% CIs on two serving stacks (a hosted API and a local greedy-decoded model), pin the model snapshot, rebuild within hours of the base run. State plainly that this is a property of the stack, not the family.
6. Cost model (one paragraph, not a criterion): with per-checkpoint bytes a(k) and per-step re-execution cost b, cost(n) = sum of a/n + b(n-1)/2; show the measured curve for two explicit exchange rates (USD per GB-month vs USD per rebuild) as a sensitivity plot; cite Toueg and Babaoglu (variable-cost checkpoints) rather than Young/Daly, since checkpoint cost grows with k.
7. Metrics: bytes per run and per step (raw, gzip, zstd, dedup), fitted marginal-cost slope c1 with CI over seeds, exact-match and field-level Jaccard of rebuilt state, ms / model calls / USD per rebuild, a fixed lineage-query set with ground-truth answers for the overlay. Drop agrepl F, ACR, the Crab ladder, lines-of-code proxy.
8. Runs: about 3 x 200-step base runs plus a few hundred re-execution calls; 10-60 USD.
9. Weeks 4-5 analysis; 6-7 writing. Leaves 4-5 weeks of slack, which is why this is the safest fallback; you could add idea B on the same recordings.

**Closest prior work and what is new.**
- The Hidden Footprint / AgentFootprint (2026), https://arxiv.org/abs/2607.11149 — growth exponents for eight frameworks (LangGraph 1.74, windowed 0.98-1.20), fixed-trace control, content-addressed compaction. Reuse its metrics; do not claim first storage curves.
- LangGraph DeltaChannel PR #7586 and issue #7843, https://github.com/langchain-ai/langgraph/pull/7586 and https://github.com/langchain-ai/langgraph/issues/7843 — O(N^2) vs O(N) benchmark by the maintainers; SqliteSaver stores full snapshots inline while Postgres de-duplicates.
- OpenHands SDK (MLSys 2026), https://arxiv.org/abs/2511.03690 — log-primary persistence grows linearly; replay 4.1 ms median.
- Reasoning Provenance for Autonomous AI Agents (2026), https://arxiv.org/abs/2603.21692 — stylized 560 KB vs 25-130 KB; plans the same measurement (concurrent-work risk).
- The Replay Gap (COLM 2026 workshop), https://arxiv.org/abs/2608.08239 and Causal Agent Replay, https://arxiv.org/abs/2606.08275 — re-execution fidelity metrics.
- Non-Determinism of "Deterministic" LLM Settings, https://arxiv.org/abs/2408.04667 — divergence-rate baseline at temperature 0.
- New: the interval sweep with rebuild fidelity and cost, the OTel overlay as a third arm (payload vs hash), the DeltaChannel/Postgres crossover, and the divergence model.

**Main risk and mitigation.** Reads as engineering trivia and the headline is pre-empted. Mitigation: make the divergence model and the cost crossover the headline, tie every number to an audit task (which steps k can be rebuilt exactly, at what price, for reconstruction and counterfactuals), and cite Hidden Footprint as the baseline you extend. Second risk: serving-stack nondeterminism swamps the interval effect. Mitigation: two stacks, pinned snapshot, control rebuilds.

**Effort.** 6-8 weeks part-time; 10-60 USD. Lowest execution risk of the six.

**Fit with the exposé.** Audit tasks: execution reconstruction (main), counterfactual analysis (cost of rewinding to k), evidence tracing (lineage queries on the overlay). Axes: storage (main), computational cost (main), implementation complexity (recorder integration points).

---

## 8. Idea F (rank 6): When is a cheap fork honest? Fork validity versus recovery boundary

**Name.** Fork Validity x Recovery Boundary.

**Hypothesis in one sentence.** For one injected fault at step k with a known repair, a fork that restores the prefix from a cached log and a fork that restores a checkpoint reach the same repair verdict when tools are stateless, but once earlier steps wrote to external state that later steps read, both fail unless that state is restored (by a snapshot or by replaying recorded write events), and the gap grows with the number of read-after-write dependencies before k.

**Why it matters.** Counterfactual analysis is the audit task the log-primary and checkpoint families both claim to own ("cheap and honest forks", "time travel"), and the exposé asks what they trade. No paper compares the two fork mechanisms on identical faults with tool statefulness as the moderator, and ActiveGraph's own "honest fork" claim has never been measured.

**What would confirm / refute it.**
- Confirm: in the stateless condition, the two forks agree within a pre-registered equivalence margin (TOST, 10 points) after accounting for the same-decision noise floor; in the stateful condition, flip rate for cache-only and state-only forks falls with read-after-write dependencies while environment-restoring forks stay flat; seconds per fork and bytes per run differ by cell (model calls do not, because neither fork re-fires the prefix).
- Refute: state-only forks match environment-restoring forks under external state (graph state is enough); or log forks that replay write events also fail (replaying a recorded write response does not recreate the written object, as SymTrace warns); or the noise floor exceeds every substrate difference.

**The experiment, step by step (scoped-down, with validity fixes).**
1. Workflow (weeks 1-2): one LangGraph "research memo" agent (plan, search a frozen 40-document corpus with planted facts, extract, write notes to a scratch SQLite file, write a cited memo), 15-20 steps. Programmatic checker: pass = all required (fact, source) pairs present. Gate: keep only tasks with at least 80% clean success. 15 tasks.
2. The key reframe, a 2x2 on ONE harness: axis A = how the prefix at k is restored (checkpoint state restore vs replay through a hash-keyed response cache); axis B = external state at k (not restored / snapshot copy / rebuilt by re-applying logged write events). Build one interception layer with these toggles. Use ActiveGraph and LangGraph only as a 10-fault cross-check that the harness reproduces their forks' verdicts.
3. Scope the cache: a fork may only be served from events <= k of the faulty run being audited; log every cache hit after k as a validity violation; add a canary post-k prompt that must be a live call.
4. Fork-time state, two realistic conditions: stale (file left at end of the faulty run; maps to Safe-to-Resume SF3) and missing (fresh process, empty file; SF5). Hold k fixed and vary write density so the number of writes is not confounded with fork position.
5. Ground truth (week 3): warm-start injection, 3 fault types with mechanical repairs (wrong tool argument, corrupted tool output, dropped note write); 15 tasks x 3 faults = 45 faults; over-generate since mini models absorb many corruptions. Two repair types per fault: the original action, and a different correct action (so success is "outcome correct", not "equals original").
6. Forks (weeks 4-6): per fault and cell, 2 repair forks plus 1 same-decision control fork, temperature 0, a locally served open-weight model with greedy decoding to shrink the noise floor. About 1,600 forks x 12 calls; 30-100 USD.
7. Metrics: flip rate (repair minus resample against the control), first-divergent-action index and edit distance (Replay Gap), seconds per fork, bytes per run per cell, automatic SF3/SF5 counts via a content hash of the scratch file at every read step. Mixed-effects logistic model with task and fault random intercepts and a cell x dependency-count interaction; Wilson intervals per level.
8. Weeks 7-8 runs; 9-10 analysis and writing; 11-12 buffer. Fallback if write-replay slips: compare only state-restore cells, which still tests "graph state alone is not enough".

**Closest prior work and what is new.**
- Crab (2026), https://arxiv.org/abs/2604.28138 — chat-only 6-13% vs chat+FS vs full 100% recovery; crash recovery, not counterfactual verdicts.
- Safe to Resume? (2026), https://arxiv.org/abs/2608.29381 — SF1-SF5 failure modes measured across LangGraph, CrewAI, Hermes, Cline, E2B.
- Shepherd (2026), https://arxiv.org/abs/2605.10913 — byte-exact prefix, suffix-only counterfactual replay, fork latency vs docker commit.
- Repair or Resample? / SymTrace (2026), https://arxiv.org/abs/2608.25920 — cached-prefix reconstruction; states that replaying a stored write response does not recreate the object.
- The Replay Gap (2026), https://arxiv.org/abs/2608.08239 — same-model control forks; 6-35% first-action divergence with no change.
- AgentCheck (2026), https://arxiv.org/abs/2607.11098 — cache-then-live fork template.
- ACRFence (2026), https://arxiv.org/abs/2603.20625 and langchain-replay, https://github.com/sixty-north/langchain-replay — show cached prefix is a knob available to the checkpoint family too.
- New: paired per-fault crossing of restore mechanism with environment handling as verdict agreement, the write-event-replay log arm, the read-after-write dose-response, and the noise-floor accounting.

**Main risk and mitigation.** The direction of the stateful result is by construction (you decide that later steps read a file the plain fork does not restore). Mitigation: reframe as magnitude and shape (dose-response), add the null-result branch ("the LLM is robust to stale notes"), and predict L = C+E (if the log beats the environment snapshot, suspect a cache leak). Second risk: most engineering of the six. Mitigation: one harness with toggles, not two frameworks.

**Effort.** 10-12 weeks part-time, little margin; 30-100 USD.

**Fit with the exposé.** Audit tasks: counterfactual analysis (main), failure localization (intervention-verified), execution reconstruction (prefix fidelity). Axes: computational cost (seconds per fork), storage (environment snapshots vs write-event log), implementation complexity (fork isolation).

---

## 9. Recommended pick and why

**Recommended default: Idea A, Redaction x Architecture.**
- All three source reviews rated its novelty strong, and the gap is confirmed by the papers themselves: Nian et al. say privacy mechanisms are unvalidated; the IETF draft mandates hash-only storage with no evaluation; DEMM-Bench has no redaction and no checkpoint regime.
- It needs no LLM judge, no human labels, no live model calls beyond fixtures. Every number is deterministic and reproducible, which is the right first research project for an engineer.
- It covers three audit tasks and all four trade-off axes, with privacy as the headline, and privacy is the axis the other five ideas barely touch.
- Its main weakness (results partly by construction) has a cheap, well-understood fix: pre-register the field map and policies, use as-shipped implementations, prove SPDR = 1.0 at raw, and lead with the non-obvious rows (NER false positives on structural strings, salted vs unsalted hashes, side channels, typed vs blob checkpoints, EncryptedSerializer). The NER false-positive measurement also gives the paper its NLP content.
- Budget: under 50 USD and 10-12 weeks part-time with a buffer.

**Safer fallback: Idea C, Snapshot Interval Dial.**
- Two reviewers rated feasibility strong; one reproduced the core measurement in fifteen minutes. It can run with zero LLM cost using a scripted model.
- Its execution risk is the lowest of the six: every metric is a byte count, a hash comparison or a timing.
- Its cost is weaker novelty (The Hidden Footprint and LangGraph's own DeltaChannel benchmark already show the quadratic-vs-linear headline). Fix that by extending their work explicitly: the interval sweep, the divergence model on two serving stacks, the OTel span-tree arm, and the DeltaChannel/Postgres crossover.
- It finishes in 6-8 weeks, which leaves room to add idea B (compaction) on the same recordings if things go well. That pairing would be a strong paper.

If you prefer the most "NLP" project and can afford 100-150 USD and a heavier analysis, idea D (Format x Fault Type) is the alternative default; but do not start it without fixing the run counts and the information-equivalent arm first.

---

## 10. Papers you should add to your folder

Only verified papers from the reviews and the literature list. None of these are in your folder yet.

1. **Seeing the Whole Elephant (TraceElephant)** — Chen et al., ACL 2026. https://arxiv.org/abs/2604.22708 — The closest existing experiment to your exposé: same runs audited under progressively richer records (16% to 28% to 33% step accuracy). Every idea above must position against it.
2. **DEMM-Bench** — Solozobov 2026. https://arxiv.org/abs/2606.20634 — Scores evidence sufficiency across eight record regimes under controlled degradation; the methodological precedent for ideas A and B.
3. **Which Agent Causes Task Failures and When? (Who&When)** — Zhang et al., ICML 2025. https://arxiv.org/abs/2505.00212 — Canonical failure-localization benchmark and metrics; step accuracy only 14% from flat logs.
4. **Who&When Pro** — Liu et al. 2026. https://arxiv.org/abs/2607.09996 — The warm-start injection recipe (replay prefix, plant one fault) used for ground truth in ideas B, D and F; also the length-degradation confound.
5. **Crab: Semantics-Aware Checkpoint/Restore** — Wu et al. 2026. https://arxiv.org/abs/2604.28138 — Fills the missing checkpoint family: chat-only snapshots recover correctly 6-13% of the time vs 100% with filesystem state.
6. **Safe to Resume?** — Wu et al. 2026. https://arxiv.org/abs/2608.29381 — Formal model and five failure modes of checkpoint/rollback across 12 frameworks; your checkpoint-family reference.
7. **The Hidden Footprint (AgentFootprint)** — Yu et al. 2026. https://arxiv.org/abs/2607.11149 — Measured storage growth for eight frameworks; the baseline idea C extends and the number idea A controls for.
8. **The Replay Gap** — Gonuguntla, COLM 2026 workshop. https://arxiv.org/abs/2608.08239 — Same-model control forks and divergence metrics; the noise floor every replay experiment needs.
9. **PROV-AGENT** — Souza et al., IEEE e-Science 2025. https://arxiv.org/abs/2508.02866 — The canonical inline provenance-overlay system (W3C PROV plus MCP, open source Flowcept); your overlay representative.
10. **From Agent Traces to Trust (survey)** — Wang et al. 2026. https://arxiv.org/abs/2606.04990 — The vocabulary source: granularity, timing (inline vs post-hoc), representation forms that map onto your three families.
11. **RedAct** — Xu, He, Fung 2026. https://arxiv.org/abs/2606.10813 — The only quantitative redaction-vs-audit-evidence study; the template for idea A's privacy axis.
12. **Agent Audit Trail (IETF Internet-Draft, draft-sharif-agent-audit-trail-03)** — Sharif 2026. https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/ — Mandates hash-only content for agent audit records with no evaluation; the standard idea A tests.

Also worth reading if time permits: TelemetrySuffBench (https://arxiv.org/abs/2608.07899), Adaptive Influence Graphs (https://arxiv.org/abs/2608.24361), Repair or Resample? / SymTrace (https://arxiv.org/abs/2608.25920), LangGraph checkpointer docs (https://docs.langchain.com/oss/python/langgraph/checkpointers), and the awesome-auditable-ai list (https://github.com/yzhao062/awesome-auditable-ai) for anything newer.

Two citation cautions from the reviews: "Safe Observability: A Framework for Automated PII Redaction..." (Melnyk 2025) and "Verifiable redactable audit log" (Palantir patent) could not be located by two reviewers; verify them yourself before citing. "An Analytical Survey of Provenance Sanitization" is by Cheney and Perera (2014), not the ProvAbs authors.

---

## 11. Warning about one of your papers: "Verifiability-First Agents" (Gupta)

The paper exists (arXiv, dblp, OpenReview; apparently a poster at the AAAI 2026 TrustAgent workshop, one arXiv version, no citing papers found). Its reference list does not hold up.

- Of 18 references, only 4 are fully correct (Amodei 2016; Gabriel 2020; Park 2023 Generative Agents; Yao 2023 ReAct, with a wrong third author).
- 4 are real works with wrong metadata: Bostrom and Yudkowsky (2014, not 2017); Christiano et al. 2018 (extra authors conflated with Leike et al.); Perez et al. 2023 (Findings of ACL, not NeurIPS); AgentBench (wrong authors, year and arXiv id, and mis-described as a misalignment benchmark).
- 10 could not be found at all. Three arXiv ids resolve to unrelated math or physics papers (2308.00669, 2311.02459, 2403.08975). Three cited workshops do not exist on the official ICML 2024, ICLR 2024 or STAI lists. One in-text citation (Zheng et al. 2023) has no reference entry.
- The pattern matters: every reference that supports the paper's own contributions (VeriLLM attestation, challenge-response verification, zero-knowledge attestations, proof-of-action protocols, provable oversight, traceable intent specifications, multi-layer governance, a verifiable-agents survey) is unverifiable, while every verifiable reference is a generic well-known paper. The text also contradicts its own Table 1 (attribution confidence 0.74 vs 0.62 baseline, "12.4%" vs a 45% latency cut, FPR "<7%" vs 0.09) and gives no dataset, task or code.

What to do:
- Do not cite it for any empirical result, and do not use it as the representative of any of the three architecture families.
- At most, mention it once as an example of the "signed receipts plus runtime audit agent" design pattern, explicitly flagged as unvalidated. Better substitutes for that pattern exist: Agent Flight Recorder (https://arxiv.org/abs/2609.01931), AEGIS pre-execution firewall (https://arxiv.org/abs/2603.12621), AuditWeave (https://arxiv.org/abs/2607.09682).
- Real, checkable alternatives that surfaced during verification for the topics it cites badly: JustAct+ (arXiv 2502.00138) and CHAP (arXiv 2606.09751) for auditable multi-agent protocols; Organizational Control Layer (arXiv 2606.04306) for governance; VeriSpecGen (arXiv 2604.10392) for intent specifications; the awesome-auditable-ai list in place of the non-existent survey.
- One useful lesson: the paper's metrics (time-to-detect, remediation latency, attribution confidence) could be re-implemented honestly inside your own evaluation, since none of the verifiable sources measures them on a shared workflow across the three families.
