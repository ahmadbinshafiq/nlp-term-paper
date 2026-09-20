"""The agent: a LangGraph loop of think -> act -> think -> act ... until `finish`.

Every node execution becomes one canonical event (docs/schema.md):
  think: the model writes a short plan, no tool.          patch: scratch[step_id]
  act:   the model writes one JSON action; the tool runs.  patch: calls[step_id] + the tool's state effect

The agent works in rounds of three acts: search, read, write_note. After a note it may
start a new round or finish. NEXT_TOOLS below is the whole rule. Ollama forces each
action to fit a JSON schema of the allowed tools, so an act can never be malformed.
"""

import copy
import json
import operator
from typing import Annotated, TypedDict

import jsonpatch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from auditarch.cache import cached_invoke
from auditarch.schema import Event, empty_state
from auditarch.tools import TOOLS, action_schema

STEP_CAP = 38   # 6 rounds of 6 steps, plus think and finish

SYSTEM_PROMPT = """You answer a question that needs several facts chained together.
You can only learn facts through the tools. Do not answer from memory.

Tools:
- search(query): returns the 5 best passages, each with handle, title and the first words of its text.
- read(handle): returns the full text of one passage and its pid.
- write_note(key, text, source_pid): saves one fact. source_pid is the pid of the passage the fact came from.
- finish(answer, note_key): gives the final answer. note_key is the key of the note that holds the final fact.

You work in rounds, one fact per round: 1. search, 2. read one of the results, 3. write_note.
A fact is often inside a passage about something else, so read the result whose text fits best.
In write_note, write the fact you found (or that the passage did not help). Use a new key for every note.
Never send the same search query twice.
The final answer must be short (a name, a place, a date or a number), copied from a note.

You work in turns. In a THINK turn you write one to three sentences.
In an ACT turn you write one JSON action: {"tool": ..., "args": {...}}."""

# Which tools the agent may call next, given the tool it called last.
NEXT_TOOLS = {None: ["search"], "search": ["read"], "read": ["write_note"], "write_note": ["search", "finish"]}

# What the THINK turn is asked, given the tool it called last. It names the act that comes next.
THINK_CUES = {
    None: "Your next act is search. Split the question into a chain of simple facts, then say what you will search for first.",
    "search": "Your next act is read. Say which one of the results you will read, and why. "
              "If no title fits, pick the result whose text is closest: the fact may be inside it.",
    "read": "Your next act is write_note. Say which fact from the passage you just read you will save, "
            "or that the passage did not help.",
    "write_note": "Look at your notes. If they already give the final answer to the question, your next act is finish: "
                  "say the short answer and the key of the note that holds it. "
                  "If not, your next act is search: say which single fact you need next and what you will search for.",
}


class RunState(TypedDict):
    messages: Annotated[list, operator.add]   # chat history the model sees
    events: Annotated[list, operator.add]     # the canonical event stream (the record)
    usage: Annotated[list, operator.add]      # tokens and seconds per model call
    app: dict                                 # application state: scratch, calls, evidence, notes, answer, decision
    step_id: int
    last_tool: str | None                     # the last tool that ran without an error
    ended: str                                # "" while running, then "finish" or "step_cap"


def apply_patch(app: dict, patch: list) -> dict:
    return jsonpatch.apply_patch(copy.deepcopy(app), patch)


def build_agent(thinker, actor, index, strict: bool = False):
    """Returns a compiled LangGraph.

    thinker and actor are (llm, pins) pairs from make_llm. They can be the same pair, or the
    thinker can have thinking switched on while the actor has it off (rule D-003b).
    `strict` means replay from the cache only.
    """

    def think(state: RunState):
        step = state["step_id"] + 1
        cue = HumanMessage("THINK turn. " + THINK_CUES[state["last_tool"]])
        text, usage = cached_invoke(*thinker, state["messages"] + [cue], strict=strict)
        patch = [{"op": "add", "path": f"/scratch/{step}", "value": text}]
        event = Event(step_id=step, node_kind="think", tool_call=None, tool_return=None, state_patch=patch)
        return {"messages": [cue, AIMessage(text)], "events": [event], "usage": [usage],
                "app": apply_patch(state["app"], patch), "step_id": step}

    def act(state: RunState):
        step = state["step_id"] + 1
        allowed = NEXT_TOOLS[state["last_tool"]]
        cue = HumanMessage("ACT turn. Write one JSON action. Allowed tools: " + ", ".join(allowed) + ".")
        text, usage = cached_invoke(*actor, state["messages"] + [cue], schema=action_schema(allowed), strict=strict)

        action = json.loads(text)                       # valid because the schema was enforced (actor has thinking off)
        tool_call = {"name": action["tool"], "args": action["args"]}
        tool_return, effect = TOOLS[tool_call["name"]](tool_call["args"], state["app"], index)

        # The recorder copies the call and its return into the state, so the patch alone carries everything.
        patch = [{"op": "add", "path": f"/calls/{step}", "value": {"tool_call": tool_call, "tool_return": tool_return}}] + effect
        event = Event(step_id=step, node_kind="act", tool_call=tool_call, tool_return=tool_return, state_patch=patch)
        result = HumanMessage("RESULT: " + json.dumps(tool_return, ensure_ascii=False))
        return {"messages": [cue, AIMessage(text), result], "events": [event], "usage": [usage],
                "app": apply_patch(state["app"], patch), "step_id": step,
                "last_tool": state["last_tool"] if "error" in tool_return else tool_call["name"],
                "ended": "finish" if tool_call["name"] == "finish" else ""}

    def after_act(state: RunState):
        if state["ended"]:
            return END
        return "think" if state["step_id"] < STEP_CAP else "cap"

    graph = StateGraph(RunState)
    graph.add_node("think", think)
    graph.add_node("act", act)
    graph.add_node("cap", lambda state: {"ended": "step_cap"})
    graph.add_edge(START, "think")
    graph.add_edge("think", "act")
    graph.add_conditional_edges("act", after_act, ["think", "cap", END])
    graph.add_edge("cap", END)
    return graph.compile()


def run_task(agent, question: str) -> RunState:
    start = {"messages": [SystemMessage(SYSTEM_PROMPT), HumanMessage("Question: " + question)],
             "events": [], "usage": [], "app": empty_state(), "step_id": 0, "last_tool": None, "ended": ""}
    return agent.invoke(start, {"recursion_limit": 4 * STEP_CAP})
