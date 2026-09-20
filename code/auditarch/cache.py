"""A content-addressed cache for model calls.

The key is a hash of everything that decides the answer: model digest, options,
the JSON schema the reply must fit, and the messages. The same input always gives
back the same stored text, byte for byte. This is what lets us replay a run up to
step k exactly and only then plant a fault.
"""

import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / "cache"


def cached_invoke(llm, pins: dict, messages, schema=None, strict: bool = False):
    """Ask the model, or give back the stored reply for exactly this input.

    schema: a JSON schema the reply must fit (None = free text).
    strict=True means "replay only": a cache miss is an error (used for replays and sham runs).
    Returns (reply text, usage), where usage = {"tokens_in", "tokens_out", "seconds", "cached"}.
    """
    key_input = {
        "model_digest": pins["model_digest"],
        "options": pins["options"],
        "schema": schema,
        "messages": [[m.type, m.content] for m in messages],
    }
    key = hashlib.sha256(json.dumps(key_input, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"{key}.json"

    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        return stored["content"], {**stored["usage"], "cached": True}
    if strict:
        raise RuntimeError(f"cache miss in replay-only mode (key {key[:12]})")

    start = time.time()
    reply = llm.invoke(messages, format=schema) if schema else llm.invoke(messages)
    meta = reply.response_metadata
    usage = {"tokens_in": meta.get("prompt_eval_count", 0), "tokens_out": meta.get("eval_count", 0),
             "seconds": round(time.time() - start, 2)}
    stored = {"content": reply.content, "usage": usage,
              "ollama_version": pins["ollama_version"], "model_tag": pins["model_tag"], "model_digest": pins["model_digest"]}
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(stored, ensure_ascii=False, indent=1), encoding="utf-8")
    return reply.content, {**usage, "cached": False}
