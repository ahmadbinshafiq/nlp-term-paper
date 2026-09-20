import copy

import jsonpatch
import pytest
from pydantic import ValidationError

from auditarch.schema import Event, empty_state, fold, unfold

PASSAGE = {"pid": "0123abcd4567", "title": "Titanic (1997 film)", "text": "Titanic is a 1997 film directed by James Cameron."}
READ_CALL = {"name": "read", "args": {"handle": "ent:passage:0123abcd4567"}}
NOTE_CALL = {"name": "write_note",
             "args": {"key": "director", "text": "Titanic was directed by James Cameron.", "source_pid": "0123abcd4567"}}


def make_events() -> list[Event]:
    """Think, read, write a note: the three hand-written events of docs/schema.md."""
    return [
        Event(step_id=1, node_kind="think", tool_call=None, tool_return=None,
              state_patch=[{"op": "add", "path": "/scratch/1", "value": "Next: who directed Titanic?"}]),
        Event(step_id=2, node_kind="act", tool_call=READ_CALL, tool_return=PASSAGE,
              state_patch=[
                  {"op": "add", "path": "/calls/2", "value": {"tool_call": READ_CALL, "tool_return": PASSAGE}},
                  {"op": "add", "path": "/evidence/0123abcd4567", "value": {"title": PASSAGE["title"], "text": PASSAGE["text"]}},
              ]),
        Event(step_id=3, node_kind="act", tool_call=NOTE_CALL, tool_return={"ok": True},
              state_patch=[
                  {"op": "add", "path": "/calls/3", "value": {"tool_call": NOTE_CALL, "tool_return": {"ok": True}}},
                  {"op": "add", "path": "/notes/director",
                   "value": {"text": NOTE_CALL["args"]["text"], "source_pid": "0123abcd4567"}},
              ]),
    ]


def test_fold_builds_the_state():
    final = fold(make_events())[-1]
    assert final["scratch"] == {"1": "Next: who directed Titanic?"}
    assert final["notes"]["director"]["source_pid"] == "0123abcd4567"
    assert final["answer"] is None


def test_calls_entry_equals_tool_call_and_return_on_every_act_event():
    events = make_events()
    final = fold(events)[-1]
    for event in events:
        if event.node_kind == "act":
            assert final["calls"][str(event.step_id)] == {
                "tool_call": event.tool_call.model_dump(), "tool_return": event.tool_return}


def test_think_events_have_null_tool_fields():
    for event in make_events():
        if event.node_kind == "think":
            assert event.tool_call is None and event.tool_return is None


def test_unfold_is_the_inverse_of_fold():
    states = fold(make_events())
    state = empty_state()
    for patch, expected in zip(unfold(states), states):
        state = jsonpatch.apply_patch(copy.deepcopy(state), patch)
        assert state == expected


def test_think_event_with_a_tool_call_is_rejected():
    with pytest.raises(ValidationError):
        Event(step_id=1, node_kind="think", tool_call=READ_CALL, tool_return=PASSAGE,
              state_patch=[{"op": "add", "path": "/scratch/1", "value": "x"}])


def test_act_event_must_copy_its_call_into_the_state():
    with pytest.raises(ValidationError):
        Event(step_id=1, node_kind="act", tool_call=READ_CALL, tool_return=PASSAGE, state_patch=[])


def test_unknown_field_or_tool_is_rejected():
    with pytest.raises(ValidationError):
        Event(step_id=1, node_kind="think", tool_call=None, tool_return=None, truth="leak",
              state_patch=[{"op": "add", "path": "/scratch/1", "value": "x"}])
    with pytest.raises(ValidationError):
        Event(step_id=1, node_kind="act", tool_call={"name": "delete", "args": {}}, tool_return={},
              state_patch=[{"op": "add", "path": "/calls/1", "value": {}}])


def test_step_ids_must_be_consecutive():
    events = make_events()
    with pytest.raises(ValueError):
        fold([events[0], events[2]])
