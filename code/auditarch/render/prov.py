"""Format 3: a W3C PROV graph. Steps are activities, data items are entities, edges say what used and made what.

    activity(step:4, [aa:kind="act", aa:tool="read", aa:args="{...}"])
    entity(passage:0123abcd4567, [aa:title="...", aa:text="..."])
    used(step:4, passage:0123abcd4567)
    wasDerivedFrom(note:director@6, passage:0123abcd4567)

How the state effects of a step become graph items:
  think       -> entity thought:k,      wasGeneratedBy(thought, step)
  read        -> entity passage:<pid>,  used(step, passage)
  write_note  -> entity note:<key>@k,   wasGeneratedBy(note, step), wasDerivedFrom(note, passage:<source_pid>)
  finish      -> entity answer:k,       wasGeneratedBy(answer, step), wasDerivedFrom(answer, note)
Every edge comes from a field of the event stream. Nothing is guessed.

render() gives PROV-N, the standard text form, which is what the auditor reads.
The round trip goes through PROV-JSON, the same document in the form the prov library can read back.
"""

import json

from prov.model import ProvDocument

from auditarch.schema import Event

# One prefix per kind of item, so ids read like step:4, passage:0123abcd4567, note:director@6.
NAMESPACES = {name: f"urn:auditarch:{name}:" for name in ["step", "thought", "passage", "note", "answer", "aa"]}


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def build(events: list) -> ProvDocument:
    doc = ProvDocument()
    for prefix, uri in NAMESPACES.items():
        doc.add_namespace(prefix, uri)
    note_ids = {}                                          # note key -> id of its latest entity
    for e in events:
        k = e.step_id
        if e.node_kind == "think":
            step = doc.activity(f"step:{k}", other_attributes={"aa:kind": "think"})
            doc.wasGeneratedBy(doc.entity(f"thought:{k}", {"aa:text": e.state_patch[0]["value"]}), step)
            continue
        call, ret = e.tool_call.model_dump(), e.tool_return
        attributes = {"aa:kind": "act", "aa:tool": call["name"], "aa:args": dumps(call["args"])}
        effects = {op["path"].split("/")[1]: op for op in e.state_patch[1:]}      # "evidence", "notes", "answer", "decision"
        if "evidence" not in effects:
            attributes["aa:return"] = dumps(ret)           # a read's return is shown by its passage entity instead
        step = doc.activity(f"step:{k}", other_attributes=attributes)

        if "evidence" in effects:
            op = effects["evidence"]
            passage = doc.entity(f"passage:{ret['pid']}", {"aa:pid": ret["pid"], "aa:op": op["op"], **{f"aa:{f}": v for f, v in op["value"].items()}})
            doc.used(step, passage)
        if "notes" in effects:
            op = effects["notes"]
            key = op["path"].split("/", 2)[2]
            note = doc.entity(f"note:{key}@{k}", {"aa:key": key, "aa:op": op["op"], "aa:text": op["value"]["text"]})
            doc.wasGeneratedBy(note, step)
            if op["value"]["source_pid"] is not None:
                doc.wasDerivedFrom(note, f"passage:{op['value']['source_pid']}")
            note_ids[key] = note.identifier
        if "answer" in effects:
            decision = effects["decision"]["value"]
            answer = doc.entity(f"answer:{k}", {"aa:answer": effects["answer"]["value"], "aa:decision": dumps(decision)})
            doc.wasGeneratedBy(answer, step)
            if decision["note_key"] in note_ids:
                doc.wasDerivedFrom(answer, note_ids[decision["note_key"]])
    return doc


def render(events: list) -> str:
    return build(events).get_provn() + "\n"


def render_json(events: list) -> str:
    return build(events).serialize(format="json")


def parse(json_text: str) -> list:
    data = json.loads(json_text)
    entities = data.get("entity", {})
    made_by, used_by, source_of = {}, {}, {}               # step -> entity ids, step -> entity id, note id -> passage id
    for edge in data.get("wasGeneratedBy", {}).values():
        made_by.setdefault(edge["prov:activity"], []).append(edge["prov:entity"])
    for edge in data.get("used", {}).values():
        used_by[edge["prov:activity"]] = edge["prov:entity"]
    for edge in data.get("wasDerivedFrom", {}).values():
        source_of[edge["prov:generatedEntity"]] = edge["prov:usedEntity"]

    events = []
    for step_name, a in sorted(data["activity"].items(), key=lambda item: int(item[0].removeprefix("step:"))):
        k = int(step_name.removeprefix("step:"))
        if a["aa:kind"] == "think":
            text = entities[made_by[step_name][0]]["aa:text"]
            patch = [{"op": "add", "path": f"/scratch/{k}", "value": text}]
            events.append(Event(step_id=k, node_kind="think", tool_call=None, tool_return=None, state_patch=patch))
            continue
        call = {"name": a["aa:tool"], "args": json.loads(a["aa:args"])}
        effects = []
        if step_name in used_by:                           # a read that worked: the return is the passage entity
            p = entities[used_by[step_name]]
            seen = {"title": p["aa:title"], "text": p["aa:text"]}
            ret = {"pid": p["aa:pid"], **seen}
            effects.append({"op": p["aa:op"], "path": f"/evidence/{p['aa:pid']}", "value": seen})
        else:
            ret = json.loads(a["aa:return"])
        for entity_id in made_by.get(step_name, []):
            item = entities[entity_id]
            if "aa:key" in item:                           # a note
                source = source_of.get(entity_id)
                value = {"text": item["aa:text"], "source_pid": source.removeprefix("passage:") if source else None}
                effects.append({"op": item["aa:op"], "path": f"/notes/{item['aa:key']}", "value": value})
            else:                                          # the answer
                effects.append({"op": "replace", "path": "/answer", "value": item["aa:answer"]})
                effects.append({"op": "replace", "path": "/decision", "value": json.loads(item["aa:decision"])})
        patch = [{"op": "add", "path": f"/calls/{k}", "value": {"tool_call": call, "tool_return": ret}}] + effects
        events.append(Event(step_id=k, node_kind="act", tool_call=call, tool_return=ret, state_patch=patch))
    return events
