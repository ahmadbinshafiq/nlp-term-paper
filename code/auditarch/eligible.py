"""Which steps of a clean run can carry which fault (prereg/fault_catalogue.md, column "Reachable if").

Used by the gate now (every task must allow all six faults) and by the fault injector in week 3.
"""

FAULT_TYPES = ["wrong_argument", "corrupted_output", "dropped_note", "overwritten_note", "wrong_source", "no_source"]


def eligible_steps(events: list, fault_type: str) -> list[int]:
    """The step ids where `fault_type` could be planted, in order."""
    steps = []
    queries, read_pids, note_keys = [], [], []      # what happened before the current step
    last_results = []                               # handles returned by the latest search
    prev_think = ""                                 # text of the think step just before, "" if there was none
    for event in events:
        ran = event.tool_call and "error" not in event.tool_return      # a refused call changed nothing (same rule as the gate)
        name = event.tool_call.name if ran else None
        args = event.tool_call.args if ran else {}
        after_think = bool(prev_think.strip())      # row 1: the think text is the only trace of a wrong argument

        if name == "search":
            stale_query_exists = any(q != args.get("query") for q in queries)
            ok = {"wrong_argument": stale_query_exists and after_think, "corrupted_output": True}
        elif name == "read":
            other_unread = [h for h in last_results if h != args.get("handle") and h not in read_pids]
            ok = {"wrong_argument": bool(other_unread) and after_think,
                  "corrupted_output": bool(queries) and args.get("handle") not in read_pids}
        elif name == "write_note":
            other_notes = [k for k in note_keys if k != args.get("key")]
            other_reads = [p for p in read_pids if p != args.get("source_pid")]
            ok = {"dropped_note": True, "no_source": True,
                  "overwritten_note": bool(other_notes), "wrong_source": bool(other_reads)}
        else:
            ok = {}
        if ok.get(fault_type):
            steps.append(event.step_id)

        # remember this step for the ones that follow
        if name == "search":
            queries.append(args.get("query"))
            last_results = [r["handle"] for r in event.tool_return.get("results", [])]
        elif name == "read" and "pid" in event.tool_return:
            read_pids.append(event.tool_return["pid"])
        elif name == "write_note":
            note_keys.append(args.get("key"))
        prev_think = event.state_patch[0]["value"] if event.node_kind == "think" else ""
    return steps
