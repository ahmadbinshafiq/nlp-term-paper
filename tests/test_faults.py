"""The fault injector on the small hand-made run (two rounds and a finish). No model is needed."""

import pytest

from auditarch import faults
from auditarch.eligible import FAULT_TYPES
from auditarch.faults import choose_k, plant
from auditarch.schema import fold
from test_agent_parts import FakeIndex, make_run

EVENTS, _ = make_run()          # steps: 2 search, 4 read p1, 6 note director, 8 search, 10 read p2, 12 note born, 14 finish


def planted(fault_type, k, monkeypatch):
    monkeypatch.setattr(faults, "JUNK_RANK", 2)                      # the fake index has only three passages
    state_before = fold(EVENTS[: k - 1])[-1]
    return plant(fault_type, EVENTS[k - 1].tool_call.model_dump(), state_before, FakeIndex())


def test_wrong_argument_on_search_sends_the_stale_query_and_is_not_refused(monkeypatch):
    call, ret, effect = planted("wrong_argument", 8, monkeypatch)
    assert call["args"]["query"] == "titanic director" and "results" in ret and effect == []


def test_wrong_argument_on_read_reads_another_unread_result(monkeypatch):
    call, ret, effect = planted("wrong_argument", 10, monkeypatch)
    assert call["args"]["handle"] == "p3" and ret["pid"] == "p3"     # asked for p2; p1 was read before
    assert effect[0]["path"] == "/evidence/p3"


def test_corrupted_read_keeps_pid_and_title_but_stores_another_text(monkeypatch):
    call, ret, effect = planted("corrupted_output", 10, monkeypatch)
    assert call == EVENTS[9].tool_call.model_dump()                  # the call itself is untouched
    assert ret["pid"] == "p2" and ret["title"] == "James Cameron" and ret["text"] == "Avatar is a 2009 film."
    assert effect[0]["value"]["text"] == ret["text"]                 # the state stores what the agent saw


def test_corrupted_search_returns_other_results(monkeypatch):
    _, ret, _ = planted("corrupted_output", 8, monkeypatch)
    assert [r["handle"] for r in ret["results"]] == ["p3"]


def test_dropped_note_says_ok_and_changes_nothing(monkeypatch):
    call, ret, effect = planted("dropped_note", 12, monkeypatch)
    assert ret == {"ok": True} and effect == []


def test_overwritten_note_replaces_the_other_note(monkeypatch):
    _, ret, effect = planted("overwritten_note", 12, monkeypatch)
    assert ret == {"ok": True}
    assert effect == [{"op": "replace", "path": "/notes/director", "value": {"text": "Kapuskasing", "source_pid": "p2"}}]


def test_wrong_source_and_no_source_change_only_the_source(monkeypatch):
    call, _, effect = planted("wrong_source", 12, monkeypatch)
    assert call["args"]["source_pid"] == "p1" and effect[0]["value"] == {"text": "Kapuskasing", "source_pid": "p1"}
    call, _, effect = planted("no_source", 12, monkeypatch)
    assert call["args"]["source_pid"] is None and effect[0]["path"] == "/notes/born"


def test_sham_is_the_plain_tool(monkeypatch):
    call, ret, effect = planted("sham", 12, monkeypatch)
    assert (call, ret, effect[0]["op"]) == (EVENTS[11].tool_call.model_dump(), {"ok": True}, "add")


def test_choose_k_follows_the_catalogue_formula():
    # dropped_note is row 3 and can sit on steps [6, 12] (m = 2). Stratum = (position + 3) mod 3.
    assert [choose_k(EVENTS, "dropped_note", pos)["k"] for pos in (0, 1, 2)] == [6, 12, 12]
    assert choose_k(EVENTS, "dropped_note", 0)["k_bin"] == 0 and choose_k(EVENTS, "dropped_note", 1)["k_bin"] == 2
    # wrong_argument is row 1: search variant when position + 1 is even, else read
    assert choose_k(EVENTS, "wrong_argument", 1)["k"] == 8           # the only eligible search step
    assert choose_k(EVENTS, "wrong_argument", 0)["k"] in (4, 10)     # a read step
    assert choose_k(EVENTS, "sham", 0)["k"] == 12                    # the middle write_note step


@pytest.mark.parametrize("fault_type", FAULT_TYPES)
def test_every_fault_can_be_chosen_and_planted(fault_type, monkeypatch):
    k = choose_k(EVENTS, fault_type, 0)["k"]
    call, ret, effect = planted(fault_type, k, monkeypatch)
    assert call["name"] == EVENTS[k - 1].tool_call.name and isinstance(ret, dict) and isinstance(effect, list)
