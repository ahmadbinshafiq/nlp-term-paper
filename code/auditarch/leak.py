"""Gold-label leak check.

Anything the agent or the auditor can see (tasks, events, renderings) must not
contain gold metadata. The answer string itself may appear, because a correct
run writes it through `finish`. What is forbidden is the gold *metadata*.
"""

# Field names that exist only in data/gold.jsonl.
GOLD_KEYS = (
    "is_supporting",
    "paragraph_support_idx",
    "decomposition",
    "answer_aliases",
    "supporting_pids",
    "support_pid",
)


def find_gold_keys(text: str) -> list[str]:
    """Return the gold field names that appear anywhere in `text`."""
    return [key for key in GOLD_KEYS if key in text]
