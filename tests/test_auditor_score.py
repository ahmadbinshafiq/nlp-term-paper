from auditarch.auditor import ANSWER_SCHEMA, READING_NOTES, SHARED_PROMPT, prompt_for, prompt_hash
from auditarch.score import position_only_guess, score

TRUTH = {"fault_type": "wrong_source", "k": 12}
RIGHT = {"step_id": 12, "fault_class": "evidence", "fault_type": "wrong_source", "pointer": "source_pid"}


def test_reading_notes_differ_in_length_by_at_most_20_percent():
    lengths = [len(note) for note in READING_NOTES.values()]
    assert max(lengths) <= 1.2 * min(lengths), lengths


def test_reading_notes_name_no_fault():
    for note in READING_NOTES.values():
        for fault in ANSWER_SCHEMA["properties"]["fault_type"]["enum"][:-1]:
            assert fault not in note and fault.replace("_", " ") not in note


def test_each_format_has_its_own_prompt_hash_and_the_shared_part_is_the_same():
    assert len({prompt_hash(fmt) for fmt in READING_NOTES}) == 3
    assert all(prompt_for(fmt, "x").startswith(SHARED_PROMPT) for fmt in READING_NOTES)


def test_scoring_a_faulty_run():
    assert score(RIGHT, TRUTH, "... source_pid ...") | {} == {"parse_ok": 1, "pred_step": 12, "pred_cat": "evidence", "pointer_ok": 1,
                                                             "is_control": 0, "true_step": 12, "false_alarm": None, "exact": 1, "within3": 1}
    near = score({**RIGHT, "step_id": 14}, TRUTH, "")
    assert (near["exact"], near["within3"], near["pointer_ok"]) == (0, 1, 0)
    assert score({**RIGHT, "step_id": None}, TRUTH, "")["exact"] == 0
    unparsed = score(None, TRUTH, "")
    assert (unparsed["parse_ok"], unparsed["exact"], unparsed["within3"]) == (0, 0, 0)       # never dropped, counted as wrong


def test_scoring_a_control_run():
    clean = {"step_id": None, "fault_class": "none", "fault_type": "none", "pointer": ""}
    assert score(clean, None, "")["false_alarm"] == 0
    assert score(RIGHT, None, "")["false_alarm"] == 1
    assert score(None, {"fault_type": "sham", "k": 12}, "")["false_alarm"] == 1              # an answer that cannot be read is a false alarm
    assert score(clean, None, "")["exact"] is None


def test_position_only_guesser_uses_the_other_tasks():
    assert position_only_guess(20, [(12, 20), (12, 20), (4, 20)]) == 12                      # most k sit at 60 percent of the run; act steps are even
    assert 1 <= position_only_guess(26, [(18, 32)]) <= 26


def test_structure_only_guesser_and_rule_auditor_find_the_structural_faults():
    import sys; sys.path.insert(0, "tests")
    from test_render import RUNS
    from auditarch.score import rule_audit, structure_only_guess
    assert rule_audit(RUNS["clean"]) is None
    for fault in ("dropped_note", "overwritten_note", "no_source"):          # their cue is pure structure
        assert rule_audit(RUNS[fault]) == 12
        # the hand-made run has only two notes, so "rarest among the notes" is a tie and the earliest wins
        assert structure_only_guess(RUNS[fault]) in (6, 12)
    assert rule_audit(RUNS["wrong_source"]) is None                           # needs the text: a rule cannot see it
