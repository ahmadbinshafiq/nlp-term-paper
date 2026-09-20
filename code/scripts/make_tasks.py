"""Build data/tasks.jsonl and data/gold.jsonl from the MuSiQue dev file (decision D-002).

tasks.jsonl holds only what the agent may see. gold.jsonl holds everything else.
Run:  uv run python code/scripts/make_tasks.py
"""

import json
import random
from collections import Counter
from pathlib import Path

from auditarch.retrieval import make_pid

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "musique_ans_v1.0_dev.jsonl"
N_CANDIDATES = 120
SEED = 0


def main():
    rows = {}
    with open(RAW, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rows[row["id"]] = row

    ids = sorted(i for i in rows if i.startswith(("3hop", "4hop")))
    sample = random.Random(SEED).sample(ids, N_CANDIDATES)  # this order is the "seed order"

    with open(ROOT / "data" / "tasks.jsonl", "w", encoding="utf-8") as tasks_f, \
         open(ROOT / "data" / "gold.jsonl", "w", encoding="utf-8") as gold_f:
        for order, task_id in enumerate(sample):
            row = rows[task_id]
            pid_of = {p["idx"]: make_pid(p["title"], p["paragraph_text"]) for p in row["paragraphs"]}

            task = {
                "id": task_id,
                "order": order,
                "hops": int(task_id[0]),
                "question": row["question"],
                "paragraphs": [
                    {"idx": p["idx"], "pid": pid_of[p["idx"]], "title": p["title"], "text": p["paragraph_text"]}
                    for p in row["paragraphs"]
                ],
            }
            gold = {
                "id": task_id,
                "answer": row["answer"],
                "answer_aliases": row["answer_aliases"],
                "is_supporting": [p["idx"] for p in row["paragraphs"] if p["is_supporting"]],
                "supporting_pids": [pid_of[p["idx"]] for p in row["paragraphs"] if p["is_supporting"]],
                "decomposition": [
                    {
                        "question": step["question"],
                        "answer": step["answer"],
                        "paragraph_support_idx": step["paragraph_support_idx"],
                        "support_pid": pid_of[step["paragraph_support_idx"]],
                    }
                    for step in row["question_decomposition"]
                ],
            }
            tasks_f.write(json.dumps(task, ensure_ascii=False) + "\n")
            gold_f.write(json.dumps(gold, ensure_ascii=False) + "\n")

    hops = Counter(int(i[0]) for i in sample)
    print(f"candidates: {len(ids)}, sampled: {len(sample)}, hop counts: {dict(sorted(hops.items()))}")
    print("first five in seed order:", sample[:5])


if __name__ == "__main__":
    main()
