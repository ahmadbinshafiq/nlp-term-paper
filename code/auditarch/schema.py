"""The canonical event and the application state (see docs/schema.md).

fold   : events -> list of states (state after each step)
unfold : list of states -> patches (one per step)
The two are inverse to each other. That is what "lossless" means for the diff format.
"""

import copy
from typing import Literal

import jsonpatch
from pydantic import BaseModel, ConfigDict, model_validator

TOOL_NAMES = ("search", "read", "write_note", "finish")


def empty_state() -> dict:
    # Every top-level key is a dict keyed by an id, never a list (JSON Patch is unreliable on lists).
    return {"scratch": {}, "calls": {}, "evidence": {}, "notes": {}, "answer": None, "decision": None}


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Literal["search", "read", "write_note", "finish"]
    args: dict


class Event(BaseModel):
    """One node execution. Exactly five fields."""

    model_config = ConfigDict(extra="forbid")
    step_id: int
    node_kind: Literal["think", "act"]
    tool_call: ToolCall | None
    tool_return: dict | None
    state_patch: list[dict]

    @model_validator(mode="after")
    def check_kind(self):
        paths = [op["path"] for op in self.state_patch]
        if self.node_kind == "think":
            if self.tool_call is not None or self.tool_return is not None:
                raise ValueError("a think event has no tool call and no tool return")
            if paths != [f"/scratch/{self.step_id}"]:
                raise ValueError("a think event touches scratch[step_id] only")
        else:
            if self.tool_call is None or self.tool_return is None:
                raise ValueError("an act event has exactly one tool call and its return")
            if f"/calls/{self.step_id}" not in paths:
                raise ValueError("an act event must copy its tool call into calls[step_id]")
        return self


def fold(events: list[Event]) -> list[dict]:
    """Apply each event's patch in order. Returns the state after every step."""
    states, state = [], empty_state()
    for expected_id, event in enumerate(events, start=1):
        if event.step_id != expected_id:
            raise ValueError(f"step ids must run 1, 2, 3, ...; got {event.step_id} at position {expected_id}")
        state = jsonpatch.apply_patch(copy.deepcopy(state), event.state_patch)
        states.append(state)
    return states


def unfold(states: list[dict]) -> list[list[dict]]:
    """The patch between each state and the one before it. Checked, with a safe fallback."""
    patches, prev = [], empty_state()
    for curr in states:
        patch = jsonpatch.make_patch(prev, curr)
        if patch.apply(copy.deepcopy(prev)) != curr:
            # Rare jsonpatch bug on nested lists: replace every changed top-level key as a whole.
            patch = jsonpatch.JsonPatch(
                [{"op": "replace", "path": f"/{key}", "value": curr[key]} for key in curr if curr[key] != prev[key]]
            )
        patches.append(patch.patch)
        prev = curr
    return patches
