# Research directions for the term paper (short version)

Written 2026-09-07. Simple English on purpose. Details are in the other files in this folder.

## 1. The short answer

**Recommended hypothesis (my pick): "Record Format x Fault Type"**

> When the same faulty agent run is shown to the same LLM auditor in three forms (an event log, a series of state snapshots shown as diffs, and a provenance graph with dependency edges), the form that finds the fault best depends on the kind of fault. The log wins on tool faults, the snapshot diffs win on state-corruption faults, and the graph wins on wrong-source faults.

Why this one:
- It is the exposé's own headline task (failure localization) on the exposé's own three families. No drift.
- It has real NLP content: an LLM auditor, judged with the same metrics as the Who&When and TRAIL benchmarks.
- Novelty was rated strong by the reviewer. Every existing benchmark uses one log-shaped record. Nobody has held the run fixed and changed the record type.
- Ground truth is free. You replay a good run to step k, plant one fault, and let it continue. The faulty step is then known. This is the Who&When Pro recipe.
- The same harness ("one run, three recorders") gives you the storage and rebuild-cost numbers of Idea C almost for free as a second results section. That covers execution reconstruction and the storage and compute axes without any extra LLM cost.

Cost: 50 to 150 USD in API calls with a small model. Time: 10 to 12 weeks part-time, tight but doable.

**Safer fallback: "Snapshot Interval Dial" (Idea C)**. All numbers are byte counts, hash comparisons and timings. Zero LLM cost is possible. Lowest risk. Weaker novelty, because a 2026 paper (The Hidden Footprint) already published the "checkpoints grow quadratically, logs grow linearly" headline. You would extend it, not discover it.

**Cheapest strong-novelty option: "Redaction x Architecture" (Idea A)**. The automated synthesis ranked this first. I rank it third. Reason: privacy is one of four trade-off axes in your exposé, not the main question, and the experiment can run with no language model at all. A professor in an NLP course may ask "where is the NLP?" If your supervisor is happy with privacy as the headline, this is a very clean project.

## 2. The six candidate hypotheses

Twenty candidates were generated from five different angles and reviewed for novelty, feasibility and validity. They collapsed into six distinct ideas.

| # | Name | Hypothesis in one line | Main audit task | Cost | Novelty | Risk for a first project |
|---|---|---|---|---|---|---|
| D | Record Format x Fault Type | Which record form helps an LLM auditor find which kind of fault | Failure localization | 50-150 USD | strong | medium (judge noise, needs 40-50 tasks) |
| C | Snapshot Interval Dial | Log with cached responses rebuilds any step exactly and cheaply; checkpoints trade storage for re-execution that may not reproduce | Execution reconstruction, counterfactual cost | 10-60 USD | weak (partly published) | lowest |
| A | Redaction x Architecture | Same privacy masking makes different policies unanswerable in a log, a checkpoint and a graph; the blob-style checkpoint loses most | Policy compliance | under 50 USD | strong | low, but "by construction" danger |
| B | Compaction Curve | Compacting a record keeps final-state audits but kills lifecycle audits, in proportion to retries and overwrites | Execution reconstruction, policy compliance | under 50 USD | strong | low, but half the result is obvious |
| E | Overlay as a View | A claim-to-evidence graph can be rebuilt from a complete log, and breaks as the log is thinned or as more sources are mixed in one model call | Evidence tracing | under 100 USD, 15-20 h labelling | acceptable | medium-high (human labels) |
| F | Fork Validity | Cached-log forks and checkpoint forks agree when tools are stateless, and both fail when earlier steps wrote external state that is not restored | Counterfactual analysis | 30-100 USD | acceptable | highest (most engineering) |

Coverage of the exposé (main = headline, sec = secondary):

| Idea | Failure localization | Evidence tracing | Execution reconstruction | Counterfactual | Policy compliance | Decision review | Storage | Complexity | Privacy | Compute |
|---|---|---|---|---|---|---|---|---|---|---|
| D | main | sec | | | | sec | sec | sec | | main |
| C | | sec | main | sec | | | main | sec | | main |
| A | | sec | sec | | main | | sec | sec | main | sec |
| B | sec | | main | | sec | | main | sec | | sec |
| E | | main | sec | | | sec | sec | sec | sec | sec |
| F | sec | | sec | main | | | sec | sec | | main |

No single idea covers three of the four tasks named in your exposé's evaluation paragraph. That is normal for a term paper. Pick one headline task and report the others as smaller sections. D plus the cheap parts of C is the pairing that covers the most.

## 3. What the experiment looks like (for D, step by step)

1. **One small agent.** A LangGraph agent that answers multi-hop questions over a fixed set of passages (HotpotQA or MuSiQue), with offline lookup tools. About 20 steps per run. Later a 40-step variant.
2. **Three recorders on the same run.** (a) An event log written from a callback (log-primary). (b) LangGraph's SqliteSaver checkpoints, rendered as step-by-step state diffs (checkpoint-based). (c) A W3C PROV graph built with the `prov` library, with "used" and "derived from" edges (provenance overlay). Check that tool inputs and outputs are byte-identical across the three.
3. **The key control.** Also derive all three forms losslessly from one canonical event stream. This separates "the record has more information" from "the record is shaped differently". Reviewers insisted on this.
4. **Ground truth by injection.** Replay a clean run to a random step k, plant one fault through the tool wrapper (never by editing text), and continue. Six fault types in three classes: tool (wrong argument, corrupted output), state (dropped note, overwritten note), evidence (claim cited to wrong source, claim with no source). About 40-50 tasks x 6 faults = 240-300 faulty runs, plus clean controls.
5. **The auditor.** One cheap fixed model, temperature 0, fixed prompt. It must name the faulty step, the fault category, and point to the record item. Same step numbering in all three forms.
6. **Metrics.** Step exact match and plus-or-minus 3 steps (Who&When, LongRCA), category F1 (TRAIL), tokens per audit, bytes per record. Two artifact controls: a position-only guesser and a shuffled-label run. If the guesser scores well, the injection is leaking.
7. **Analysis.** A paired design with a mixed-effects logistic model (run as random effect). One primary test: the format x fault-class interaction.
8. **Free extras from the same harness.** Bytes per step for each recorder, milliseconds to rebuild step k from the log vs from the nearest checkpoint, and whether the rebuilt state is identical. This is the cheap half of Idea C.
9. **Pilot first.** Ten runs x three forms in week 3. Look at the renderings side by side before scaling up.

Weeks 1-2 workflow, 3 pilot, 4-5 injection and ground truth, 6-7 full run, 8-9 analysis, 10-11 writing, 12 buffer.

## 4. Warnings you should know before choosing

- **Preprints.** Most of the 188 verified papers are 2026 arXiv preprints, not peer-reviewed. One paper cited by others (GraphTracer) was withdrawn for a methodological error. Hedge novelty claims and add a venue column to your bibliography.
- **The "no real architecture" objection.** If all three records come from one LangGraph run, a critic can say you compared renderings, not architectures. Defense: use as-shipped recorders (LangGraph's own checkpointer, a real PROV emitter), and cross-check the log arm against ActiveGraph on a handful of runs. State the limitation openly.
- **By construction.** If you write the policies, the schemas and the checker yourself, the result can be true by design. For A or B, use externally written policies: the tau-bench airline and retail policy documents, AgentDojo, or AgentSpec's 43 rules. For D, the injection recipe and the artifact controls are the defense.
- **Concurrent work.** For Idea C, Vispute and Kadam (arXiv 2603.21692) plan a similar storage measurement. For Idea E, Janssen (2026) has a pre-registered but unrun protocol comparing logs with log-plus-graph. Check arXiv monthly and the awesome-auditable-ai list.
- **Wording.** The IETF "Agent Audit Trail" document is an individual Internet-Draft, not a standard. Do not call it a mandate.
- **Single agent.** All six ideas use one agent. Responsibility attribution across agents is out of scope. Say so in the paper.
- **Model nondeterminism.** Even at temperature 0, hosted models drift between calls. Any replay or rebuild claim needs a same-decision control and, ideally, a locally served model with deterministic inference (vLLM batch-invariant mode or SGLang deterministic mode).

## 5. One of your four papers should not be trusted

"Verifiability-First Agents" (Gupta, IIT Roorkee): of its 18 references, 4 are correct, 4 have wrong metadata, and 10 could not be found at all. Three arXiv IDs point to unrelated physics or maths papers. Three cited workshops do not exist on the official ICML 2024, ICLR 2024 and STAI lists. The text contradicts its own results table. Do not cite it for any result. If you want an example of "signed receipts plus a runtime audit agent", cite Agent Flight Recorder (arXiv 2609.01931), AEGIS (arXiv 2603.12621) or AuditWeave (arXiv 2607.09682) instead.

## 6. Papers to add to your folder

Verified to exist. I did not download them, so you can decide.

1. Seeing the Whole Elephant (TraceElephant), ACL 2026. https://arxiv.org/abs/2604.22708. Closest existing experiment: same runs, richer records, step accuracy 16 to 33 percent.
2. Which Agent Causes Task Failures and When? (Who&When), ICML 2025. https://arxiv.org/abs/2505.00212. The failure-localization benchmark and metrics.
3. Who&When Pro, 2026. https://arxiv.org/abs/2607.09996. The warm-start injection recipe for ground truth.
4. TRAIL: Trace Reasoning and Agentic Issue Localization, 2025. https://arxiv.org/abs/2505.08638. Category taxonomy and joint accuracy metric.
5. Crab: Semantics-Aware Checkpoint/Restore, 2026. https://arxiv.org/abs/2604.28138. Checkpoint family: chat-only snapshots recover correctly only 6-13 percent of the time.
6. Safe to Resume?, 2026. https://arxiv.org/abs/2608.29381. Five failure modes of checkpoint rollback across 12 frameworks.
7. The Hidden Footprint (AgentFootprint), 2026. https://arxiv.org/abs/2607.11149. Measured storage growth for eight frameworks.
8. The Replay Gap, COLM 2026 workshop. https://arxiv.org/abs/2608.08239. Same-model control forks and the divergence noise floor.
9. PROV-AGENT, IEEE e-Science 2025. https://arxiv.org/abs/2508.02866. The canonical provenance-overlay system (open source: Flowcept).
10. From Agent Traces to Trust (survey), 2026. https://arxiv.org/abs/2606.04990. Vocabulary for your three families; lists your comparison as an open problem.
11. Trade-Offs in Automatic Provenance Capture, 2016. https://link.springer.com/chapter/10.1007/978-3-319-40593-3_3. The experimental template: same workload, several capture architectures, measure expressiveness, effort and overhead.
12. A survey of rollback-recovery protocols in message-passing systems, 2002. https://dl.acm.org/doi/10.1145/568522.568525. The classic log-based versus checkpoint-based framing.
13. DEMM-Bench, 2026. https://arxiv.org/abs/2606.20634. Evidence sufficiency across record regimes (for A or B).
14. RedAct, 2026. https://arxiv.org/abs/2606.10813. The only quantitative redaction-versus-audit study (for A).

Also useful: LangGraph checkpointer docs (https://docs.langchain.com/oss/python/langgraph/checkpointers), LangGraph time travel (https://docs.langchain.com/oss/python/langgraph/use-time-travel), and the curated list https://github.com/yzhao062/awesome-auditable-ai.

## 7. How to do research, for an engineer (short)

- **A hypothesis is a bet you can lose.** Write it as one sentence that a specific number could contradict. "Architecture X is more auditable" is not a bet. "The graph beats the log by 10 points on wrong-source faults" is.
- **Decide what counts as confirm and refute before you run anything.** Write it in a dated file (a git tag is enough). This is called pre-registration. It protects you from fooling yourself.
- **Hold everything fixed except one thing.** Same run, same auditor, same prompt, same token budget. Only the record form changes. Every difference you find is then about the record.
- **Add a control that should fail.** A guesser that only knows where faults are usually injected. If it does as well as your auditor, your experiment is leaking.
- **Pilot small.** Ten runs, look at the outputs by hand, fix the rendering, then scale.
- **Report the noise.** Repeat runs, use confidence intervals, and say what a null result would mean. A clean null result is a fine term paper.
- **Position against the closest paper, not the whole field.** For D that is TraceElephant. Say in one paragraph what they did and what you add.
- **Write as you go.** Methods section first, while you build. Results and discussion last.
- **Talk to your supervisor with two or three options, not one.** Ask two questions: is a deterministic, no-LLM study acceptable for this course, and what are the deadline and page limit. The answers decide between D, C and A.

## 8. Files in this folder

- `full-report.md`: the complete synthesized report with all six ideas in detail, the scoped-down experiment for each, and the reviewer fixes.
- `all-20-candidates.md`: every candidate hypothesis before merging, with experiment designs and related work.
- `literature-index.md`: 188 verified papers grouped by architecture family, with URLs.
- `literature-verified-details.md`: the same papers with abstract summaries and a relevance note each.
- `literature-gap-notes.md`: what each of the 12 search angles found and what gap it revealed.
- `notes-on-your-four-papers.md`: my summary of the four papers you already had, plus the exposé.
- `critic-and-extra-sweeps.md`: the completeness critic's objections and four follow-up searches (regulation, external policy sets, native privacy mechanisms, deterministic inference).

Things I could not verify: one candidate paper ("Cost-Performance Trade-offs in Checkpoint-Based LLM Agent Architectures", a ResearchGate upload) could not be confirmed to exist. Two reviewers could not locate "Safe Observability" (Melnyk 2025). Treat both as unconfirmed.
