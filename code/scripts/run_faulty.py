"""Plant faults into clean runs that passed the gate (prereg/fault_catalogue.md).

For each task and fault: replay the clean run (the cache gives back every step before k), plant the fault at
step k, let the run go on live, and check that the record before step k is byte-identical to the clean run.
Saved to results/faulty/<order>_<task_id>/<fault_type>/ as
  events.jsonl  the record of the faulty run
  truth.json    the ground truth: which step, what was changed. No model ever sees this file.

Run:  uv run python code/scripts/run_faulty.py --pool dev --faults wrong_argument wrong_source sham
"""

import argparse
import json
from pathlib import Path

from auditarch.agent import build_agent, run_task
from auditarch.eligible import FAULT_TYPES
from auditarch.faults import FAULT_CLASS, choose_k
from auditarch.llm import AGENT_MODEL, THINK_STOP, make_llm
from auditarch.retrieval import Bm25Index, build_corpus, load_tasks
from auditarch.schema import Event

ROOT = Path(__file__).resolve().parents[2]
N_DEVELOPMENT = 5          # the first passing tasks are development tasks, the rest is the sweep pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", choices=["dev", "sweep"], default="dev")
    parser.add_argument("--faults", nargs="+", default=FAULT_TYPES, choices=FAULT_TYPES + ["sham"])
    args = parser.parse_args()

    tasks = {t["id"]: t for t in load_tasks()}
    index = Bm25Index(build_corpus(list(tasks.values())))
    actor = make_llm(AGENT_MODEL)
    thinker = make_llm(AGENT_MODEL, stop=THINK_STOP)

    passed = [d for d in sorted((ROOT / "results" / "clean").iterdir()) if not json.loads((d / "run.json").read_text())["gate_failed"]]
    pool = passed[:N_DEVELOPMENT] if args.pool == "dev" else passed[N_DEVELOPMENT:]

    for position, clean_dir in enumerate(pool):
        task = tasks[json.loads((clean_dir / "run.json").read_text())["task_id"]]
        clean_lines = (clean_dir / "events.jsonl").read_text(encoding="utf-8").splitlines(keepends=True)
        clean = [Event(**json.loads(line)) for line in clean_lines]

        for fault_type in args.faults:
            out = ROOT / "results" / "faulty" / clean_dir.name / fault_type
            if (out / "truth.json").exists():
                continue
            choice = choose_k(clean, fault_type, position)
            k = choice["k"]
            sham = fault_type == "sham"
            agent = build_agent(thinker, actor, index, strict=sham, fault={"type": fault_type, "k": k})   # a sham run must come from the cache alone
            final = run_task(agent, task)
            lines = [e.model_dump_json() + "\n" for e in final["events"]]

            # proof that only the fault differs (catalogue rule 6)
            same_until = len(clean_lines) if sham else k - 1
            assert lines[:same_until] == clean_lines[:same_until], f"{out}: the record differs from the clean run before step {k}"
            assert not sham or lines == clean_lines, f"{out}: a sham run must equal the clean run"

            after_k = [e for e in final["events"][k:] if e.tool_call and "error" in e.tool_return]
            truth = {
                "task_id": task["id"], "fault_type": fault_type, "fault_class": FAULT_CLASS[fault_type],
                "k": k, "k_bin": choice["k_bin"], "hook_tool": clean[k - 1].tool_call.name,
                "original": clean[k - 1].model_dump(), "changed": final["events"][k - 1].model_dump(),
                "ended": final["ended"], "n_steps": final["step_id"],
                "answer_changed": final["app"]["answer"] != json.loads((clean_dir / "run.json").read_text())["answer"],
                "finish_note_missing": bool(final["app"]["decision"]) and final["app"]["decision"]["note_key"] not in final["app"]["notes"],
                "requeried_after_k": any(e.tool_call.name == "search" for e in after_k),
                "reread_after_k": any(e.tool_call.name == "read" for e in after_k),
                "seconds": round(sum(u["seconds"] for u in final["usage"] if not u["cached"]), 1),
            }
            out.mkdir(parents=True, exist_ok=True)
            (out / "events.jsonl").write_text("".join(lines), encoding="utf-8")
            (out / "truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{clean_dir.name[:3]} {fault_type:17s} k={k:2d} ({truth['hook_tool']:10s}) ended={truth['ended']:9s} steps={truth['n_steps']:2d} "
                  f"answer_changed={truth['answer_changed']} {truth['seconds']}s")


if __name__ == "__main__":
    main()
