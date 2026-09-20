# The canonical event (decision zero)

Every agent run is stored as one stream of events in `events.jsonl`, one line per event.
All three record formats (event log, state diffs, PROV graph) are made from this one stream.
So the three formats always carry the same information. Only the shape differs.

## One event = exactly five fields

| Field | Type | Meaning |
|---|---|---|
| `step_id` | int, starts at 1 | Position in the run. The same number appears in the log, the checkpoints and the PROV activities. |
| `node_kind` | `"think"` or `"act"` | The only two kinds of step. |
| `tool_call` | object or null | `{name, args}`. Null on think steps. |
| `tool_return` | object or null | What the tool gave back. Null on think steps. |
| `state_patch` | list | JSON Patch operations: what this step changed in the application state. |

Ground truth about a planted fault lives in `truth.json`, outside the stream. No model ever sees it.

## The two kinds of step

- **think**: the model reasons, no tool is called. The patch touches `scratch[step_id]` only.
- **act**: exactly one tool call. The patch touches `calls[step_id]` plus the state effect of that tool.

Notes and answers are effects of tools. They are not extra kinds of step.

## The four tools

| Tool | Returns | State effect |
|---|---|---|
| `search(query)` | a list of `{handle, title}` (top 3 from BM25) | none |
| `read(handle)` | the passage text | writes `evidence[pid]` |
| `write_note(key, text, source_pid)` | `ok` | writes `notes[key]` |
| `finish(answer, note_key)` | `ok` | writes `answer` and `decision` = `{note_key, cited_pid}` |

`cited_pid` is copied by the tool from the note's `source_pid`. The model never chooses it.
So a wrong source on a note travels to the final claim by itself, and no fault hook is needed on `finish`.
The tools never raise. `finish` is always the last step. If `notes[note_key]` does not exist, `finish` still returns `ok` and writes `decision = {note_key, cited_pid: null}` (decision D-005).

## The application state

Every key is a dict keyed by an id. No lists at the top level (JSON Patch is unreliable on lists, see the plan, section 8, row 5).

```json
{
  "scratch":  {"<step_id>": "text of a think step"},
  "calls":    {"<step_id>": {"tool_call": {}, "tool_return": {}}},
  "evidence": {"<pid>": {"title": "", "text": ""}},
  "notes":    {"<key>": {"text": "", "source_pid": ""}},
  "answer":   null,
  "decision": null
}
```

The recorder copies every tool call and its return into `calls[step_id]`.
So the state patch alone carries every field, and nothing lives only in chat messages.
This is what makes the diff format lossless.

## Ids

- Passage: `ent:passage:<pid>`, where `pid` is the first 12 hex characters of sha1(title + newline + text).
- Note: `ent:note:<key>@<step_id>`.

## PROV edges

- A `read` step: `used(activity k, ent:passage:<pid>)`, and activity k generates the evidence entity.
- A `write_note` step: `wasGeneratedBy(ent:note:<key>@k, activity k)` plus `wasDerivedFrom(note, ent:passage:<source_pid>)`. No `used` edge, and no `wasDerivedFrom` edge if `source_pid` is null.
- Every edge comes from a field of the event stream. An edge that is guessed afterwards is an inferred edge and belongs to the fourth arm only.

## Where faults are planted

The exact rules are in `prereg/fault_catalogue.md`. Short version:

| Fault class | Fault type | Hook | What happens |
|---|---|---|---|
| tool | wrong argument | `search` or `read` step | the tool receives a changed argument |
| tool | corrupted output | `search` or `read` step | the tool's return is changed |
| state | dropped note | `write_note` step | the write is swallowed, `ok` is still returned |
| state | overwritten note | `write_note` step | the text is written to another existing key |
| evidence | wrong source | `write_note` step, `source_pid` only | `source_pid` is set to another passage |
| evidence | no source | `write_note` step, `source_pid` only | `source_pid` is set to null |
| none (control) | sham | `write_note` step | the wrapper is engaged but returns the identical output |

## Three hand-written events

A think step, a read step, and a note step. Values are shortened.

```json
{"step_id": 3, "node_kind": "think", "tool_call": null, "tool_return": null,
 "state_patch": [{"op": "add", "path": "/scratch/3", "value": "I know the film is Titanic. Next: who directed it?"}]}
```

```json
{"step_id": 5, "node_kind": "act",
 "tool_call": {"name": "read", "args": {"handle": "ent:passage:0123abcd4567"}},
 "tool_return": {"pid": "0123abcd4567", "title": "Titanic (1997 film)", "text": "Titanic is a 1997 film directed by James Cameron. ..."},
 "state_patch": [
   {"op": "add", "path": "/calls/5", "value": {"tool_call": {"name": "read", "args": {"handle": "ent:passage:0123abcd4567"}},
                                               "tool_return": {"pid": "0123abcd4567", "title": "Titanic (1997 film)", "text": "Titanic is a 1997 film directed by James Cameron. ..."}}},
   {"op": "add", "path": "/evidence/0123abcd4567", "value": {"title": "Titanic (1997 film)", "text": "Titanic is a 1997 film directed by James Cameron. ..."}}
 ]}
```

```json
{"step_id": 6, "node_kind": "act",
 "tool_call": {"name": "write_note", "args": {"key": "director", "text": "Titanic was directed by James Cameron.", "source_pid": "0123abcd4567"}},
 "tool_return": {"ok": true},
 "state_patch": [
   {"op": "add", "path": "/calls/6", "value": {"tool_call": {"name": "write_note", "args": {"key": "director", "text": "Titanic was directed by James Cameron.", "source_pid": "0123abcd4567"}},
                                               "tool_return": {"ok": true}}},
   {"op": "add", "path": "/notes/director", "value": {"text": "Titanic was directed by James Cameron.", "source_pid": "0123abcd4567"}}
 ]}
```

With the fault "wrong source" planted at step 6, the only difference is `source_pid` in the call, in `calls/6` and in `notes/director`: it names a passage the note did not come from.
