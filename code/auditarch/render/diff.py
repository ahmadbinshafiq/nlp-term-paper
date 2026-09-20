"""Format 2: state diffs. For each step, what changed in the application state (JSON Patch).

    ## step 4 (act)
    {"op": "add", "path": "/calls/4", "value": {"tool_call": {...}, "tool_return": {...}}}
    {"op": "add", "path": "/evidence/0123abcd4567", "value": {"title": "...", "text": "..."}}

This is what a checkpoint-based record shows: not what was done, but how the saved state
differs from the checkpoint before. There is no message list, only application state.
"""

import json

from auditarch.schema import Event


def render(events: list) -> str:
    lines = []
    for e in events:
        lines.append(f"## step {e.step_id} ({e.node_kind})")
        lines += [json.dumps(op, ensure_ascii=False) for op in e.state_patch]
    return "\n".join(lines) + "\n"


def parse(text: str) -> list:
    events = []
    for block in ("\n" + text.strip()).split("\n## step ")[1:]:      # a block starts at a line that begins with "## step "
        head, *body = block.split("\n")
        step, kind = int(head.split(" ")[0]), head.split("(")[1].rstrip(")")
        patch = [json.loads(line) for line in body]
        call = patch[0]["value"] if kind == "act" else {"tool_call": None, "tool_return": None}   # calls[step] holds both
        events.append(Event(step_id=step, node_kind=kind, tool_call=call["tool_call"], tool_return=call["tool_return"],
                            state_patch=patch))
    return events
