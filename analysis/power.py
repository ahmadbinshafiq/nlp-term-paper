"""What can this study detect? Runs the whole decision tree on simulated data sets (pre-registration, section 5).

Needs analysis/sim/power_*.csv (simulate.py) and analysis/sim/p_power_*.csv (primary.R). Writes prereg/power.md.
Run:  uv run python analysis/power.py
"""

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FORMATS, CLASSES = ["log", "diff", "prov"], ["tool", "state", "evidence"]
PREDICTED = {"tool": 0, "state": 1, "evidence": 2}          # index of the predicted format in FORMATS
SETTINGS = ["null", "null_task_format", "margin10", "margin15", "margin20"]
BOUNDS = [0.10, 0.15, 0.20]


def task_table(df: pd.DataFrame) -> np.ndarray:
    """acc[task, class, format]: share of exact answers. The simulated design is balanced, so task means can be averaged."""
    t = df.pivot_table(index="task_id", columns=["fault_class", "format"], values="exact", aggfunc="mean")
    return np.stack([[t[(c, f)].to_numpy() for f in FORMATS] for c in CLASSES], axis=0).transpose(2, 0, 1)


def class_margins(acc: np.ndarray) -> np.ndarray:
    """acc[..., class, format] -> margin per class: predicted format minus the mean of the other two."""
    out = []
    for c, best in enumerate(PREDICTED.values()):
        others = [f for f in range(3) if f != best]
        out.append(acc[..., c, best] - acc[..., c, others].mean(axis=-1))
    return np.stack(out, axis=-1)


def one_data_set(df: pd.DataFrame, p: float, rng) -> dict:
    tasks = task_table(df)
    acc = tasks.mean(axis=0)
    margin = class_margins(acc)
    draws = tasks[rng.integers(0, len(tasks), size=(500, len(tasks)))].mean(axis=1)       # 500 resamples of tasks
    boot = class_margins(draws)
    lo95, lo90, hi90 = np.quantile(boot, 0.025, axis=0), np.quantile(boot, 0.05, axis=0), np.quantile(boot, 0.95, axis=0)
    best_in_class = [acc[c].argmax() == b and (acc[c] == acc[c].max()).sum() == 1 for c, b in enumerate(PREDICTED.values())]
    meets = [(margin[c] >= 0.10) and (lo95[c] > 0) and best_in_class[c] for c in range(3)]

    pooled, pooled_draws = acc.mean(axis=0), draws.mean(axis=1)
    top = int(pooled.argmax())
    dominates = all(acc[c].argmax() == top for c in range(3)) and all(
        np.quantile(pooled_draws[:, top] - pooled_draws[:, f], 0.025) > 0 for f in range(3) if f != top)

    result = {"half_width": float(np.mean((np.quantile(boot, 0.975, axis=0) - lo95) / 2)), "meets": sum(meets)}
    for bound in BOUNDS:
        if dominates:
            label = "one format dominates"
        elif p < 0.05:
            label = {3: "confirmed", 2: "partly confirmed", 1: "partly confirmed", 0: "another interaction"}[sum(meets)]
        elif all(lo90 > -bound) and all(hi90 < bound):
            label = "null"
        else:
            label = "underpowered"
        result[f"label_{bound}"] = label
    return result


def main():
    rng = np.random.default_rng(0)
    lines = ["# Power: what this study can detect (simulation)", "",
             "Made by `analysis/simulate.py`, `analysis/primary.R` and `analysis/power.py`. 200 simulated data sets per setting, 50 tasks, "
             "6 faulty runs per task, 3 formats. Accuracy per class as on the validation runs with Qwen (tool 0.70, state 0.85, evidence 0.95); "
             "task SD 0.5 and run SD 1.0 on the logit scale. Bootstrap: 500 resamples here (2,000 in the real analysis).", ""]
    summary = {}
    for name in SETTINGS:
        data = pd.read_csv(HERE / "sim" / f"power_{name}.csv")
        p = pd.read_csv(HERE / "sim" / f"p_power_{name}.csv").set_index("dataset").p_interaction
        results = [one_data_set(d, p[k], rng) for k, d in data.groupby("dataset")]
        summary[name] = {"significant": float(np.mean(p < 0.05)), "half_width": float(np.mean([r["half_width"] for r in results])),
                         "labels": {b: Counter(r[f"label_{b}"] for r in results) for b in BOUNDS}, "n": len(results)}

    lines += ["## The interaction test", "", "| Setting | Share of data sets with a significant interaction |", "|---|---|"]
    names = {"null": "no effect", "null_task_format": "no effect, but tasks differ in which format suits them",
             "margin10": "true margins 10 points", "margin15": "true margins 15 points", "margin20": "true margins 20 points"}
    lines += [f"| {names[s]} | {summary[s]['significant']:.2f} |" for s in SETTINGS]
    lines += ["", "The first two rows are false-positive rates and should be near 0.05.", "",
              f"Mean half-width of a 95 percent interval of one margin: {100 * summary['null']['half_width']:.1f} points.", ""]
    for bound in BOUNDS:
        labels = ["confirmed", "partly confirmed", "another interaction", "one format dominates", "null", "underpowered"]
        lines += [f"## Chance of each outcome label, with equivalence bound B = {int(100 * bound)} points", "",
                  "| Setting | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
        for s in SETTINGS:
            counts = summary[s]["labels"][bound]
            lines.append(f"| {names[s]} | " + " | ".join(f"{counts[label] / summary[s]['n']:.2f}" for label in labels) + " |")
        lines.append("")
    chosen = next((b for b in BOUNDS if summary["null"]["labels"][b]["null"] / summary["null"]["n"] >= 0.80), None)
    chance = summary["null"]["labels"][chosen or 0.20]["null"] / summary["null"]["n"]
    lines += ["## The bound B (rule of the pre-registration, section 5)", "",
              f"B = {int(100 * (chosen or 0.20))} points. With true margins of 0, the label \"null\" comes out in {chance:.2f} of the data sets."
              + ("" if chosen else " No bound reached 0.80, so B = 20 and a null result was unlikely to be reachable.")]
    (HERE.parent / "prereg" / "power.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-3:]))


if __name__ == "__main__":
    main()
