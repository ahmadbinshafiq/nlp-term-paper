# Context for the term-paper research task

## Who the user is
- Master's student in NLP at Trier University, Germany. Engineer by background, new to research.
- Writing an NLP term paper (one semester, single student, modest compute/API budget).
- Needs ONE concrete, testable hypothesis. Does not need to be highly novel, but must have some novelty.
- Wants plain English, brief writing.

## The exposé (verbatim, submitted already)

Title: Comparing Auditable Architectures for LLM Agents

This term paper will compare three approaches to building auditable LLM agents: log-primary
architectures, checkpoint-based architectures, and provenance-overlay systems. The study will
draw on multiple recent works representing each of these approaches, without focusing on any
single system as the primary reference, and will instead treat representative architectures from
each category as equally important for comparison.

The paper will not assume that one architecture is universally more auditable. Instead, it will
study how different architectures support different audit goals, such as identifying the source of
an error, tracing claims back to evidence, reconstructing an execution, checking policy
compliance, and reviewing agent decisions.

Main research question: How do log-primary, checkpoint-based, and provenance-overlay architectures
differ in their support for specific audit tasks, and what trade-offs do they introduce in terms of
storage, implementation complexity, privacy, and computational cost?

The evaluation will be based on a controlled agent workflow applied consistently across the
different architectures, allowing for a structured comparison of how each system supports key
audit tasks such as failure localization, evidence tracing, execution reconstruction, and
counterfactual analysis.

Expected outcome: not a single ranking of architectures, but a clearer understanding of which
architecture is most suitable for which audit requirement and use case.

## Working definitions of the three architecture families (from the exposé + papers)
1. **Log-primary / event-sourced**: an append-only event log is the source of truth; state is a fold/projection over the log. Example: ActiveGraph (Nakajima 2026). Related: event sourcing, durable execution engines (Temporal, Restate, Inngest), "the log is the agent".
2. **Checkpoint-based**: the agent state is snapshotted at intervals or at each step; you can resume/rewind from snapshots. Example: LangGraph checkpointers ("time travel"), Autogen/ CrewAI state persistence, Ray/Flink-style checkpointing. NOTE: no paper in the user's folder represents this family yet. The literature sweep must find representatives.
3. **Provenance-overlay**: an ordinary agent run plus a separately built graph of entities/activities/agents (W3C PROV style) or a semantic claim→evidence graph. Examples: PROV-AGENT (Souza et al. 2025), the semantic provenance graphs in Rasheed et al. 2026, GRADE (Zhao 2026), OpenTelemetry GenAI spans / AgentOps taxonomy.

## Paper 1: "Auditable Agents" — Nian, Yuan, Zhang, Li, Li, Hu, Wei, Xiao, Xiao, Zhao. USC/ASU/UTK/JHU. arXiv:2604.05485v2 (Aug 2026). Position paper.
- Claim: no agent system can be accountable without auditability. Distinguishes accountability (goal), auditability (system property), auditing (process).
- **Five dimensions of auditability with metrics** (this is a ready-made measurement framework):
  - Action Recoverability: ACR (fraction of policy-relevant actions in record), RF (record fidelity: fraction of required fields recoverable per action).
  - Lifecycle Coverage: LPC (fraction of lifecycle phases observed: retries, fallbacks, approvals, delegations), GB (gap burden = unobserved content).
  - Policy Checkability: SPDR (fraction of structural policies decidable from the record: comply/violate/undecidable), ADL (audit detection latency).
  - Responsibility Attribution: AC (fraction of actions with full responsibility chain), ACD (avg recovered chain depth).
  - Evidence Integrity: IS ordinal (0 none / 1 append-only / 2 hash-chained / 3 signed), VC (verification cost).
  - Proposition 1: one missing field in the record schema can make a whole class of policies undecidable.
- Three mechanism classes: detect (pre-deployment static analysis), enforce (runtime mediation, e.g. Aegis firewall: 8.3 ms median overhead, signed hash-chained records), recover (post-hoc reconstruction, e.g. implicit execution tracing via watermarking, ~0.93 IoU).
- Auditability Card (6 questions) as a reporting artifact.
- **Stated limitations / open problems that a term paper could pick up**:
  - "No end-to-end audit": they never measured all five dimensions on a single deployed system with ground-truth violations.
  - Threshold calibration for the auditability predicate is open.
  - Only structural policies; semantic policies (OP4) open.
  - OP3: full-chain attribution across delegation. OP5: adversarial recovery. OP6: cross-party audit aggregation.
  - Privacy vs data minimization tension acknowledged but no mechanism.
  - Table 5 positions related work (ToolEmu, R-Judge, Agent-SafetyBench, AgentSpec, AGrail, AgentOps, SMACTR, Mökander, South et al. authenticated delegation, Chan et al. visibility, Ojewale et al. audit trails) — none covers all five dimensions; Evidence Integrity and Lifecycle Coverage most neglected.
- Cites AgentRx (Barke et al. 2026, diagnosing agent failures from trajectories), GRADE (Zhao 2026), Ojewale et al. 2026 audit trails (hash-chained, model lifecycle not agent runtime).

## Paper 2: "From Fluent to Verifiable: Claim-Level Auditability for Deep Research Agents" — Rasheed, Banerjee, Mukherjee, Hazra. arXiv:2602.13855 (Feb 2026). Perspective paper.
- Argues logs record WHAT happened but not WHICH source supports WHICH claim and HOW. Calls for semantic provenance (claim–evidence graph) not action traces. W3C PROV is a base but insufficient.
- Failure taxonomy for deep research agents: objective drift, metric misalignment, baseline rediscovery (planning); constraint loss over long context / cross-validation bug, transient memory (execution); citation decorrelation, unverifiable inference chain (synthesis); model-size dependent failures.
- **AAR standard metrics** (ready-made): Provenance Coverage PCov (fraction of claims with a complete path source→reasoning→claim), Provenance Soundness PSnd (fraction of claim–source pairs where the source actually entails the claim, via NLI threshold), Contradiction Transparency CTran (fraction of real source conflicts that the system surfaced), Audit Effort AEff (human minutes per claim; proxy = path length).
- Auditability invariant: verification effort must be much smaller than generation effort (E_verify << E_generate).
- Formal graph: source nodes, reasoning nodes (deduction/induction/synthesis, model id), claim nodes; typed edges supports/contradicts/refines/prerequisite with entailment strength.
- Argues validation must run DURING synthesis, not post hoc; post-hoc verification "cannot recover missing reasoning chains".
- Objections addressed: bigger models will fix it; graphs too expensive; logs are enough; validation adds latency.
- Relevant cited works: PROV-AGENT (Souza et al. 2025, e-Science), DeepTRACE (Venkit et al. ICLR 2026: citation accuracy 40–80%), VeriTrail (Metropolitansky & Larson 2025), VeriLA (Sung et al. 2025), Fernsel et al. 2024 (auditability assessment framework), Cemri et al. 2025 "Why do multi-agent LLM systems fail?" (MAST taxonomy), Beel & Kan 2025 evaluation of Sakana AI Scientist, RE-TRAC trajectory compression, Zep, KGoT, HippoRAG.

## Paper 3: "The Log is the Agent: Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems" — Yohei Nakajima. arXiv:2605.21997 (May 2026). Systems paper. Open source: pip install activegraph (Apache-2.0), docs.activegraph.ai.
- ActiveGraph: append-only event log is source of truth; graph = deterministic projection (fold) of log; behaviors subscribe to graph patterns and emit events. No orchestrator.
- Properties: deterministic replay (model/tool responses cached content-addressed by prompt hash, temperature 0), cheap forking at any event (shared prefix served from cache, no new model calls), structural diff between runs, end-to-end lineage (every object has provenance: behavior + causing event + model request event).
- Strict vs permissive replay; strict replay = proof of reproducibility, catches determinism-contract violations.
- Worked example: diligence pack, 671 events, 93 objects, 76 relations, 103 model calls, 48 tool calls; runs offline from fixtures, byte-deterministic.
- Table 1 compares: conventional loop vs memory-layer vs ActiveGraph on persistence, provenance, deterministic reconstruction, replay, fork, fork cost, structural diff.
- **Stated limitations**: replay cost grows with log length; no checkpointing/compaction yet ("a million-event run is replayed in full today"); schema evolution burden; side-effecting tools only replay their record; concurrent writers unresolved; determinism contract only enforced dynamically; **"We report no large-scale empirical evaluation ... Establishing that the auditability and forking properties translate into measurable advantages on downstream agent tasks is the natural next step."**
- Related: MemGPT/Letta, Zep/Graphiti, Mem0, Hindsight, blackboard architectures, BabyAGI.

## Paper 4: "Verifiability-First Agents: Provable Observability and Lightweight Audit Agents..." — Abhivansh Gupta, IIT Roorkee. 5-page workshop-style preprint (AAAI format).
- VFA architecture: Intent Specification (ISpec: objective/constraint/policy/verification layers), Action Attestation Layer (signed receipts: id, tool, args hash, result hash, timestamp, signature), Provenance Log, Audit Agents (rule-based + statistical + semantic ensemble computing an alignment score), Challenge–Response Attestation, Controller & Remediator. OPERA benchmark proposal.
- Metrics: Time-to-Detect, Remediation Latency, Attribution Confidence (fraction of episodes with perfect reconstruction), FPR, composite VScore.
- Reported: 150 episodes, 7B–13B models; Td 35.4→11.9 s vs no-verifier; AC 0.62→0.85; overhead <6.5%; FPR <7%. Ablations: removing attestation layer hurts most.
- CAUTION: the paper is thin (no experimental details, no dataset description) and several references look questionable (e.g. "Wang, Chen, and Liu 2024. AgentBench" has wrong authors; "Krishnan and Mishra 2024", "Lee and Suresh 2025", "Pan and Liu 2023", "Feng, Lin, Zhu 2024 VeriLLM", "Long, Zhang, Du 2024", "Xu, Hu, Lin 2024", "Zhang and Tan 2025", "Shen, Tang 2023" may not exist). Treat as low-reliability; useful only as an example of the "signed receipts + runtime audit agent" design pattern (closer to log-primary + integrity than to any of the three families).

## Audit tasks named in the exposé (the paper must evaluate these)
- Failure localization (which step/agent caused the error; cf. Who&When benchmark, AgentRx, TRAIL)
- Evidence tracing (which source supports which claim; cf. AAR PCov/PSnd)
- Execution reconstruction (rebuild what happened; cf. ACR/RF/LPC, replay)
- Counterfactual analysis (what if step k had been different; cf. ActiveGraph fork)
- Policy compliance checking (cf. SPDR)
- Decision review

## Trade-off axes named in the exposé
storage, implementation complexity, privacy, computational cost.
