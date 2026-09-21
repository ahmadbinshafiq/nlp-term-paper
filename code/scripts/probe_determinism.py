"""Determinism probe (plan, section 3, step 7): does the auditor give the same answer when asked again?

Six records (two per format) are audited three times each, WITHOUT the cache, and the model is unloaded
between rounds so that a warm prompt cache cannot hide a difference. Writes results/probe-<model>.json.

Run:  uv run python code/scripts/probe_determinism.py --model qwen3.8:27b
"""

import argparse
import json
import subprocess
from pathlib import Path

from langchain_core.messages import HumanMessage

from auditarch.auditor import ANSWER_SCHEMA, prompt_for
from auditarch.llm import AUDITOR_MODEL, make_llm
from auditarch.render import diff, log, prov
from auditarch.schema import Event

ROOT = Path(__file__).resolve().parents[2]
ROUNDS = 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=AUDITOR_MODEL)
    args = parser.parse_args()
    llm, pins = make_llm(args.model)

    folders = sorted((ROOT / "results" / "faulty").glob("*/*"))[:6]                      # six faulty development runs
    formats = [("log", log), ("log", log), ("diff", diff), ("diff", diff), ("prov", prov), ("prov", prov)]
    prompts = []
    for folder, (name, module) in zip(folders, formats):
        with open(folder / "events.jsonl", encoding="utf-8") as f:
            events = [Event(**json.loads(line)) for line in f]
        prompts.append((f"{folder.parent.name[:3]}/{folder.name}/{name}", prompt_for(name, module.render(events))))

    answers = {label: [] for label, _ in prompts}
    for round_number in range(ROUNDS):
        subprocess.run(["ollama", "stop", args.model], capture_output=True)                # unload: the next call starts cold
        for label, prompt in (prompts if round_number % 2 == 0 else prompts[::-1]):        # another order in every second round
            answers[label].append(llm.invoke([HumanMessage(prompt)], format=ANSWER_SCHEMA).content)

    same_text = sum(len(set(a)) == 1 for a in answers.values())
    same_step = sum(len({json.loads(x)["step_id"] for x in a}) == 1 for a in answers.values())
    report = {"model": args.model, **pins, "records": len(prompts), "rounds": ROUNDS,
              "records_with_identical_text": same_text, "records_with_identical_step": same_step, "answers": answers}
    out = ROOT / "results" / f"probe-{args.model.replace(':', '-')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.model}: identical text in {same_text} of {len(prompts)} records, identical step in {same_step} of {len(prompts)}")


if __name__ == "__main__":
    main()
