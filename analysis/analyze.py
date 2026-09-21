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


def guesser_baselines(development: bool) -> pd.DataFrame:
    """The three baselines that use no model. They read the saved faulty runs, not the auditor's answers."""
    runs = []
    for path in sorted((ROOT / "results" / "faulty").glob("*/*/truth.json")):
        truth = json.loads(path.read_text())
        is_dev = int(path.parent.parent.name[:3]) in DEVELOPMENT_ORDERS
        if truth["fault_type"] != "sham" and is_dev == development:
            with open(path.parent / "events.jsonl", encoding="utf-8") as f:
                runs.append((truth, [Event(**json.loads(line)) for line in f]))
    rows = []
    for truth, events in runs:
        others = [(t["k"], len(e)) for t, e in runs if t["task_id"] != truth["task_id"]]       # the tested task is left out
        n_acts = sum(1 for e in events if e.tool_call)
        rows.append({"fault_type": truth["fault_type"], "uniform chance": 1 / n_acts,
                     "position-only": position_only_guess(len(events), others) == truth["k"],
                     "structure-only": structure_only_guess(events) == truth["k"],
                     "rule auditor": rule_audit(events) == truth["k"]})
    return pd.DataFrame(rows).groupby("fault_type").mean().reindex(FAULT_ORDER)


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

    faulty.to_csv(folder / "primary_input.csv", index=False)
    subprocess.run(["Rscript", str(ROOT / "analysis" / "primary.R"), str(folder / "primary_input.csv"), str(folder / "primary_test.csv")], check=True)
    test = pd.read_csv(folder / "primary_test.csv").iloc[0]

    guessers = guesser_baselines(args.development)
    chance = guessers["uniform chance"].mean()
    controls_ok = bool(guessers["position-only"].mean() < chance + 0.10)          # controls 2 to 4 in short; details in the tables below
    result = decide(faulty, float(test.p_interaction), controls_ok, args.bound)

    out = [f"# Analysis of sweep `{args.sweep}`, {args.role} auditor ({scores.model_tag.iloc[0]})", "",
           "EXPLORATORY: development tasks." if args.development else "Main analysis: sweep tasks.", "",
           f"Faulty runs: {faulty.run_id.nunique()} (removed as too long: {scores[too_long].run_id.nunique()}). "
           f"Answers parsed: {scores.parse_ok.mean():.2f}.", "",
           "## 1. Outcome label", "", f"**{result['label']}**", "",
           f"Interaction test: p = {result['p_interaction']:.4f} ({test.ladder_step}). Equivalence bound B = {args.bound:.2f}.", "",
           "| Class | Predicted format | Margin | 95% interval | 90% interval | Meets the rule |", "|---|---|---|---|---|---|"]
    for c, best in {"tool": "log", "state": "diff", "evidence": "prov"}.items():
        out.append(f"| {c} | {best} | {result['margins'][c]:+.3f} | [{result['ci95'][c][0]:+.3f}, {result['ci95'][c][1]:+.3f}] | "
                   f"[{result['ci90'][c][0]:+.3f}, {result['ci90'][c][1]:+.3f}] | {'yes' if result['meets_rule'][c] else 'no'} |")
    out += ["", "## 2. Exact step found, per fault class and format", "", table(accuracy_table(faulty)), "",
            "## 3. Exact step found, per fault type and format", "",
            table(faulty.pivot_table(index="fault_type", columns="format", values="exact", aggfunc="mean").reindex(FAULT_ORDER)[FORMATS]), "",
            "## 4. Baselines without a model (share of runs where the faulty step was named)", "", table(guessers), "",
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
    (folder / "analysis.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:14]))


DEVELOPMENT_ORDERS = {0, 1, 2, 11, 13}          # seed-order numbers of the five development tasks (DECISIONS.md)

if __name__ == "__main__":
    main()
