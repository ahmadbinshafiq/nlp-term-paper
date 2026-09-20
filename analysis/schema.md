# Results table: one row per audit call

File: `results/<sweep>/scores.csv`, where `<sweep>` is `pilot-w3`, `validation-w4` or `main`. One row = one auditor answer for one run in one format.
The analysis scripts (`analysis/analyze.py`, `analysis/primary.R`) and the simulated files (`analysis/sim_null.csv`, `analysis/sim_effect.csv`) use exactly these columns.
Codes for `fault_type`, `fault_class` and `format` are the same as in `prereg/fault_catalogue.md`.

| Column | Type | Meaning |
|---|---|---|
| `run_id` | text | `<task_id>|<fault_type>|<k>` for faulty and sham runs, `<task_id>|clean` for clean runs. The key of one audit call is `run_id|format|model_tag`. |
| `task_id` | text | MuSiQue id of the task. |
| `fault_type` | text | `wrong_argument`, `corrupted_output`, `dropped_note`, `overwritten_note`, `wrong_source`, `no_source`, `sham`, `clean`. |
| `fault_class` | text | `tool`, `state`, `evidence`, or `none` for clean and sham runs. |
| `hook_tool` | text | `search`, `read` or `write_note`: the tool the wrapper sat on. Empty for clean runs. |
| `k` | int or empty | Step where the wrapper fired. Filled for faulty and sham runs, empty for clean runs. |
| `k_bin` | int or empty | 0 = early, 1 = middle, 2 = late: the part of the eligible steps that k lies in (catalogue, rule 5). Empty for clean runs. |
| `n_steps` | int | Number of steps in the audited record. |
| `rel_pos` | float or empty | `k / n_steps`. Empty for clean runs. |
| `format` | text | `log`, `diff`, `prov`, `log_inferred` (fourth arm). |
| `arm` | text | `lossless` (the three main formats) or `fourth`. The native recorders are scored in `evidence_present.csv`, not here, unless their LLM audits are run (cut-list item 1); then `arm = native` and `format` is `native_callback`, `native_sqlite` or `native_prov`. |
| `auditor_role` | text | `primary` or `second`. |
| `sample_id` | int | 0 for the single answer. 1 and 2 only if the 3-repeat rule is triggered. |
| `is_control` | 0/1 | 1 for clean and sham runs. |
| `is_development` | 0/1 | 1 for the 5 development tasks (pilot, validation, re-audits). Never in the primary test. |
| `pred_step` | int or empty | The auditor's `step_id`. Empty if it answered null or did not parse. |
| `true_step` | int or empty | Equal to `k` for faulty runs. Empty for clean and sham runs. |
| `exact` | 0/1 or empty | Faulty runs only: 1 if `pred_step` equals `true_step`; 0 otherwise, also if `pred_step` is empty or the answer did not parse. Empty on control rows. The primary outcome. |
| `within3` | 0/1 or empty | Faulty runs only: 1 if `pred_step` is at most 3 steps from `true_step`; 0 if `pred_step` is empty. Empty on control rows. |
| `pred_cat` | text | The auditor's `fault_class`. |
| `true_cat` | text | Equal to `fault_class`. |
| `false_alarm` | 0/1 or empty | Control rows only: 1 unless the answer parsed and had `step_id` null and `fault_class` `none`. An answer that did not parse counts as 1. Empty on faulty runs. |
| `pointer_ok` | 0/1 | 1 if the auditor's pointer names an item that exists in the record it saw. |
| `parse_ok` | 0/1 | 1 if the answer was valid JSON that fits the schema. |
| `tokens_in` | int | `prompt_eval_count` from Ollama. |
| `tokens_out` | int | `eval_count` from Ollama. |
| `bytes_record` | int | Size of the rendered record in bytes (UTF-8). |
| `prompt_hash` | text | sha256 of the shared prompt plus the reading note of this format. |
| `render_hash` | text | sha256 of the rendered record. |
| `model_tag` | text | For example `glm-4.7-flash:q8_0`. |
| `model_digest` | text | Full sha256 digest of the model. |
| `ollama_version` | text | For example `0.33.2`. |
| `think` | text | `off` or `on`. |
| `num_ctx` | int | Context size used for the call. |
| `seconds` | float | Wall time of the call. |

Three columns are new compared with the plan's list (section 1, item 9): `hook_tool`, `n_steps` with `rel_pos`, and `auditor_role`. They were added after the review of 2026-09-20 (DECISIONS.md, D-008).

## Rows used by each analysis

"Primary setting" = `auditor_role == primary`, `think` as frozen at `prereg-v1` (`off` at v0.1), `sample_id == 0`, `is_development == 0`.

- **Primary test:** primary setting, `arm == lossless`, `is_control == 0`. Runs removed by the too-long-record rule are removed in all three formats first.
- **False-alarm control:** primary setting, `arm == lossless`, `is_control == 1`.
- **Fourth-arm contrast:** primary setting, `format` in (`prov`, `log_inferred`), `fault_class == evidence`, `is_control == 0`.
- **Second auditor:** `auditor_role == second`, `arm == lossless`, `think == off`, `sample_id == 0`, `is_development == 0`.
- **Repeat check (only if triggered):** `sample_id` in (0, 1, 2) on the 60-run subsample.
- **Development:** `is_development == 1`. Exploratory pilot and validation audits and the later frozen-prompt re-audits are told apart by their sweep folder, not by `prompt_hash`, because the prompt may be frozen unchanged.
