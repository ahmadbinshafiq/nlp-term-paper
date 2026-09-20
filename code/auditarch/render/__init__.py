"""Three ways to write down the same event stream: event log, state diffs, PROV graph.

Every module has render(events) -> text and parse(text) -> events. The text is what the auditor reads.
parse(render(events)) == events is the proof that a format loses nothing (code/scripts/roundtrip.py).
"""
