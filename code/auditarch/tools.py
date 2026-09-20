"""The agent's four tools (docs/schema.md, decision D-005).

The model calls a tool by writing one JSON action (see action_schema).
Each tool is a plain function of (args, state, index). It returns two things:
  - the tool return (what the agent sees), and
  - the state effect, as a list of JSON Patch operations.
Tools never raise. A bad call gives back {"error": ...} and changes nothing.
"""

from jsonpointer import escape

# The arguments of each tool. All arguments are strings.
TOOL_ARGS = {
    "search": ["query"],
    "read": ["handle"],
    "write_note": ["key", "text", "source_pid"],
    "finish": ["answer", "note_key"],
}


def action_schema(allowed: list) -> dict:
    """JSON schema for one action: {"tool": <one of allowed>, "args": {...}}.

    Ollama forces the model's reply to fit this schema, so the agent cannot call
    a tool that is not allowed, and the reply always parses.
    """
    def one(name):
        args = {"type": "object", "properties": {a: {"type": "string"} for a in TOOL_ARGS[name]}, "required": TOOL_ARGS[name]}
        return {"type": "object", "properties": {"tool": {"enum": [name]}, "args": args}, "required": ["tool", "args"]}
    return {"anyOf": [one(name) for name in allowed]}


SEARCH_RESULTS = 5    # how many passages a search returns
SNIPPET_CHARS = 200    # how much of a passage a search result shows


def set_op(state: dict, section: str, key: str, value) -> dict:
    """One patch operation that sets state[section][key]: 'add' if the key is new, else 'replace'."""
    op = "replace" if key in state[section] else "add"
    return {"op": op, "path": f"/{section}/{escape(key)}", "value": value}


def result_list(index, pids: list) -> list:
    """How a search shows passages: handle, title and the first words of the text."""
    return [{"handle": pid, "title": index.corpus[pid]["title"], "snippet": index.corpus[pid]["text"][:SNIPPET_CHARS]}
            for pid in pids]


def search(args, state, index):
    query = str(args.get("query", ""))
    earlier = [c["tool_call"]["args"].get("query") for c in state["calls"].values() if c["tool_call"]["name"] == "search"]
    if query in earlier:
        return {"error": "you already sent this query; use other words"}, []
    return {"results": result_list(index, index.search(query, k=SEARCH_RESULTS))}, []


def read(args, state, index):
    pid = str(args.get("handle", ""))
    if pid not in index.corpus:
        return {"error": "unknown handle"}, []
    if pid in state["evidence"]:
        return {"error": "you already read this passage; read another result or search again"}, []
    passage = index.corpus[pid]
    seen = {"title": passage["title"], "text": passage["text"]}
    return {"pid": pid, **seen}, [set_op(state, "evidence", pid, seen)]


def write_note(args, state, index):
    key = str(args.get("key", ""))
    if key in state["notes"]:
        return {"error": "this key already exists; use a new key"}, []
    note = {"text": str(args.get("text", "")), "source_pid": args.get("source_pid")}
    return {"ok": True}, [set_op(state, "notes", key, note)]


def finish(args, state, index):
    note_key = str(args.get("note_key", ""))
    note = state["notes"].get(note_key)
    # cited_pid is copied from the note, never chosen by the model. A missing note gives null (D-005).
    decision = {"note_key": note_key, "cited_pid": note["source_pid"] if note else None}
    return {"ok": True}, [
        {"op": "replace", "path": "/answer", "value": str(args.get("answer", ""))},
        {"op": "replace", "path": "/decision", "value": decision},
    ]


TOOLS = {"search": search, "read": read, "write_note": write_note, "finish": finish}
