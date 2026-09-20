"""Each format must turn back into the identical event stream, for clean runs and for every kind of fault."""

import copy

import pytest

from auditarch.render import diff, log, prov
from auditarch.schema import Event, fold, unfold
from test_agent_parts import make_run


def faulty_runs():
    """The clean hand-made run plus one hand-made variant per fault that changes the state effect."""
    clean = [e.model_dump() for e in make_run()[0]]
    runs = {"clean": clean}

    dropped = copy.deepcopy(clean)                       # step 12: the note write is swallowed
    dropped[11]["state_patch"] = dropped[11]["state_patch"][:1]
    runs["dropped_note"] = dropped

    overwritten = copy.deepcopy(clean)                   # step 12: the text lands in the other note
    overwritten[11]["state_patch"][1].update(op="replace", path="/notes/director")
    runs["overwritten_note"] = overwritten

    no_source = copy.deepcopy(clean)                     # step 12: source_pid is null in the call and in the note
    no_source[11]["tool_call"]["args"]["source_pid"] = None
    no_source[11]["state_patch"][0]["value"]["tool_call"]["args"]["source_pid"] = None
    no_source[11]["state_patch"][1]["value"]["source_pid"] = None
    runs["no_source"] = no_source

    corrupted = copy.deepcopy(clean)                     # step 10: the read returns the wrong text
    corrupted[9]["tool_return"]["text"] = "Avatar is a 2009 film."
    corrupted[9]["state_patch"][0]["value"]["tool_return"]["text"] = "Avatar is a 2009 film."
    corrupted[9]["state_patch"][1]["value"]["text"] = "Avatar is a 2009 film."
    runs["corrupted_output"] = corrupted
    return {name: [Event(**e) for e in events] for name, events in runs.items()}


RUNS = faulty_runs()


@pytest.mark.parametrize("name", RUNS)
def test_log_round_trip(name):
    assert log.parse(log.render(RUNS[name])) == RUNS[name]


@pytest.mark.parametrize("name", RUNS)
def test_diff_round_trip(name):
    assert diff.parse(diff.render(RUNS[name])) == RUNS[name]


@pytest.mark.parametrize("name", RUNS)
def test_prov_round_trip(name):
    assert prov.parse(prov.render_json(RUNS[name])) == RUNS[name]


def test_the_three_renderings_differ_and_the_diff_has_no_message_list():
    events = RUNS["clean"]
    texts = [log.render(events), diff.render(events), prov.render(events)]
    assert len(set(texts)) == 3
    assert "messages" not in diff.render(events)


def test_prov_draws_the_source_as_an_edge_and_drops_it_when_the_source_is_null():
    assert "wasDerivedFrom(note:born@12, passage:p2" in prov.render(RUNS["clean"])
    assert "wasDerivedFrom(note:born@12" not in prov.render(RUNS["no_source"])


def test_log_shows_a_missing_effect_as_a_missing_line():
    clean_block = log.render(RUNS["clean"]).split("step 12 |")[1].split("step 13 |")[0]
    dropped_block = log.render(RUNS["dropped_note"]).split("step 12 |")[1].split("step 13 |")[0]
    assert "effect:" in clean_block and "effect:" not in dropped_block


def test_recorded_patches_equal_the_diff_of_consecutive_states():
    """The patch an event carries is the same as the diff between the state before and after (the checkpoint view)."""
    events = RUNS["clean"]
    by_path = lambda ops: sorted(ops, key=lambda op: op["path"])
    for event, patch in zip(events, unfold(fold(events))):
        assert by_path(patch) == by_path(event.state_patch)
