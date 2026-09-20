"""Format 1: the event log. One block per step, in the order things happened.

    step 4 | act | read
      call: {"handle": "0123abcd4567"}
      return: {"pid": "0123abcd4567", "title": "...", "text": "..."}
      effect: ["add", "/evidence/0123abcd4567"]

An effect line says what the step changed in the state. Its value is printed only when
it is not already visible in the call or the return of the same step.
"""

import json

from auditarch.schema import Event


def implied_value(path: str, call: dict, ret: dict):
    """The value an effect has when it just stores what the call or the return already shows."""
    if path.startswith("/evidence/"):
        return {"title": ret.get("title"), "text": ret.get("text")}
    if path.startswith("/notes/"):
        return {"text": call["args"].get("text"), "source_pid": call["args"].get("source_pid")}
    if path == "/answer":
        return call["args"].get("answer")
    return None


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def render(events: list) -> str:
    lines = []
    for e in events:
        if e.node_kind == "think":
            lines += [f"step {e.step_id} | think", "  text: " + dumps(e.state_patch[0]["value"])]
            continue
        call = e.tool_call.model_dump()
        lines += [f"step {e.step_id} | act | {call['name']}", "  call: " + dumps(call["args"]), "  return: " + dumps(e.tool_return)]
        for op in e.state_patch[1:]:                       # state_patch[0] is calls[step], which the two lines above show
            effect = [op["op"], op["path"]]
            if op["value"] != implied_value(op["path"], call, e.tool_return):
                effect.append(op["value"])
            lines.append("  effect: " + dumps(effect))
    return "\n".join(lines) + "\n"


def parse(text: str) -> list:
    events = []
    for block in ("\n" + text.strip()).split("\nstep ")[1:]:
        head, *body = block.split("\n")
        fields = [line.strip().split(": ", 1) for line in body]
        step, kind = int(head.split(" | ")[0]), head.split(" | ")[1]
        if kind == "think":
            patch = [{"op": "add", "path": f"/scratch/{step}", "value": json.loads(fields[0][1])}]
            events.append(Event(step_id=step, node_kind="think", tool_call=None, tool_return=None, state_patch=patch))
            continue
        call = {"name": head.split(" | ")[2], "args": json.loads(fields[0][1])}
        ret = json.loads(fields[1][1])
        patch = [{"op": "add", "path": f"/calls/{step}", "value": {"tool_call": call, "tool_return": ret}}]
        for _, raw in fields[2:]:
            effect = json.loads(raw)
            value = effect[2] if len(effect) == 3 else implied_value(effect[1], call, ret)
            patch.append({"op": effect[0], "path": effect[1], "value": value})
        events.append(Event(step_id=step, node_kind="act", tool_call=call, tool_return=ret, state_patch=patch))
    return events
