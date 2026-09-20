# Do not cite (or cite only with care)

Checked against the primary sources on 2026-09-20. Re-check in the week-11 citation audit.

## Do not cite for results

| Source | What is wrong | What to do |
|---|---|---|
| **Gupta, "Verifiability-First Agents"** (PDF in `papers/untrusted/`) | Of its 18 references, 10 cannot be found and 4 have wrong details. Three of its arXiv ids lead to unrelated physics and maths papers. The text contradicts its own results table. No dataset or experiment details. | Do not cite its numbers. At most mention it as an example of the "signed receipts plus audit agent" design idea, and say that its results could not be checked. Details: `research/notes-on-your-four-papers.md`. |
| **GraphTracer**, arXiv 2510.10581 | Withdrawn by its authors on 2025-12-22 (v2). arXiv comment: the authors name a fundamental error in the method that affects the main results. Only v1 has the full text. | Do not use its results. If it must be named, write "(withdrawn)" and point to v1. BibTeX key `graphtracer2025` exists for that case only. |

## Cite, but word it carefully

| Source | The trap | Correct wording |
|---|---|---|
| **IETF `draft-sharif-agent-audit-trail`** ("Agent Audit Trail", R. Sharif, version -04 of 2026-09-15, expires 2027-03-19) | It looks like a standard. It is an individual Internet-Draft. No working group has adopted it, it is not an RFC, and the IETF page says it is not endorsed and has no formal standing. "Intended status: Standards Track" in its header is only the author's wish. | "an individual Internet-Draft (work in progress)". Never "IETF standard" or "the IETF proposes". |
| **Who&When Pro GitHub repository** (`ag2ai/whowhen_pro`; `whowhenpro/whowhen_pro` redirects to it) | It holds the evaluation harness only. Its own roadmap lists "full benchmark data release" and "data generation pipeline release" as not done. | Cite the **paper** (arXiv 2607.09996, Section 3 and Appendix C) for the injection recipe and the 18 modes. The released `taxonomy.yaml` has 17 modes. See `papers/injection-recipe-notes.md`. |
| **GRADE**, arXiv 2606.22741 | The repository README (revised 2026-09-08) withdraws the claim that the dependency layer predicts failure. Two arXiv versions exist (v1 June, v2 September 2026). | Cite it for the graph model and the edge grades (observed, declared, inferred), and for execution-layer fault localization only. State the version. |
| **CatchBench**, arXiv 2608.22808 | Four versions in four weeks; the author list grew from 1 to 8 and the paper from 39 to 55 pages. | Cite v4 (2026-09-17), state the version, and tie every number you quote to that version. |
| **Auditable Agents**, arXiv 2604.05485 | The arXiv paper is a 24-page extended version. The authors say a condensed 4-page version is in the Proceedings of the ACM AI Leadership Summit 2026; that page could not be found. The author list grew from 5 to 10. | Cite the arXiv version as a preprint and state the version. |

## Venue claims that are not confirmed yet

Cite these as arXiv preprints until the proceedings page exists:
- **TrajDebug** (2608.06346): the authors' README says Findings of EMNLP 2026. Not in the ACL Anthology on 2026-09-20.
- **AgentRx** (2602.02475): the arXiv comment says EMNLP Findings 2026. Not in the ACL Anthology on 2026-09-20.
- **The Replay Gap** (2608.08239): the arXiv comment reads like a COLM 2026 paper, but the paper header and the README say it is a workshop at COLM 2026 (2026-10-09), and that workshop has no proceedings.
- **ECHO** (2510.04886): a NeurIPS 2025 workshop poster, confirmed on neurips.cc, but the workshop has no proceedings. Call it a workshop paper, not a NeurIPS paper.

Confirmed on the publisher's page: TraceElephant (ACL 2026, long papers), Who&When (ICML 2025, PMLR 267, spotlight poster), PROV-AGENT (IEEE eScience 2025), MuSiQue (TACL 2022).

## General rule

17 of the 36 entries in `paper/references.bib` are plain preprints and 5 more are not confirmed at a venue. Write "a recent preprint reports ..." for these, and do not build a claim of novelty on a preprint alone.
