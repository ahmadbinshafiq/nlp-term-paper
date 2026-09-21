"""Simulated audit results with a known truth, to test the analysis and to measure what the study can detect.

One data set = N tasks x 6 faulty runs x 3 formats, in the columns of analysis/schema.md that the primary test uses.
The chance of finding the fault is set per fault class (as seen on the validation runs) and then moved by
  - a planted margin: the predicted format is better than the other two in its class,
  - a task effect and a run effect (some tasks and runs are harder),
  - optionally a task-by-format effect (some tasks suit one format), to test the assumption of the main test.

Run:  uv run python analysis/simulate.py        (writes analysis/sim/*.csv)
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "sim"
FORMATS = ["log", "diff", "prov"]
FAULTS = {"wrong_argument": "tool", "corrupted_output": "tool", "dropped_note": "state",
          "overwritten_note": "state", "wrong_source": "evidence", "no_source": "evidence"}
PREDICTED = {"tool": "log", "state": "diff", "evidence": "prov"}
BASE = {"tool": 0.70, "state": 0.85, "evidence": 0.95}     # exact-step accuracy per class on the validation runs (Qwen)
TASK_SD, RUN_SD = 0.5, 1.0                                 # on the logit scale


def logit(p):
    return np.log(p / (1 - p))


def simulate(n_tasks: int, margin: float, seed: int, task_format_sd: float = 0.0) -> pd.DataFrame:
    """margin is in points (0.15 = 15 points): predicted format = base + 2/3 margin, the other two = base - 1/3 margin."""
    rng = np.random.default_rng(seed)
    rows = []
    for t in range(n_tasks):
        task_effect = rng.normal(0, TASK_SD)
        suits = {f: rng.normal(0, task_format_sd) for f in FORMATS}
        for fault_type, fault_class in FAULTS.items():
            run_effect = rng.normal(0, RUN_SD)
            for fmt in FORMATS:
                shift = margin * (2 / 3 if fmt == PREDICTED[fault_class] else -1 / 3)
                p = np.clip(BASE[fault_class] + shift, 0.02, 0.98)
                p = 1 / (1 + np.exp(-(logit(p) + task_effect + run_effect + suits[fmt])))
                rows.append({"task_id": f"t{t}", "run_id": f"t{t}|{fault_type}", "fault_type": fault_type,
                             "fault_class": fault_class, "format": fmt, "exact": int(rng.random() < p)})
    return pd.DataFrame(rows)


def many(n_sets: int, **settings) -> pd.DataFrame:
    return pd.concat([simulate(seed=s, **settings).assign(dataset=s) for s in range(n_sets)])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    simulate(50, 0.0, seed=0).to_csv(OUT / "sim_null.csv", index=False)
    simulate(50, 0.20, seed=0).to_csv(OUT / "sim_effect.csv", index=False)
    settings = {"null": dict(margin=0.0), "null_task_format": dict(margin=0.0, task_format_sd=0.5),
                "margin10": dict(margin=0.10), "margin15": dict(margin=0.15), "margin20": dict(margin=0.20)}
    for name, kwargs in settings.items():
        many(200, n_tasks=50, **kwargs).to_csv(OUT / f"power_{name}.csv", index=False)
        print("wrote", name)
