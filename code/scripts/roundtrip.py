"""Check on every saved run that each format turns back into the identical event stream.

Writes results/roundtrip.csv: one line per run with ok / FAIL per format and the size of each rendering.
Run:  uv run python code/scripts/roundtrip.py
"""

import csv
import hashlib
import json
from pathlib import Path

from auditarch.render import diff, log, prov
from auditarch.schema import Event

ROOT = Path(__file__).resolve().parents[2]


def main():
    rows = []
    for path in sorted((ROOT / "results").glob("*/*/events.jsonl")):
        events = [Event(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]
        if not events:
            continue
        texts = {"log": log.render(events), "diff": diff.render(events), "prov": prov.render(events)}
        parsers = {"log": lambda: log.parse(texts["log"]), "diff": lambda: diff.parse(texts["diff"]),
                   "prov": lambda: prov.parse(prov.render_json(events))}
        row = {"run": str(path.parent.relative_to(ROOT / "results")), "steps": len(events)}
        for name in texts:
            try:
                row[name + "_ok"] = "ok" if parsers[name]() == events else "FAIL"
            except Exception as error:                     # a rendering that cannot be read back is a failure too
                row[name + "_ok"] = f"FAIL ({type(error).__name__})"
            row[name + "_bytes"] = len(texts[name].encode("utf-8"))
        row["distinct_hashes"] = len({hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts.values()})
        rows.append(row)

    with open(ROOT / "results" / "roundtrip.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failures = [r["run"] for r in rows if any(str(v).startswith("FAIL") for v in r.values())]
    mean = lambda key: round(sum(r[key] for r in rows) / len(rows))
    print(f"runs: {len(rows)} | round-trip failures: {len(failures)} {failures[:5]}")
    print(f"mean bytes  log {mean('log_bytes')}  diff {mean('diff_bytes')}  prov {mean('prov_bytes')}")


if __name__ == "__main__":
    main()
