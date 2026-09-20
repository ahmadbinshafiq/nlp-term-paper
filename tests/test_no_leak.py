"""No file that the agent or the auditor can see may contain gold metadata."""

from pathlib import Path

import pytest

from auditarch.leak import GOLD_KEYS, find_gold_keys

ROOT = Path(__file__).resolve().parents[1]

# Everything the models can see. Runs and renderings do not exist yet in week 1;
# they are picked up by these patterns as soon as they are written.
VISIBLE_PATTERNS = [
    "data/tasks.jsonl",
    "results/**/events.jsonl",
    "results/**/renderings/*",
]


def visible_files():
    files = []
    for pattern in VISIBLE_PATTERNS:
        files.extend(sorted(ROOT.glob(pattern)))
    return files


def test_tasks_file_exists():
    assert (ROOT / "data" / "tasks.jsonl").exists(), "run code/scripts/make_tasks.py first"


@pytest.mark.parametrize("path", visible_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_gold_metadata(path):
    assert find_gold_keys(path.read_text(encoding="utf-8")) == []


def test_checker_catches_gold_file():
    """The checker must fire on the gold file, or a green test above means nothing."""
    found = find_gold_keys((ROOT / "data" / "gold.jsonl").read_text(encoding="utf-8"))
    assert set(found) == set(GOLD_KEYS)
