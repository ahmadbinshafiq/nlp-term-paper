"""Planting one fault at step k of a run (prereg/fault_catalogue.md).

choose_k(...)  which step gets the fault: a fixed formula, nothing random (catalogue rule 5)
plant(...)     what the step does instead of the plain tool: returns (tool_call, tool_return, effect)

The agent calls plant() at step k only. Everything before k comes from the cache, so it is
byte-identical to the clean run; everything after k is a live continuation.
"""

from auditarch.eligible import FAULT_TYPES, eligible_steps
from auditarch.tools import SEARCH_RESULTS, TOOLS, result_list, set_op

FAULT_CLASS = {"wrong_argument": "tool", "corrupted_output": "tool", "dropped_note": "state",
               "overwritten_note": "state", "wrong_source": "evidence", "no_source": "evidence", "sham": "none"}
JUNK_RANK = 50          # corrupted output shows what BM25 ranks from here on: clearly unrelated passages


def choose_k(events: list, fault_type: str, task_position: int) -> dict:
    """The step for this fault in this task. task_position = place of the task in its pool, from 0."""
    if fault_type == "sham":
        steps = eligible_steps(events, "dropped_note")               # every write_note step that ran
        return {"k": steps[len(steps) // 2], "k_bin": 1}

    row = FAULT_TYPES.index(fault_type) + 1                           # row number in the catalogue, 1 to 6
    steps = eligible_steps(events, fault_type)
    if row <= 2:                                                      # rows 1 and 2 have a search and a read variant
        tool_at = {e.step_id: e.tool_call.name for e in events if e.tool_call}
        wanted = "search" if (task_position + row) % 2 == 0 else "read"
        steps = [k for k in steps if tool_at[k] == wanted] or steps   # the other variant if the wanted one cannot be built

    m = len(steps)
    stratum = (task_position + row) % 3                               # 0 early, 1 middle, 2 late
    rank = (2 * stratum + 1) * m // 6
    return {"k": steps[rank], "k_bin": 3 * (2 * rank + 1) // (2 * m)}


def earlier_calls(state: dict, name: str) -> list:
    """The calls of one tool that ran before this step, oldest first."""
    calls = [state["calls"][step] for step in sorted(state["calls"], key=int)]
    return [c for c in calls if c["tool_call"]["name"] == name and "error" not in c["tool_return"]]


def plant(fault_type: str, tool_call: dict, state: dict, index):
    """Returns (tool_call, tool_return, effect) for the faulty step. `tool_call` is what the agent asked for."""
    name, args = tool_call["name"], dict(tool_call["args"])
    searches, reads, notes = (earlier_calls(state, tool) for tool in ("search", "read", "write_note"))

    if fault_type == "wrong_argument" and name == "search":          # row 1a: a stale query, and its real results
        args["query"] = [s["tool_call"]["args"]["query"] for s in searches if s["tool_call"]["args"]["query"] != args["query"]][-1]
        return {"name": name, "args": args}, {"results": result_list(index, index.search(args["query"], k=SEARCH_RESULTS))}, []

    if fault_type == "wrong_argument" and name == "read":            # row 1b: another unread handle from the latest search
        offered = [r["handle"] for r in searches[-1]["tool_return"]["results"]]
        args["handle"] = [h for h in offered if h != args["handle"] and h not in state["evidence"]][0]
        return {"name": name, "args": args}, *TOOLS["read"](args, state, index)

    if fault_type == "corrupted_output" and name == "search":        # row 2a: right query, unrelated results
        junk = index.search(args["query"], k=JUNK_RANK + SEARCH_RESULTS)[JUNK_RANK:]
        return tool_call, {"results": result_list(index, junk)}, []

    if fault_type == "corrupted_output" and name == "read":          # row 2b: right passage id and title, text of an unrelated passage
        junk_pid = index.search(searches[-1]["tool_call"]["args"]["query"], k=JUNK_RANK + 1)[JUNK_RANK]
        seen = {"title": index.corpus[args["handle"]]["title"], "text": index.corpus[junk_pid]["text"]}
        return tool_call, {"pid": args["handle"], **seen}, [set_op(state, "evidence", args["handle"], seen)]

    if fault_type == "dropped_note":                                 # row 3: the write is swallowed, the tool still says ok
        return tool_call, {"ok": True}, []

    if fault_type == "overwritten_note":                             # row 4: the text lands in the most recent other note
        other_key = [n["tool_call"]["args"]["key"] for n in notes if n["tool_call"]["args"]["key"] != args["key"]][-1]
        note = {"text": args["text"], "source_pid": args["source_pid"]}
        return tool_call, {"ok": True}, [set_op(state, "notes", other_key, note)]

    if fault_type == "wrong_source":                                 # row 5: the note cites the most recently read other passage
        args["source_pid"] = [r["tool_return"]["pid"] for r in reads if r["tool_return"]["pid"] != args["source_pid"]][-1]
    if fault_type == "no_source":                                    # row 6: the note cites nothing
        args["source_pid"] = None
    # rows 5 and 6 change the call only; the sham changes nothing. The plain tool does the rest.
    return {"name": name, "args": args}, *TOOLS[name](args, state, index)
