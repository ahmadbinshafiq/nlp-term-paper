"""The auditor: a model reads the record of one run and names the faulty step.

The same shared prompt is used for every format. Each format adds one short reading note that explains
only how the record is written (what a line, an operation, a node and an edge are). A reading note names
no fault and no check (pre-registration, section 2).
"""

import hashlib
import json

from langchain_core.messages import HumanMessage

from auditarch.cache import cached_invoke

SHARED_PROMPT = """You are an auditor. Below is the record of one run of a question-answering agent.

The agent works in steps. A think step writes a short plan. An act step calls one tool:
- search(query) returns 5 passages (handle, title, first words of the text).
- read(handle) returns one passage (pid, title, text) and stores it as evidence.
- write_note(key, text, source_pid) stores a note. source_pid names the passage the fact came from.
- finish(answer, note_key) gives the final answer and cites the source of that note.
A tool may refuse a call with an error, for example a repeated query. A refusal is normal. It is not a fault.

At most one fault was planted in this run, at exactly one act step. The six possible faults:
- wrong_argument (class tool): the tool was called with another argument than the plan just before it said.
- corrupted_output (class tool): the tool returned something that does not fit the call.
- dropped_note (class state): a write_note step returned ok, but no note was stored.
- overwritten_note (class state): a write_note step stored its text under another key that already existed.
- wrong_source (class evidence): a note names a source passage that its text did not come from.
- no_source (class evidence): a note has no source passage.
Many runs are clean, with no fault at all. Report a fault only if the record clearly shows it.
If nothing is clearly wrong, the right answer is: step_id null, fault_class none, fault_type none.

Name the first step where something went wrong, not the step where it was noticed.
Answer with JSON: analysis (two or three sentences: what you checked and what you found), step_id (the number
of the faulty step, or null if the run is clean), fault_class (tool, state, evidence, or none), fault_type
(one of the six names, or none), pointer (a short piece copied from the record that shows the fault; empty if clean)."""

READING_NOTES = {
    "log": "The record is an event log. Each block starts with `step N | think` or `step N | act | tool`. "
           "A think block has one `text:` line. An act block has a `call:` line with the arguments, a `return:` line with "
           "what the tool gave back, and one `effect:` line for every change the step made to the stored state, written as "
           "[operation, path] or [operation, path, value]. The value is left out when the call or the return already shows it.",
    "diff": "The record is a list of state changes. Each block starts with `## step N (think)` or `## step N (act)`. "
            "Every line below it is one JSON Patch operation with `op` (add or replace), `path` (the place in the stored state) "
            "and `value`. The stored state has the sections scratch (think texts), calls (each tool call together with its "
            "return), evidence (passages that were read), notes, answer and decision.",
    "prov": "The record is a W3C PROV graph in PROV-N notation. `activity(step:N, ...)` is a step; its kind, tool, arguments "
            "and return are attributes. `entity(...)` is a data item: thought:N, passage:<pid>, note:<key>@N or answer:N. "
            "`used(step, passage)` means the step read that passage. `wasGeneratedBy(item, step)` means the step produced "
            "the item. `wasDerivedFrom(a, b)` means that item a names item b as its source.",
}

FAULT_NAMES = ["wrong_argument", "corrupted_output", "dropped_note", "overwritten_note", "wrong_source", "no_source", "none"]
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string"},                  # written first, so the model looks before it decides
        "step_id": {"type": ["integer", "null"]},
        "fault_class": {"type": "string", "enum": ["tool", "state", "evidence", "none"]},
        "fault_type": {"type": "string", "enum": FAULT_NAMES},
        "pointer": {"type": "string"},
    },
    "required": ["analysis", "step_id", "fault_class", "fault_type", "pointer"],
}


def prompt_for(fmt: str, record: str) -> str:
    return SHARED_PROMPT + "\n\nHow to read this record: " + READING_NOTES[fmt] + "\n\nRECORD:\n" + record


def prompt_hash(fmt: str) -> str:
    """One hash per format: the shared prompt plus that format's reading note (frozen at prereg-v1)."""
    return hashlib.sha256(prompt_for(fmt, "").encode("utf-8")).hexdigest()


def audit(llm, pins: dict, fmt: str, record: str) -> dict:
    """One audit call. Returns the parsed answer (or None) plus token counts and seconds."""
    text, usage = cached_invoke(llm, pins, [HumanMessage(prompt_for(fmt, record))], schema=ANSWER_SCHEMA)
    # Ollama shortens a prompt that does not fit, without an error. That must never happen silently.
    assert usage["tokens_in"] + pins["options"]["num_predict"] < pins["options"]["num_ctx"], "record too long for num_ctx"
    try:
        answer = json.loads(text)
    except json.JSONDecodeError:
        answer = None
    return {"answer": answer, **usage}
