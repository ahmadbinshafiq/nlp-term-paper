"""Tests for the tools, the cache, the fault eligibility rules and the gate. No model is needed."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from auditarch import cache
from auditarch.eligible import FAULT_TYPES, eligible_steps
from auditarch.gate import answers_match, check_clean_run, normalize
from auditarch.schema import Event, empty_state, fold
from auditarch.tools import TOOLS, action_schema


class FakeIndex:
    corpus = {"p1": {"title": "Titanic (1997 film)", "text": "Titanic was directed by James Cameron."},
              "p2": {"title": "James Cameron", "text": "James Cameron was born in Kapuskasing."},
              "p3": {"title": "Avatar", "text": "Avatar is a 2009 film."}}

    def search(self, query, k=3):
        return ["p1", "p2", "p3"][:k]


# ---------- tools ----------

def test_search_returns_handle_title_snippet_and_changes_nothing():
    ret, effect = TOOLS["search"]({"query": "titanic"}, empty_state(), FakeIndex())
    assert ret["results"][0] == {"handle": "p1", "title": "Titanic (1997 film)", "snippet": "Titanic was directed by James Cameron."}
    assert effect == []


def test_read_writes_evidence_and_unknown_handle_is_an_error_not_an_exception():
    ret, effect = TOOLS["read"]({"handle": "p1"}, empty_state(), FakeIndex())
    assert ret["pid"] == "p1" and effect[0]["path"] == "/evidence/p1" and effect[0]["op"] == "add"
    assert TOOLS["read"]({"handle": "nope"}, empty_state(), FakeIndex()) == ({"error": "unknown handle"}, [])


def test_write_note_adds_then_replaces():
    state = empty_state()
    _, effect = TOOLS["write_note"]({"key": "director", "text": "Cameron", "source_pid": "p1"}, state, FakeIndex())
    assert effect == [{"op": "add", "path": "/notes/director", "value": {"text": "Cameron", "source_pid": "p1"}}]
    state["notes"]["director"] = effect[0]["value"]
    _, effect = TOOLS["write_note"]({"key": "director", "text": "x", "source_pid": "p2"}, state, FakeIndex())
    assert effect[0]["op"] == "replace"


def test_finish_copies_the_source_and_never_fails_on_a_missing_note():
    state = empty_state()
    state["notes"]["born"] = {"text": "Kapuskasing", "source_pid": "p2"}
    _, effect = TOOLS["finish"]({"answer": "Kapuskasing", "note_key": "born"}, state, FakeIndex())
    assert effect[1]["value"] == {"note_key": "born", "cited_pid": "p2"}
    ret, effect = TOOLS["finish"]({"answer": "x", "note_key": "gone"}, state, FakeIndex())
    assert ret == {"ok": True} and effect[1]["value"] == {"note_key": "gone", "cited_pid": None}


def test_action_schema_only_allows_the_named_tools():
    schema = action_schema(["search", "finish"])
    assert [one["properties"]["tool"]["enum"] for one in schema["anyOf"]] == [["search"], ["finish"]]
    assert schema["anyOf"][1]["properties"]["args"]["required"] == ["answer", "note_key"]


# ---------- cache ----------

class FakeLlm:
    calls = 0

    def invoke(self, messages, format=None):
        FakeLlm.calls += 1
        return AIMessage(content=f"reply number {FakeLlm.calls}", response_metadata={"prompt_eval_count": 7, "eval_count": 3})


def test_cache_replays_the_same_answer_and_strict_mode_refuses_a_miss(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    pins = {"model_digest": "d", "options": {"temperature": 0}, "ollama_version": "v", "model_tag": "m"}
    first, usage1 = cache.cached_invoke(FakeLlm(), pins, [HumanMessage("hello")])
    again, usage2 = cache.cached_invoke(FakeLlm(), pins, [HumanMessage("hello")])
    assert first == again == "reply number 1"
    assert (usage1["cached"], usage2["cached"]) == (False, True)
    with pytest.raises(RuntimeError):
        cache.cached_invoke(FakeLlm(), pins, [HumanMessage("something new")], strict=True)


def test_cache_key_changes_with_the_options(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    pins = {"model_digest": "d", "options": {"think": False}, "ollama_version": "v", "model_tag": "m"}
    a, _ = cache.cached_invoke(FakeLlm(), pins, [HumanMessage("hi")])
    b, _ = cache.cached_invoke(FakeLlm(), {**pins, "options": {"think": True}}, [HumanMessage("hi")])
    assert a != b


# ---------- a small hand-made clean run: two rounds and a finish ----------

def make_run():
    index, state, events = FakeIndex(), empty_state(), []

    def step(kind, name=None, args=None):
        n = len(events) + 1
        if kind == "think":
            patch = [{"op": "add", "path": f"/scratch/{n}", "value": "plan"}]
            events.append(Event(step_id=n, node_kind="think", tool_call=None, tool_return=None, state_patch=patch))
        else:
            ret, effect = TOOLS[name](args, fold(events)[-1] if events else state, index)
            call = {"name": name, "args": args}
            patch = [{"op": "add", "path": f"/calls/{n}", "value": {"tool_call": call, "tool_return": ret}}] + effect
            events.append(Event(step_id=n, node_kind="act", tool_call=call, tool_return=ret, state_patch=patch))

    for name, args in [("search", {"query": "titanic director"}), ("read", {"handle": "p1"}),
                       ("write_note", {"key": "director", "text": "James Cameron", "source_pid": "p1"}),
                       ("search", {"query": "james cameron born"}), ("read", {"handle": "p2"}),
                       ("write_note", {"key": "born", "text": "Kapuskasing", "source_pid": "p2"}),
                       ("finish", {"answer": "Kapuskasing", "note_key": "born"})]:
        step("think")
        step("act", name, args)
    return events, fold(events)[-1]


GOLD = {"answer": "Kapuskasing", "answer_aliases": [], "supporting_pids": ["p1", "p2"]}


def test_every_fault_can_be_built_in_the_clean_run():
    events, _ = make_run()
    assert eligible_steps(events, "dropped_note") == [6, 12]
    assert eligible_steps(events, "overwritten_note") == [12]      # needs another note before it
    assert eligible_steps(events, "wrong_source") == [12]          # needs another passage read before it
    assert eligible_steps(events, "wrong_argument") == [4, 8, 10]  # read at 4 and 10, second search at 8
    assert all(eligible_steps(events, fault) for fault in FAULT_TYPES)


def test_gate_passes_the_clean_run_and_names_what_is_wrong_otherwise():
    events, app = make_run()
    assert check_clean_run(events, app, "finish", GOLD) == {"failed": [], "flags": []}
    wrong = check_clean_run(events, app, "finish", {**GOLD, "answer": "Toronto", "supporting_pids": ["p3"]})
    assert wrong["failed"] == ["answer_wrong", "cited_pid_not_gold"]
    assert "not_finished:step_cap" in check_clean_run(events[:-2], fold(events[:-2])[-1], "step_cap", GOLD)["failed"]


def test_normalize_and_answer_matching():
    assert normalize("The  Atlantic Ocean.") == "atlantic ocean"
    assert answers_match("2", ["two"])
    assert answers_match("summer or fall", ["usually in the summer or fall"])
    assert not answers_match("1", ["1952"])
    assert not answers_match("", ["1952"])
