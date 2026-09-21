# Fault catalogue (v0.2, 2026-09-20)

Seven rows: six faults in three classes, plus the sham control. Rows 1 and 2 have two variants (a: `search`, b: `read`).
Read `docs/schema.md` first. Status: frozen with the tag `prereg-v1`. All rows were tested on the five development tasks (results/PILOT-NOTES.md).

## Rules that hold for every row

1. **One fault per run.** A clean run is replayed from the cache up to step k-1. At step k the wrapper `FaultyTool(tool, fault, k)` fires once. After k the run goes on live, with the same model and options. Exception: a sham run changes nothing, so every later model call hits the cache and the run replays with no live model call. A cache miss during a sham run is an error and fails the run.
2. **The fault looks like the agent's own mistake.** The record and the message history that the model sees afterwards always agree. An act is one message that holds the agent's JSON action, followed by one `RESULT:` message with the tool return. Rows 1, 5 and 6: the JSON action at step k is rewritten to the changed action (and for row 1 the `RESULT:` message holds the return for the changed call); every message before step k stays byte-identical. Row 2: only the `RESULT:` message of step k changes. Rows 3 and 4: no message changes (the agent sees `RESULT: {"ok": true}`), only the state. Reason: `docs/schema.md` says that nothing lives only in chat messages. If the history kept the original call while the record shows the changed one, the record could no longer explain what the agent did next. The original values go only into `truth.json`, which no model ever sees.
3. **Ground-truth step = k**, the step where the wrapper fired. This holds even if the visible damage shows up later.
4. **Every choice is fixed by a rule**, never random. So the same (task, fault) always gives the same run.
5. **How k and the hook tool are set.**
   - Let i be the position of the task in its pool in seed order (from 0) and j the row number (1 to 7).
   - Rows 1 and 2: the hook tool is `search` if i + j is even, else `read`. If that variant is not reachable in this run, the other one is used.
   - Eligible steps = the act steps of the hook tool in the clean run that meet the column "Reachable if", sorted: e[0] ... e[m-1]. A call that the tool refused (it returned an error and changed nothing) is never eligible. The rules are coded in `code/auditarch/eligible.py`.
   - Stratum s = (i + j) mod 3, with 0 = early, 1 = middle, 2 = late. Then **k = e[floor((2s + 1) x m / 6)]**. This gives positions 0, 1, 1 for m = 2; 0, 1, 2 for m = 3; 0, 2, 3 for m = 4; 1, 3, 5 for m = 6.
   - `k_bin` of the chosen step with rank r is floor(3 x (r + 0.5) / m). It stores the part the step really lies in, which can differ from s when m is small.
   - Sweep tasks always have m >= 1 for every row, because the gate demands it (pre-registration, section 3, check 5).
   - Validation runs: all six faults are planted into all five development tasks (30 runs), with k from the same formula, plus one sham per task. This is simpler than a special rule for validation and gives 5 runs per fault.
   - Sham (row 7): k = the middle eligible `write_note` step, e[floor(m / 2)].
6. **Proof that only the fault differs.** The record of a faulty run is byte-identical to the clean run on every line before step k. For the sham row, `events.jsonl` and every rendering are byte-identical to the clean run on every line; only `truth.json` differs. Both are checked on every run.
7. **`truth.json`** holds: `fault_type`, `fault_class`, k, `k_bin`, `hook_tool`, original value, changed value, and these flags, which are reported and never used to drop runs: `answer_changed`, `ended` (`finish`, `step_cap`, or `failed_step` if an action was cut off before it was complete), `finish_note_missing`, `requeried_after_k` and `reread_after_k` (a search or a read after k was refused by the tool as a repeat). The natural patterns of a run (the same query tried twice, a read of a handle no search returned, a plan that does not match the act) are computed from `events.jsonl` at analysis time.
8. **The plain tools never raise.** `finish` is always the last step. If `notes[note_key]` does not exist, `finish` still returns `ok` and writes `decision = {note_key, cited_pid: null}`. This is the plain tool's behaviour in clean runs too, so the wrapper changes step k only. `search` returns the 5 best passages as `{handle, title, snippet}`, so the agent (and the auditor) can see what a search found. The plain tools refuse a repeated query, a second read of the same passage and an existing note key: they return `{"error": ...}` and change nothing. The fault wrapper goes around these refusals where a row needs it (rows 1a and 4): it builds the return and the state effect itself. (Decisions D-005 and D-009.)

## The rows

| # | Code (`fault_type`) | Class | Hook tool | Exact operation at step k | Reachable if |
|---|---|---|---|---|---|
| 1a | `wrong_argument` | `tool` | `search` | The query is replaced by the agent's own previous search query (a stale query). The wrapper returns the BM25 results for that query, without the refusal that the plain tool gives for a repeated query. | an earlier `search` step has a different query, and step k-1 is a think step with a non-empty text |
| 1b | `wrong_argument` | `tool` | `read` | The handle is replaced by another handle from the latest search result: rank 2 if the agent asked for rank 1, else rank 1. If that passage was already read before k, the next rank is taken. The tool reads that other passage. | the latest search returned a handle that was not asked for and not read before k, and step k-1 is a think step with a non-empty text |
| 2a | `corrupted_output` | `tool` | `search` | The tool runs on the right query, but the returned handles, titles and snippets are ranks 51-55 instead of ranks 1-5. | always |
| 2b | `corrupted_output` | `tool` | `read` | The tool runs on the right handle. The returned `pid` and `title` stay, but `text` is replaced by the text of the rank-51 passage of the latest search query. `evidence[pid]` stores the wrong text. | there was a search before this read, and this pid was not read before step k |
| 3 | `dropped_note` | `state` | `write_note` | The write is swallowed. The tool still returns `ok`. The patch adds `calls[k]` only, no `notes[key]`. | always |
| 4 | `overwritten_note` | `state` | `write_note` | The text and source are written to the most recently written other key (the wrapper does this itself; the plain tool would refuse an existing key). The key the agent named is not created. The tool returns `ok`. | at least one other note exists |
| 5 | `wrong_source` | `evidence` | `write_note` (`source_pid` only) | `source_pid` is replaced by the pid of the most recently read other passage. Key and text stay. | at least one other passage was read before step k |
| 6 | `no_source` | `evidence` | `write_note` (`source_pid` only) | `source_pid` is set to null. Key and text stay. | always |
| 7 | `sham` | `none` (control row) | `write_note` | The wrapper is engaged at step k but passes call and return through unchanged. | always |

Why "step k-1 is a think step" in row 1: after the call is rewritten, step k agrees with itself (call Y, return for Y). The only trace of the fault is that the think text just before says X. Without that think step the fault could not be found from the record at all.

Why there is no hook on `finish`: `finish` copies `cited_pid` from the note. So a bad source on a note reaches the final claim by itself. A hook on `finish` would always sit on the last step and hand the position guesser a free cue.

## What each format should show (the predictions behind the hypothesis)

Format codes: `log`, `diff`, `prov`. All three hold the same information; the question is only where the eye has to go.

| # | Fault | Visible at step k? | `log` | `diff` | `prov` | Predicted best |
|---|---|---|---|---|---|---|
| 1 | `wrong_argument` | yes, against step k-1 | The think line at k-1 and the call at k are adjacent plain lines: "said X, called Y". | Same neighbours (the think text is in the patch of step k-1), but the call is wrapped in a patch operation, one level deeper. | The call is an attribute of activity k; the think text is another node. | `log` |
| 2 | `corrupted_output` | yes | Call and return are adjacent: a query against unrelated titles, or a title against unrelated text. | Same content inside the `calls[k]` value, and again in `evidence[pid]`. | Return text is an attribute of an entity; the mismatch is inside one node. | `log` |
| 3 | `dropped_note` | yes | Step k has no `effect:` line, while every other `write_note` step has one. | Step k is the only `write_note` step whose patch has no `/notes/...` operation. | Activity k generates no note entity. | `diff` |
| 4 | `overwritten_note` | yes | The call names key A, the `effect:` line names key B. | Step k shows `replace /notes/B` where every other note step shows `add /notes/<own key>`. | The note entity made at k is a new version of note B, not a new note A. | `diff` |
| 5 | `wrong_source` | yes, against the read steps | `source_pid` is one string among many; one must search back for where the text was read. | Same: one string inside `notes[key]`. | The `wasDerivedFrom` edge is `source_pid` drawn as an edge. It puts the note next to the passage entity and its text, so the text check needs no search back. There is no separate `used` edge on a `write_note` step. | `prov` |
| 6 | `no_source` | yes | `source_pid: null` in the call. | `source_pid: null` in `notes[key]`. | The note entity has no `wasDerivedFrom` edge, while every other note has one. `source_pid: null` is also an attribute of activity k (needed for the round trip). | `prov` |
| 7 | `sham` | nothing to see | identical to the clean run | identical | identical | none: the right answer is "no fault" |

**How the log shows effects.** After each act step the log prints one effect line per patch operation other than `/calls/<k>`, for example `effect: ["add", "/notes/director"]`. The value is added when it is not already visible in the call or return line of the same step (layout: `code/auditarch/render/log.py`). The layout was settled by the round-trip test only, never by auditor accuracy per format.

**PROV edge rules** (also in `docs/schema.md`): a `read` step gets `used(step:k, passage:<pid>)`; the passage entity carries the title and text that the read returned. A `write_note` step gets `wasGeneratedBy(note, step:k)` plus `wasDerivedFrom(note, passage)` built from `source_pid`, and no `used` edge. A `finish` step gets `wasDerivedFrom(answer, note)` built from `note_key`. Any edge that is not in the event stream would be an inferred edge; those belong to the fourth arm only.

**Honest notes.**
- Row 1a can be found by a one-line rule too: in a clean run a repeated query is always refused with an error, so a repeated query that returns results marks the fault. It is reported with the rule baselines, like rows 3, 4 and 6.
- Rows 3, 4 and 6 (and maybe 5) can be found by a one-line rule on the structure, without reading any text. The pre-registration therefore reports a structure-only guesser and one rule auditor as baselines for these rows (section 7, control 3).
- Row 6 may be near ceiling in all three formats. It is part of the week-4 floor/ceiling check per fault type.
- Four of six faults hook `write_note`, which is only about 3 to 4 of about 22 steps. A guesser that picks a random `write_note` step therefore scores far above uniform chance. This "tool-prior baseline" is the reference for the structure-only guesser.

## Scoring of the control rows

Clean and sham runs have no faulty step. The right auditor answer is `step_id: null`, `fault_class: none`. `false_alarm` = 1 unless the answer parsed and said exactly that; an answer that cannot be parsed counts as a false alarm.
The sham is a pipeline check: the hash of each sham rendering equals the hash of the same rendering of its clean run. Clean controls are the first 25 sweep tasks in seed order, sham controls the last 20. One false-alarm rate per format is reported over all distinct no-fault tasks (a task in both sets counts once).

## Open points (decide before `prereg-v1`, log each in `DECISIONS.md`)

None. Rank 51 (rows 2a, 2b) stays: `corrupted_output` was neither at 0 nor at 100 percent on the development runs.

Closed in v0.1: hidden faults in clean runs (now gate check 4, D-006); message history (rule 2); how the log shows effects (rule above).
Closed in v0.2: the agent thinks before every act step (built that way in week 2); rule 2 rewritten for JSON actions; rows 1a, 2a and 4 adapted to tools that refuse repeats and to 5 search results.
