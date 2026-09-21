"""The analysis of one sweep: primary test, margins, decision tree, controls and secondary tables.

Reads results/<sweep>/scores.csv (columns: analysis/schema.md), runs analysis/primary.R, writes results/<sweep>/analysis.md.
Run:  uv run python analysis/analyze.py --sweep main --role primary --bound 0.20
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from margins import FORMATS, accuracy_table, decide          # noqa: E402

from auditarch.schema import Event                           # noqa: E402
from auditarch.score import position_only_guess, rule_audit, structure_only_guess   # noqa: E402

FAULT_ORDER = ["wrong_argument", "corrupted_output", "dropped_note", "overwritten_note", "wrong_source", "no_source"]


def table(df: pd.DataFrame) -> str:
    return df.to_markdown(floatfmt=".2f")


def wilson(hits: int, n: int) -> str:
    low, high = binomtest(hits, n).proportion_ci(method="wilson")
    return f"{hits}/{n} = {hits / n:.2f} [{low:.2f}, {high:.2f}]"


def saved_runs(development: bool):
    """(truth, events, folder) of every faulty or sham run of the chosen pool."""
    for path in sorted((ROOT / "results" / "faulty").glob("*/*/truth.json")):
        if (int(path.parent.parent.name[:3]) in DEVELOPMENT_ORDERS) == development:
            with open(path.parent / "events.jsonl", encoding="utf-8") as f:
                yield json.loads(path.read_text()), [Event(**json.loads(line)) for line in f], path.parent


def guesser_baselines(development: bool) -> pd.DataFrame:
    """The baselines that use no model. They read the saved faulty runs, not the auditor's answers. One row per run."""
    runs = [(t, e) for t, e, _ in saved_runs(development) if t["fault_type"] != "sham"]
    all_k = [t["k"] for t, _ in runs]
    rows = []
    for truth, events in runs:
        others = [(t["k"], len(e)) for t, e in runs if t["task_id"] != truth["task_id"]]       # the tested task is left out
        acts = [e for e in events if e.tool_call]
        notes = [e for e in acts if e.tool_call.name == "write_note"]
        rows.append({"fault_type": truth["fault_type"], "uniform chance": 1 / len(acts),
                     "tool prior": 1 / len(notes) if truth["hook_tool"] == "write_note" else 0.0,
                     "most frequent step": max(set(all_k), key=all_k.count) == truth["k"],
                     "position-only": position_only_guess(len(events), others) == truth["k"],
                     "structure-only": structure_only_guess(events) == truth["k"],
                     "rule auditor": rule_audit(events) == truth["k"]})
    return pd.DataFrame(rows).astype({c: float for c in ["most frequent step", "position-only", "structure-only", "rule auditor"]})


def sham_runs_equal_clean_runs(development: bool) -> bool:
    """Control 1: every sham record is byte-identical to the clean record of its task, so every rendering is too."""
    return all((folder / "events.jsonl").read_bytes() == (ROOT / "results" / "clean" / folder.parent.name / "events.jsonl").read_bytes()
               for truth, _, folder in saved_runs(development) if truth["fault_type"] == "sham")


def shuffled_label_point(faulty: pd.DataFrame, n_shuffles: int = 2000, seed: int = 0) -> tuple:
    """Control 4: the score against true steps shuffled within fault type. Returns (mean, 97.5 percent point)."""
    rng = np.random.default_rng(seed)
    runs = faulty.drop_duplicates("run_id")[["run_id", "fault_type", "true_step"]]
    scores = []
    for _ in range(n_shuffles):
        shuffled = runs.groupby("fault_type").true_step.transform(lambda s: rng.permutation(s.to_numpy()))
        step_of = dict(zip(runs.run_id, shuffled))
        scores.append((faulty.pred_step == faulty.run_id.map(step_of)).mean())
    return float(np.mean(scores)), float(np.quantile(scores, 0.975))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", required=True)
    parser.add_argument("--role", default="primary", choices=["primary", "second"])
    parser.add_argument("--bound", type=float, default=0.20, help="equivalence bound B from prereg/power.md")
    parser.add_argument("--development", action="store_true", help="analyse development rows (exploratory) instead of sweep rows")
    args = parser.parse_args()

    folder = ROOT / "results" / args.sweep
    scores = pd.read_csv(folder / "scores.csv")
    scores = scores[(scores.auditor_role == args.role) & (scores.arm == "lossless") & (scores.sample_id == 0)
                    & (scores.is_development == int(args.development))]
    if "too_long" not in scores:                                                  # files made before this column existed
        scores["too_long"] = 0
    too_long = scores.groupby("run_id").too_long.transform("max") == 1            # a too-long record removes the run in all formats
    faulty = scores[(scores.is_control == 0) & ~too_long]
    controls = scores[scores.is_control == 1]

    faulty.to_csv(folder / f"primary_input_{args.role}.csv", index=False)
    subprocess.run(["Rscript", str(ROOT / "analysis" / "primary.R"), str(folder / f"primary_input_{args.role}.csv"),
                    str(folder / f"primary_test_{args.role}.csv")], check=True)
    test = pd.read_csv(folder / f"primary_test_{args.role}.csv").iloc[0]

    assert (faulty.groupby("run_id").format.nunique() == 3).all(), "a run is missing one of its three formats: the audits are not complete"

    # the controls that decide step 0 of the tree (pre-registration, section 7)
    guessers = guesser_baselines(args.development)
    control1 = sham_runs_equal_clean_runs(args.development)
    tool_faults = guessers[guessers.fault_type.isin(["wrong_argument", "corrupted_output"])]
    hits, n = int(tool_faults["structure-only"].sum()), len(tool_faults)
    control3 = binomtest(hits, n).proportion_ci(method="wilson")[1] < guessers["tool prior"].mean() + 0.10
    shuffled_mean, shuffled_top = shuffled_label_point(faulty)
    control4 = faulty.exact.mean() > shuffled_top
    result = decide(faulty, float(test.p_interaction), control1 and control3 and control4, args.bound)

    acc = accuracy_table(faulty)
    ceiling = [c for c in acc.index if (acc.loc[c] >= 0.95).all()]            # a class where every format is at 95 percent or more
    if result["label"] == "refuted: one format dominates" and result["p_interaction"] < 0.05:
        result["label"] += " (size differs by class)"

    out = [f"# Analysis of sweep `{args.sweep}`, {args.role} auditor ({scores.model_tag.iloc[0]})", "",
           "EXPLORATORY: development tasks." if args.development else "Main analysis: sweep tasks.",
           "Second auditor: description only. Its label and p-value are shown for completeness and are not a test (pre-registration, section 8)."
           if args.role == "second" else "", "",
           f"Faulty runs: {faulty.run_id.nunique()} (removed as too long: {scores[too_long].run_id.nunique()}). "
           f"Answers parsed: {scores.parse_ok.mean():.2f}.", "",
           "## 1. Outcome label", "", f"**{result['label']}**", "",
           f"Interaction test: p = {result['p_interaction']:.4f} ({test.ladder_step}; fit warning left: {test.still_failed}). "
           f"Equivalence bound B = {args.bound:.2f}.", "",
           "Predictions that cannot be tested because every format is at 95 percent or more in that class (ceiling): "
           + (", ".join(ceiling) if ceiling else "none") + ".", "",
           f"Control 1 (sham records equal clean records): {'pass' if control1 else 'FAIL'}. "
           f"Control 3 (structure-only guesser on the two tool faults: {wilson(hits, n)}, against tool prior "
           f"{guessers['tool prior'].mean():.3f} + 0.10): {'pass' if control3 else 'FAIL'}. "
           f"Control 4 (real exact score {faulty.exact.mean():.3f} against labels shuffled within fault type: mean {shuffled_mean:.3f}, "
           f"97.5 percent point {shuffled_top:.3f}): {'pass' if control4 else 'FAIL'}.", "",
           "| Class | Predicted format | Margin | 95% interval | 90% interval | Meets the rule |", "|---|---|---|---|---|---|"]
    for c, best in {"tool": "log", "state": "diff", "evidence": "prov"}.items():
        out.append(f"| {c} | {best} | {result['margins'][c]:+.3f} | [{result['ci95'][c][0]:+.3f}, {result['ci95'][c][1]:+.3f}] | "
                   f"[{result['ci90'][c][0]:+.3f}, {result['ci90'][c][1]:+.3f}] | {'yes' if result['meets_rule'][c] else 'no'} |")
    out += ["", "## 2. Exact step found, per fault class and format", "", table(accuracy_table(faulty)), "",
            "## 3. Exact step found, per fault type and format", "",
            table(faulty.pivot_table(index="fault_type", columns="format", values="exact", aggfunc="mean").reindex(FAULT_ORDER)[FORMATS]), "",
            "## 4. Baselines without a model (share of runs where the faulty step was named)", "",
            table(guessers.groupby("fault_type").mean().reindex(FAULT_ORDER)), "",
            "All faults together: " + ", ".join(f"{c} {guessers[c].mean():.3f}" for c in guessers.columns[1:]) + ".", "",
            "## 5. Controls: clean and sham runs", ""]
    for fmt in FORMATS:
        c = controls[controls.format == fmt].drop_duplicates("task_id")           # a task that is both clean and sham control counts once
        f = faulty[faulty.format == fmt]
        missed = int((f.pred_step.isna() & (f.parse_ok == 1)).sum())
        out.append(f"- `{fmt}`: false alarms {wilson(int(c.false_alarm.sum()), len(c))}; said \"no fault\" on a faulty run {wilson(missed, len(f))}")
    late = faulty[(faulty.exact == 0) & faulty.pred_step.notna()]
    out += ["", "## 6. Secondary", "",
            table(faulty.groupby("format").agg(within3=("within3", "mean"), right_class=("pred_cat", lambda s: (s == faulty.loc[s.index, "true_cat"]).mean()),
                                               pointer_ok=("pointer_ok", "mean"), tokens_in=("tokens_in", "mean"), seconds=("seconds", "mean")).reindex(FORMATS)), "",
            f"Of the wrong step answers, the share that named a step AFTER the fault (the symptom, not the cause): "
            f"{(late.pred_step > late.true_step).mean():.2f}.", "",
            "Exact step by position of the fault (k_bin: 0 early, 1 middle, 2 late):", "",
            table(faulty.pivot_table(index="k_bin", columns="format", values="exact", aggfunc="mean")[FORMATS]), ""]
    (folder / f"analysis_{args.role}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:14]))


DEVELOPMENT_ORDERS = {0, 1, 2, 11, 13}          # seed-order numbers of the five development tasks (DECISIONS.md)

if __name__ == "__main__":
    main()
