"""Week-1 smoke test: the four building blocks work on this machine.

1. LangGraph + SqliteSaver give a StateSnapshot.
2. The prov library writes PROV-JSON with a wasDerivedFrom edge.
3. The pinned local model answers with one tool call (agent role).
4. The pinned local model returns JSON that follows a schema (auditor role).

Run:  uv run python code/scripts/smoke_test.py
"""

import json
import sqlite3
import time
from typing import TypedDict

from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from prov.model import ProvDocument

from auditarch.llm import AGENT_MODEL, AUDITOR_MODEL, chat_model, check_pins


def snapshot_demo():
    class State(TypedDict):
        notes: dict

    def write(state: State):
        return {"notes": {**state["notes"], "director": "James Cameron"}}

    graph = StateGraph(State)
    graph.add_node("write", write)
    graph.add_edge(START, "write")
    graph.add_edge("write", END)
    app = graph.compile(checkpointer=SqliteSaver(sqlite3.connect(":memory:", check_same_thread=False)))
    config = {"configurable": {"thread_id": "smoke"}}
    app.invoke({"notes": {}}, config)
    snap = app.get_state(config)
    history = list(app.get_state_history(config))
    print("1. StateSnapshot values:", snap.values, "| metadata:", snap.metadata, "| checkpoints:", len(history))


def prov_demo():
    doc = ProvDocument()
    doc.add_namespace("ent", "urn:auditarch:ent:")
    doc.add_namespace("act", "urn:auditarch:act:")
    doc.entity("ent:passage:0123abcd4567")
    doc.entity("ent:note:director@4")
    doc.activity("act:step:4")
    doc.used("act:step:4", "ent:passage:0123abcd4567")
    doc.wasGeneratedBy("ent:note:director@4", "act:step:4")
    doc.wasDerivedFrom("ent:note:director@4", "ent:passage:0123abcd4567")
    data = json.loads(doc.serialize(format="json"))
    assert "wasDerivedFrom" in data
    print("2. PROV-JSON relation kinds:", sorted(k for k in data if k != "prefix"))


@tool
def search(query: str) -> list[str]:
    """BM25 search over the passage pool. Returns passage handles."""
    return []


@tool
def read(handle: str) -> str:
    """Read one passage by its handle."""
    return ""


def speed(message) -> str:
    meta = message.response_metadata
    read_s = meta["prompt_eval_duration"] / 1e9
    write_s = meta["eval_duration"] / 1e9
    return (f"in {meta['prompt_eval_count']} tokens at {meta['prompt_eval_count'] / read_s:.0f}/s, "
            f"out {meta['eval_count']} tokens at {meta['eval_count'] / write_s:.0f}/s")


def agent_demo():
    pins = check_pins(AGENT_MODEL)
    llm = chat_model(AGENT_MODEL).bind_tools([search, read])
    start = time.time()
    message = llm.invoke([
        ("system", "Answer using only the tools. Call exactly one tool per turn."),
        ("user", "Who directed the film that won Best Picture at the 70th Academy Awards?"),
    ])
    assert len(message.tool_calls) == 1, message
    print(f"3. tool call: {message.tool_calls[0]['name']}({message.tool_calls[0]['args']}) "
          f"| {speed(message)} | {time.time() - start:.1f}s | digest {pins['model_digest'][:12]}")


AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "step_id": {"type": ["integer", "null"]},
        "fault_class": {"type": "string", "enum": ["tool", "state", "evidence", "none"]},
        "fault_type": {"type": "string"},
        "pointer": {"type": "string"},
    },
    "required": ["step_id", "fault_class", "fault_type", "pointer"],
}


def auditor_demo():
    check_pins(AUDITOR_MODEL)
    log = "\n".join(json.dumps(e) for e in [
        {"step_id": 1, "node_kind": "act", "tool_call": {"name": "read", "args": {"handle": "p:aa11"}},
         "tool_return": {"pid": "p:aa11", "text": "Titanic was directed by James Cameron."}},
        {"step_id": 2, "node_kind": "act",
         "tool_call": {"name": "write_note", "args": {"key": "director", "text": "James Cameron", "source_pid": "p:zz99"}},
         "tool_return": {"ok": True}},
    ])
    llm = chat_model(AUDITOR_MODEL, format=AUDIT_SCHEMA)
    start = time.time()
    message = llm.invoke("One fault may be planted in this agent run. Fault classes: tool, state, evidence "
                         "(a note cites a passage it did not come from). Return the faulty step.\n\n" + log)
    answer = json.loads(message.content)
    print(f"4. auditor JSON: {answer} | {speed(message)} | {time.time() - start:.1f}s")


if __name__ == "__main__":
    snapshot_demo()
    prov_demo()
    agent_demo()
    auditor_demo()
    print("smoke test passed")
