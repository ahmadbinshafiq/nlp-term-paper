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
    return max(1, round((most_common + 0.5) / 10 * n_steps))
