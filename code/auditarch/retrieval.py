"""Offline BM25 search over the pooled passage corpus (decision D-002)."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from rank_bm25 import BM25Okapi

TASKS_PATH = Path(__file__).resolve().parents[2] / "data" / "tasks.jsonl"


def make_pid(title: str, text: str) -> str:
    """Stable passage id: the same title and text always give the same id."""
    return hashlib.sha1(f"{title}\n{text}".encode("utf-8")).hexdigest()[:12]


def tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, split on anything that is not a letter or digit."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+", text.lower())


def load_tasks(path: Path = TASKS_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_corpus(tasks: list[dict]) -> dict[str, dict]:
    """Pool the paragraphs of all tasks. Same title and text -> one passage."""
    corpus = {}
    for task in tasks:
        for p in task["paragraphs"]:
            corpus.setdefault(p["pid"], {"pid": p["pid"], "title": p["title"], "text": p["text"]})
    return corpus


class Bm25Index:
    def __init__(self, corpus: dict[str, dict]):
        self.pids = sorted(corpus)  # sorted, so the index is the same on every run
        self.corpus = corpus
        docs = [tokenize(corpus[pid]["title"] + " " + corpus[pid]["text"]) for pid in self.pids]
        self.bm25 = BM25Okapi(docs)

    def search(self, query: str, k: int = 3) -> list[str]:
        """Return the pids of the k best passages, best first. Ties break by pid."""
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.pids, scores), key=lambda pair: (-pair[1], pair[0]))
        return [pid for pid, _ in ranked[:k]]
