<!-- Reading-kit note. Written from the paper itself by one agent and checked against the sources by a second one, 2026-09-20. -->

# Who&When Pro (arXiv 2607.09996)

## 1. Recipe
1. **Seeds.** Successful runs become seeds; failed runs only feed the taxonomy (§3.1, §3.2).
2. **Pick step t.** Sampled given the target mode; each family has a preferred position (§3.3).
3. **Build the wrong action.** A frontier model reads the context up to t and writes an injection prompt. Patched into the agent's model call at t, it makes the base agent model write the wrong action (§3.3, App. K).
4. **Warm start.** Recorded actions 1..t-1 are replayed. Static tool calls come from a seed-time cache, so observations are byte-identical (§3.3). For smolagents: SQLite, key = SHA-256 of tool parameters. Live browsers (Magentic-One) are re-run with fidelity checks; a mismatch aborts (App. F.3).
5. **Continue.** The wrong action replaces step t; the agent runs on from t+1 (§3.3).
6. **Filter.** Keep only failing runs. Drop traces that leak the injection prompt or where the answer was clear before t (§3.3).
7. **Ground truth.** Decisive step = earliest step whose fix makes the run succeed (§3). Undoing the injection restores the seed, "so t is the decisive step by definition" (§3.3).

## 2. Taxonomy
Table 5 (App. C): **18 modes**, six families. `taxonomy.yaml` and dataset card: **17 modes**.
- Perception: visual misidentification, grounding error
- Reasoning: hallucination, reasoning error, calculation error, task misunderstanding
- Planning: ineffective planning, goal drift
- Action: tool parameter error, *hallucinated tool or action*, output format error, premature termination, looping behavior
- Verification: context loss, inadequate verification
- Coordination: delegation and orchestration error, communication failure, over-reliance on other agents

The YAML lacks the italic mode, so its Action codes (A.1 to A.4) shift: YAML A.2 = output format, Table 5 A.2 = hallucinated tool. Match by name, not code. Released text and video labels contain no A.5.

## 3. Length and position
The word confound never appears. Reported:
- Position depends on family: planning early, verification late (§3.3). 64% of injections fall at 40-80% of the trace (App. D.5).
- Step accuracy drops from 94% (under 3K tokens) to 50% (over 12K) (§4.2, Fig. 4c).

I found no analysis separating position or length from mode.

## 4. GitHub release
Evaluation harness only: `whowhen_eval/` plus scorer tests. README roadmap: only the harness is ticked; full data release and generation pipeline are not. No injection code in the file tree, so cite the recipe from the paper only.

## 5. Differences from ours
1. **Fault source.** Theirs: a wrong agent action, written by the LLM under an injection prompt. Ours: a tool wrapper corrupts arguments, outputs, notes or sources. Table 5 has no mode for corrupted tool output.
2. **Replay.** They cache tool outputs only, not LLM calls (App. F.3). We plan to cache LLM calls.
3. **Controls.** They keep failing runs only; no sham arm found. We plan one.

## How to cite this in the paper
- Cite the **paper** (arXiv 2607.09996, Section 3, Section 3.3, Appendix C Table 5, Appendix F.3) for the recipe and the taxonomy.
- Never cite the GitHub repository for the recipe: it holds the evaluation harness only.
- Say "18 modes in the paper, 17 in the released `taxonomy.yaml`" if you mention the count at all.
- It is an arXiv preprint (no venue claimed on 2026-09-20).

## Still unverified (checked 2026-09-20)
- Why the released YAML has 17 modes and the paper 18 is not explained anywhere. The mode "hallucinated tool or action" is missing from the YAML and the dataset card.
- The numbers 94% / 50% (Fig. 4c) and 64% (App. D.5, Fig. 15) are from the paper text; the figures were not viewed.
- "No sham arm" and "no analysis that separates position or length from mode" are negative findings from a keyword search of the HTML version, not from a full read of the PDF.
- The image splits of the Hugging Face dataset could not be checked.
- "Ours" in section 5 is still a plan: the LLM cache, the fault wrapper and the sham arm are not written yet.
