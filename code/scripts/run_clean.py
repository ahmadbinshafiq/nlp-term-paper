"""Run clean (fault-free) agent runs in seed order until enough tasks pass the gate.

Each run is saved to results/clean/<order>_<task_id>/ as
  events.jsonl  the canonical event stream (the record)
  run.json      how the run ended, the gate result, tokens and seconds
A task that already has a run.json is not run again, so the script can be stopped and restarted.

Run:  uv run python code/scripts/run_clean.py --passers 5
"""

import argparse
import json
from pathlib import Path

from auditarch.agent import STEP_CAP, build_agent, run_task
from auditarch.gate import check_clean_run
from auditarch.llm import AGENT_MODEL, make_llm
from auditarch.retrieval import Bm25Index, build_corpus, load_tasks

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--passers", type=int, default=5, help="stop when this many tasks have passed the gate")
    parser.add_argument("--max-runs", type=int, default=120)
    parser.add_argument("--model", default=AGENT_MODEL)
    parser.add_argument("--think", action="store_true", help="thinking on in THINK turns (rule D-003b)")
    parser.add_argument("--out", default="clean", help="folder under results/")
    args = parser.parse_args()

    tasks = load_tasks()
    with open(ROOT / "data" / "gold.jsonl", encoding="utf-8") as f:
        gold = {g["id"]: g for g in map(json.loads, f)}
    actor = make_llm(args.model)                                           # ACT turns: thinking off, JSON action
    thinker = make_llm(args.model, think=True, num_predict=8192) if args.think else actor
    pins = thinker[1]
    agent = build_agent(thinker, actor, Bm25Index(build_corpus(tasks)))
    out = ROOT / "results" / args.out

    passed = 0
    for task in tasks[: args.max_runs]:
        run_dir = out / f"{task['order']:03d}_{task['id']}"
        if not (run_dir / "run.json").exists():
            final = run_task(agent, task["question"])
            gate = check_clean_run(final["events"], final["app"], final["ended"], gold[task["id"]])
            live = [u for u in final["usage"] if not u["cached"]]
            summary = {
                "task_id": task["id"], "order": task["order"], "hops": task["hops"],
                "ended": final["ended"], "n_steps": final["step_id"], "step_cap": STEP_CAP,
                "answer": final["app"]["answer"], "gold_answer": gold[task["id"]]["answer"],
                "gate_failed": gate["failed"], "flags": gate["flags"],
                "model_calls": len(final["usage"]),
                "tokens_in": sum(u["tokens_in"] for u in final["usage"]),
                "tokens_out": sum(u["tokens_out"] for u in final["usage"]),
                "seconds": round(sum(u["seconds"] for u in live), 1),
                **pins,
            }
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "events.jsonl").write_text(
                "".join(e.model_dump_json() + "\n" for e in final["events"]), encoding="utf-8")
            (run_dir / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

        summary = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        ok = not summary["gate_failed"]
        passed += ok
        print(f"{summary['order']:3d} {summary['hops']}hop steps={summary['n_steps']:2d} {summary['ended']:11s} "
              f"{'PASS' if ok else 'fail'}  answer={summary['answer']!r} gold={summary['gold_answer']!r} {summary['gate_failed']}")
        if passed >= args.passers:
            break
    print(f"passed {passed}")


if __name__ == "__main__":
    main()
