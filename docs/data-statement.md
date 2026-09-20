# Data statement

- **Dataset:** MuSiQue-Ans, development split (`musique_ans_v1.0_dev.jsonl`, 2,417 questions).
  Paper: Trivedi, Balasubramanian, Khot and Sabharwal, "MuSiQue: Multihop Questions via Single-hop Question Composition", TACL 2022.
- **Where it came from:** the Hugging Face copy `dgslibisey/MuSiQue` (a re-upload, not the authors' own page; it has no dataset card).
  File sha256: `15fa63794d18a94ce12411aca6e2327e65b6e83b0b1490efab3f1962e48abf3b`.
  To do before submission: compare this file with the authors' release at https://github.com/StonyBrookNLP/musique.
- **License:** the authors' repository says "MuSiQue is distributed under a CC BY 4.0 License". The Hugging Face copy states no license. Checked on 2026-09-20.
- **What we use:** 250 questions with 3 or 4 hops, sampled with seed 0 (decisions D-002 and D-011). The agent sees each question, MuSiQue's sub-questions for it (without answers) and the passage pool. The passages are Wikipedia-derived text.
- **Personal data:** none collected. There are no human subjects. Real names appear only as part of the benchmark text.
- **Where the text goes:** nowhere. All models run locally on one laptop through Ollama. No passage, question or answer is sent to an outside service.
- **Models:** GLM-4.7-Flash (MIT license). Qwen3.8 27B as second auditor (Apache 2.0, as shown by `ollama show qwen3.8:27b --license`).
- **Faults:** every fault in the study is synthetic. It is planted by our own tool wrapper in a run that was correct before.
- **Gold labels:** kept in `data/gold.jsonl`, apart from `data/tasks.jsonl`. `tests/test_no_leak.py` checks that no file a model can see contains gold metadata.
