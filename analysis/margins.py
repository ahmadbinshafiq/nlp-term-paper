"""Margins with bootstrap intervals, and the decision tree of the pre-registration (sections 5 and 6)."""

import numpy as np
import pandas as pd

FORMATS = ["log", "diff", "prov"]
PREDICTED = {"tool": "log", "state": "diff", "evidence": "prov"}


def accuracy_table(df: pd.DataFrame) -> pd.DataFrame:
    """Rows: fault class. Columns: format. Values: share of runs where the exact step was found."""
    return df.pivot_table(index="fault_class", columns="format", values="exact", aggfunc="mean")[FORMATS]


def margins(df: pd.DataFrame) -> dict:
    """For each class: accuracy of the predicted format minus the mean of the other two."""
    acc = accuracy_table(df)
    out = {}
    for fault_class, best in PREDICTED.items():
        others = [f for f in FORMATS if f != best]
        out[fault_class] = acc.loc[fault_class, best] - acc.loc[fault_class, others].mean()
    return out


def bootstrap(df: pd.DataFrame, statistic, n_resamples: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Resample TASKS with replacement; all rows of a drawn task come along. Returns one row per resample."""
    rng = np.random.default_rng(seed)
    by_task = {task: rows for task, rows in df.groupby("task_id")}
    tasks = list(by_task)
    draws = []
    for _ in range(n_resamples):
        sample = pd.concat([by_task[t] for t in rng.choice(tasks, size=len(tasks))])
        draws.append(statistic(sample))
    return pd.DataFrame(draws)


def interval(values, level: float):
    low = (1 - level) / 2
    return float(np.quantile(values, low)), float(np.quantile(values, 1 - low))


def decide(df: pd.DataFrame, p_interaction: float, controls_ok: bool, bound: float, n_resamples: int = 2000) -> dict:
    """Walk the decision tree. The first step that applies gives the label."""
    acc, point = accuracy_table(df), margins(df)
    boot = bootstrap(df, margins, n_resamples)
    ci95 = {c: interval(boot[c], 0.95) for c in PREDICTED}
    ci90 = {c: interval(boot[c], 0.90) for c in PREDICTED}
    meets = {c: point[c] >= 0.10 and ci95[c][0] > 0 and acc.loc[c, PREDICTED[c]] > acc.loc[c].drop(PREDICTED[c]).max()
             for c in PREDICTED}

    top = acc.idxmax(axis=1)                                          # best format per class
    one_best = top.nunique() == 1 and all((acc.loc[c] == acc.loc[c].max()).sum() == 1 for c in acc.index)
    dominates = False
    if one_best:
        best = top.iloc[0]
        def leads(sample):                                           # lead of the best format over each other format, all faulty runs pooled
            a = sample.groupby("format").exact.mean()
            return {f: a[best] - a[f] for f in FORMATS if f != best}
        lead = bootstrap(df, leads, n_resamples)
        dominates = all(interval(lead[f], 0.95)[0] > 0 for f in lead.columns)

    significant = p_interaction < 0.05
    if not controls_ok:
        label = "not interpretable"
    elif dominates:
        label = "refuted: one format dominates"
    elif significant:
        label = {3: "confirmed", 2: "partly confirmed", 1: "partly confirmed", 0: "refuted: another interaction"}[sum(meets.values())]
    elif all(-bound < ci90[c][0] and ci90[c][1] < bound for c in PREDICTED):
        label = "null"
    else:
        label = "underpowered"
    return {"label": label, "margins": point, "ci95": ci95, "ci90": ci90, "meets_rule": meets, "p_interaction": p_interaction}
