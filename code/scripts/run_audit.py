"""Audit saved runs: show each run to the auditor in each format and score the answers.

Audits the clean runs of the chosen pool (controls) and every faulty run found under results/faulty/ for that pool.
Appends one row per call to results/<out>/scores.csv (columns: analysis/schema.md). A row that exists is not made again.

Run:  uv run python code/scripts/run_audit.py --pool dev --out pilot-w3
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from auditarch.auditor import audit, prompt_hash
from auditarch.llm import AUDITOR_MODEL, OPTIONS, make_llm
from auditarch.render import diff, log, prov
from auditarch.schema import Event
from auditarch.score import score

ROOT = Path(__file__).resolve().parents[2]
FORMATS = {"log": log, "diff": diff, "prov": prov}
N_DEVELOPMENT, N_CLEAN_CONTROLS = 5, 25
COLUMNS = ["run_id", "task_id", "fault_type", "fault_class", "hook_tool", "k", "k_bin", "n_steps", "rel_pos", "format", "arm",
           "auditor_role", "sample_id", "is_control", "is_development", "pred_step", "true_step", "exact", "within3", "pred_cat",
           "true_cat", "false_alarm", "pointer_ok", "parse_ok", "tokens_in", "tokens_out", "bytes_record", "prompt_hash",
           "render_hash", "model_tag", "model_digest", "ollama_version", "think", "num_ctx", "seconds"]


def runs_of(pool: str):
    """Yields (folder with events.jsonl, truth or None) for the clean controls and the faulty runs of the pool."""
    passed = [d for d in sorted((ROOT / "results" / "clean").iterdir()) if not json.loads((d / "run.json").read_text())["gate_failed"]]
    tasks = passed[:N_DEVELOPMENT] if pool == "dev" else passed[N_DEVELOPMENT:]
    for clean_dir in tasks[:N_CLEAN_CONTROLS]:
        yield clean_dir, None
    for clean_dir in tasks:
        for fault_dir in sorted((ROOT / "results" / "faulty" / clean_dir.name).glob("*")):
            yield fault_dir, json.loads((fault_dir / "truth.json").read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", choices=["dev", "sweep"], default="dev")
    parser.add_argument("--out", default="pilot-w3", help="folder under results/")
    parser.add_argument("--model", default=AUDITOR_MODEL)
    parser.add_argument("--role", choices=["primary", "second"], default="primary")
    parser.add_argument("--think", action="store_true", help="auditor with thinking on (pre-registration, section 9)")
    args = parser.parse_args()

    llm, pins = make_llm(args.model, think=args.think, num_predict=4096 if args.think else OPTIONS["num_predict"])   # 4096 leaves room for the record inside num_ctx
    path = ROOT / "results" / args.out / "scores.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            done = {(r["run_id"], r["format"], r["model_tag"]) for r in csv.DictReader(f)}

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if not done:
            writer.writeheader()
        for folder, truth in runs_of(args.pool):
            with open(folder / "events.jsonl", encoding="utf-8") as lines:
                events = [Event(**json.loads(line)) for line in lines]
            task_id = truth["task_id"] if truth else json.loads((folder / "run.json").read_text())["task_id"]
            fault_type = truth["fault_type"] if truth else "clean"
            k = truth["k"] if truth else ""
            run_id = f"{task_id}|{fault_type}|{k}" if truth else f"{task_id}|clean"

            for fmt, module in FORMATS.items():
                if (run_id, fmt, args.model) in done:
                    continue
                record = module.render(events)
                result = audit(llm, pins, fmt, record)
                row = {
                    "run_id": run_id, "task_id": task_id, "fault_type": fault_type,
                    "fault_class": truth["fault_class"] if truth else "none", "true_cat": truth["fault_class"] if truth else "none",
                    "hook_tool": truth["hook_tool"] if truth else "", "k": k, "k_bin": truth["k_bin"] if truth else "",
                    "n_steps": len(events), "rel_pos": round(k / len(events), 3) if truth else "",
                    "format": fmt, "arm": "lossless", "auditor_role": args.role, "sample_id": 0,
                    "is_development": int(args.pool == "dev"),
                    "tokens_in": result["tokens_in"], "tokens_out": result["tokens_out"], "seconds": result["seconds"],
                    "bytes_record": len(record.encode("utf-8")), "prompt_hash": prompt_hash(fmt),
                    "render_hash": hashlib.sha256(record.encode("utf-8")).hexdigest(),
                    "model_tag": pins["model_tag"], "model_digest": pins["model_digest"], "ollama_version": pins["ollama_version"],
                    "think": "on" if pins["options"]["think"] else "off", "num_ctx": pins["options"]["num_ctx"],
                    **score(result["answer"], truth, record),
                }
                writer.writerow({c: ("" if row[c] is None else row[c]) for c in COLUMNS})
                f.flush()
                print(f"{run_id[:40]:40s} {fmt:4s} pred={row['pred_step']} true={row['true_step']} exact={row['exact']} "
                      f"false_alarm={row['false_alarm']} tokens_in={row['tokens_in']} {row['seconds']}s")


if __name__ == "__main__":
    main()
