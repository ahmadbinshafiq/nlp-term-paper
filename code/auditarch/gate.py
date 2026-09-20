"""The gate: is this clean run good enough to plant faults into? (DECISIONS.md, D-006)

All checks are mechanical. Gold data is used here, offline, and is never shown to a model.
"""

import re
import string

from auditarch.eligible import FAULT_TYPES, eligible_steps


NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
                "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12"}


def normalize(text: str) -> str:
    """The usual answer normalization: lowercase, no punctuation, no articles, single spaces. Also "two" -> "2"."""
    text = "".join(ch for ch in text.lower() if ch not in string.punctuation)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(NUMBER_WORDS.get(word, word) for word in text.split())


def answers_match(answer: str, gold_answers: list) -> bool:
    """True if the answer equals a gold answer, or one is a run of whole words inside the other.

    So "summer or fall" matches "usually in the summer or fall", but "1" does not match "1952".
    """
    a = normalize(answer).split()
    for gold in gold_answers:
        g = normalize(gold).split()
        short, long = sorted([a, g], key=len)
        if short and any(long[i:i + len(short)] == short for i in range(len(long) - len(short) + 1)):
            return True
    return False


def check_clean_run(events: list, app: dict, ended: str, gold: dict) -> dict:
    """Returns {"failed": [...names of failed checks...], "flags": [...]}. An empty "failed" list means pass."""
    failed, flags = [], []
    # only calls that ran; a refused call (the tool returned an error) changed nothing
    calls = [(e.step_id, e.tool_call.name, e.tool_call.args, e.tool_return) for e in events
             if e.tool_call and "error" not in e.tool_return]

    # 1. the answer is correct
    if not answers_match(app["answer"] or "", [gold["answer"], *gold["answer_aliases"]]):
        failed.append("answer_wrong")

    # 2. the run reached finish, and the note it names exists
    decision = app["decision"] or {}
    if ended != "finish":
        failed.append("not_finished:" + ended)
    elif decision.get("note_key") not in app["notes"]:
        failed.append("finish_note_missing")

    # 3. the cited passage is a gold supporting passage
    if decision.get("cited_pid") not in gold["supporting_pids"]:
        failed.append("cited_pid_not_gold")

    # 4. no hidden fault of our own kinds
    read_so_far, keys_so_far = set(), set()
    for step, name, args, ret in calls:
        if name == "read" and "pid" in ret:
            read_so_far.add(ret["pid"])
        if name == "write_note":
            if args.get("key") in keys_so_far:
                failed.append(f"note_key_written_twice@{step}")
            if args.get("source_pid") is None:
                failed.append(f"null_source@{step}")
            elif args.get("source_pid") not in read_so_far:
                failed.append(f"source_not_read_before@{step}")
            keys_so_far.add(args.get("key"))

    # 5. all six faults can be built in this run
    for fault_type in FAULT_TYPES:
        if not eligible_steps(events, fault_type):
            failed.append("not_buildable:" + fault_type)

    # natural patterns that do not fail the gate but are counted
    queries = [args.get("query") for _, name, args, _ in calls if name == "search"]
    if len(queries) != len(set(queries)):
        flags.append("same_query_twice")
    offered = set()
    for _, name, args, ret in calls:
        if name == "search":
            offered |= {r["handle"] for r in ret.get("results", [])}
        if name == "read" and args.get("handle") not in offered:
            flags.append("read_of_unoffered_handle")
    return {"failed": failed, "flags": flags}
