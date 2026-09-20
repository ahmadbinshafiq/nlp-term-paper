"""Check on every saved run that each format turns back into the identical event stream.

Writes results/roundtrip.csv: one line per run with ok / FAIL per format and the size of each rendering.
Run:  uv run python code/scripts/roundtrip.py
"""

import csv
import json
from pathlib import Path

from auditarch.render import diff, log, prov
from auditarch.schema import Event

ROOT = Path(__file__).resolve().parents[2]


def main():
    modules = {"log": log, "diff": diff, "prov": prov}
    rows = []
    for path in sorted((ROOT / "results").glob("*/*/events.jsonl")):
        with open(path, encoding="utf-8") as f:
            events = [Event(**json.loads(line)) for line in f]
        if not events:
            continue
        row = {"run": str(path.parent.relative_to(ROOT / "results")), "steps": len(events)}
        for name, module in modules.items():
            text = module.render(events)
            try:
                row[name + "_ok"] = "ok" if module.parse(text) == events else "FAIL"
            except Exception as error:                     # a rendering that cannot be read back is a failure too
                row[name + "_ok"] = f"FAIL ({type(error).__name__})"
            row[name + "_bytes"] = len(text.encode("utf-8"))
        rows.append(row)

    with open(ROOT / "results" / "roundtrip.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failures = [r["run"] for r in rows if any(str(v).startswith("FAIL") for v in r.values())]
    print(f"runs: {len(rows)} | round-trip failures: {len(failures)} {failures[:5]}")
    for name in modules:
        print(f"mean bytes {name}: {round(sum(r[name + '_bytes'] for r in rows) / len(rows))}")


if __name__ == "__main__":
    main()
