"""Scoring one auditor answer against the ground truth (analysis/schema.md)."""


def score(answer: dict | None, truth: dict | None, record: str) -> dict:
    """truth is the content of truth.json, or None for a clean run. A sham run has truth["fault_type"] == "sham"."""
    parse_ok = answer is not None
    pred_step = answer["step_id"] if parse_ok else None
    row = {"parse_ok": int(parse_ok), "pred_step": pred_step, "pred_cat": answer["fault_class"] if parse_ok else "",
           "pointer_ok": int(parse_ok and answer["pointer"] != "" and answer["pointer"] in record)}

    is_control = truth is None or truth["fault_type"] == "sham"
    if is_control:                                       # the right answer is: no step, class none
        said_clean = parse_ok and pred_step is None and answer["fault_class"] == "none"
        return {**row, "is_control": 1, "true_step": None, "exact": None, "within3": None, "false_alarm": int(not said_clean)}

    k = truth["k"]
    return {**row, "is_control": 0, "true_step": k, "false_alarm": None,
            "exact": int(pred_step == k),
            "within3": int(pred_step is not None and abs(pred_step - k) <= 3)}


def position_only_guess(n_steps: int, other_runs: list) -> int:
    """A guesser that never sees the record: it names the step at the most common relative position of k.

    other_runs = [(k, n_steps), ...] from the OTHER tasks, so the tested task is left out.
    """
    tenths = [min(9, 10 * k // n) for k, n in other_runs]            # relative position of k, in tenths of the run
    most_common = max(set(tenths), key=lambda t: (tenths.count(t), -t))
    guess = round((most_common + 0.5) / 10 * n_steps)
    return max(2, guess - guess % 2)                                 # faults sit on act steps, and act steps have even numbers


def signature(event) -> tuple:
    """What a step looks like when every text is hidden: kind, tool, which state paths it touched, which arguments are null."""
    if event.tool_call is None:
        return ("think",)
    touched = tuple((op["op"], op["path"].split("/")[1]) for op in event.state_patch[1:])
    null_args = tuple(sorted(a for a, v in event.tool_call.args.items() if v is None))
    return ("act", event.tool_call.name, touched, null_args, "error" in event.tool_return)


def structure_only_guess(events: list) -> int:
    """A guesser that sees the structure of the record but no text: it names the step whose signature is
    rarest among the steps of the same tool. Ties go to the earliest step."""
    acts = [e for e in events if e.tool_call]
    def rarity(event):
        same_tool = [signature(e) for e in acts if e.tool_call.name == event.tool_call.name]
        return same_tool.count(signature(event)) / len(same_tool)
    return min(acts, key=lambda e: (rarity(e), e.step_id)).step_id


def rule_audit(events: list):
    """One simple rule auditor on the event stream: the first write_note step that did not add its own note
    with a source. Returns a step id or None. It needs no model and reads no text."""
    for e in events:
        if e.tool_call and e.tool_call.name == "write_note" and "error" not in e.tool_return:
            key, source = e.tool_call.args.get("key"), e.tool_call.args.get("source_pid")
            added_own_note = any(op["op"] == "add" and op["path"].startswith("/notes/") for op in e.state_patch[1:])
            if not added_own_note or source is None:
                return e.step_id
    return None
