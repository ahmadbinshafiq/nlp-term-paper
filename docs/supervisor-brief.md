# Term paper brief for the supervisor meeting

**Topic (from the exposé):** Comparing Auditable Architectures for LLM Agents: log-primary, checkpoint-based and provenance-overlay.

## What I want to test

**Hypothesis.** The best record format for finding a fault in an agent run depends on the kind of fault.
An event log is best for tool faults, state diffs are best for state faults, and a provenance graph is best for evidence faults.

**Why this is new.** I found no study that compares the three record families side by side on an audit task.
A June 2026 survey (arXiv 2606.04990) lists this as an open problem. The closest work, TraceElephant, changes how complete a record is, not its shape.

## How

1. One LangGraph agent answers MuSiQue questions with 3 or 4 hops, using four tools (search, read, write note, finish) over a fixed set of passages. With each question the agent gets the dataset's own sub-questions as a plan (no answers), because the study tests auditors, not question answering. A small local model solves about 30 percent of the tasks cleanly; only those runs are used.
2. I replay a correct run up to step k and plant one fault there. There are six fault types in three classes (tool, state, evidence). The faulty step is known, so ground truth is free.
3. The same faulty run is written in three formats that hold exactly the same information: event log, state diffs, PROV graph.
4. One LLM auditor reads each format and names the faulty step. Score: exact step accuracy.
5. One test, fixed before the main run: the interaction of format and fault class in a mixed-effects logistic model. 40 to 50 tasks, about 345 runs, 1,380 audits.
6. Controls: clean runs, sham runs, a guesser that only knows positions, and a check that no gold label leaks into a record.

**Models.** Everything runs locally and costs nothing: GLM-4.7-Flash (30B, open weights) as agent and auditor, Qwen3.8 27B as a second auditor. The weights are pinned, so anyone can repeat the study.

**Plan.** 12 weeks. Week 3: pilot with 10 runs and a go/no-go check. Week 4: plan frozen in a git tag (pre-registration). Weeks 6-7: main run. Weeks 9-12: writing.

**Fallback (Idea C).** If the pilot fails or time is short: measure storage and rebuild cost of logs against checkpoints on the same harness. No LLM auditor, lowest risk.

## Questions

1. What are the deadline, the page limit, the template and the language (German or English)?
2. Must code and data be released? May the pre-registration tag be public?
3. Is a study of LLM-auditor accuracy "NLP enough", or do you prefer the measurement study (Idea C)?
4. Is a small open-weights model on my laptop acceptable as agent and auditor, instead of a commercial model?
5. Do three equal-information formats of one LangGraph run, plus the as-shipped recorders as a side arm, count as a "controlled workflow applied consistently"?
6. Is a clean, well-controlled null result acceptable for a good grade?
7. Is one main audit task (failure localization), with short sections on the others, acceptable?
8. Will you read the one-page pre-registration before the main run? Are check-ins in weeks 3, 6 and 11 fine?
9. What are the rules for declaring AI tools used in research and writing?
10. Which citation style? May arXiv preprints be main sources? (Most related work is from 2026 and not yet peer-reviewed.)
11. The exposé promised six audit tasks, four trade-off axes and a 40-step tier. May the 40-step tier and the privacy axis shrink to a discussion paragraph?
12. Is a formal ethics or data declaration needed for public benchmark text?
13. A first power estimate says that with 50 tasks the study can detect differences of about 20 percentage points between formats, not 10. Compute is free, so I could double the number of faulty runs. Is that worth it, or is "large effects only" acceptable if stated openly?

## If we cannot meet this week

I will go on with these assumptions and change them when I hear from you: English, about 20 pages, deadline at the end of week 12 (2026-12-13), code released.
