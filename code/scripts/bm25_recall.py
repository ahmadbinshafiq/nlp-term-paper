"""Measure BM25 recall over gold sub-questions (decision D-002, gate: top-3 recall above 0.8).

Each "#n" in a sub-question is replaced by the gold answer of sub-question n.
Run:  uv run python code/scripts/bm25_recall.py
"""

import json
import re
from pathlib import Path

from auditarch.retrieval import Bm25Index, build_corpus, load_tasks

ROOT = Path(__file__).resolve().parents[2]
KS = (3, 5, 10)


def fill_placeholders(question: str, answers: list[str]) -> str:
    return re.sub(r"#(\d+)", lambda m: answers[int(m.group(1)) - 1], question)


def main():
    tasks = load_tasks()
    with open(ROOT / "data" / "gold.jsonl", encoding="utf-8") as f:
        gold = {g["id"]: g for g in map(json.loads, f)}

    corpus = build_corpus(tasks)
    index = Bm25Index(corpus)
    n_paragraphs = sum(len(t["paragraphs"]) for t in tasks)
    print(f"tasks: {len(tasks)}, paragraphs: {n_paragraphs}, unique passages in pool: {len(corpus)}")

    hits = {k: 0 for k in KS}
    hits_by_hops = {}          # hops -> [hits at top 3, sub-questions]
    all_hops_hit = 0           # tasks where every sub-question is a top-3 hit
    n_sub = 0
    for task in tasks:
        steps = gold[task["id"]]["decomposition"]
        answers = [s["answer"] for s in steps]
        task_ok = True
        for step in steps:
            query = fill_placeholders(step["question"], answers)
            ranked = index.search(query, k=max(KS))
            n_sub += 1
            for k in KS:
                hits[k] += step["support_pid"] in ranked[:k]
            hit3 = step["support_pid"] in ranked[:3]
            task_ok = task_ok and hit3
            row = hits_by_hops.setdefault(task["hops"], [0, 0])
            row[0] += hit3
            row[1] += 1
        all_hops_hit += task_ok

    print(f"sub-questions: {n_sub}")
    for k in KS:
        print(f"recall@{k}: {hits[k] / n_sub:.3f}  ({hits[k]}/{n_sub})")
    for hops, (h, n) in sorted(hits_by_hops.items()):
        print(f"recall@3 for {hops}-hop tasks: {h / n:.3f}  ({h}/{n})")
    print(f"tasks where every sub-question is a top-3 hit: {all_hops_hit}/{len(tasks)}")


if __name__ == "__main__":
    main()
