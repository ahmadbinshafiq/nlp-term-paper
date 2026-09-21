"""Pinned local models (decisions D-003 and D-003c).

Every script that calls a model goes through this file, so the Ollama version,
the model digest and the options are the same everywhere and are checked first.
"""

import json
import urllib.request

from langchain_ollama import ChatOllama

OLLAMA_URL = "http://localhost:11434"
PINNED_OLLAMA_VERSION = "0.33.2"

AGENT_MODEL = "glm-4.7-flash:q8_0"
AUDITOR_MODEL = "qwen3.8:27b"                    # primary auditor (decision D-012)
SECOND_AUDITOR_MODEL = "glm-4.7-flash:q8_0"      # second auditor: fast, audits all runs as well

# model tag -> full sha256 digest. A tag can be re-uploaded; a digest cannot change.
PINNED_DIGESTS = {
    "glm-4.7-flash:q8_0": "a035bf4bc812e1408631c2d2b14581b99dfe39f71d895aceb269b4a886080196",
    "qwen3.8:27b": "22130167c4c20e20c7b71454612966ca8e8171e9b3cc8ab6ce8aa6cbfec79643",
}

# The same options for every call. num_ctx is fixed for good in week 3.
# THINK turns also get THINK_STOP; ACT turns also get a JSON schema (agent.py).
OPTIONS = {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 1024}
THINK_STOP = ["</think>", "ACT turn", '{"tool"']      # a THINK turn must not run on into the next act


def _get(path: str) -> dict:
    with urllib.request.urlopen(OLLAMA_URL + path, timeout=30) as response:
        return json.loads(response.read())


def check_pins(model: str) -> dict:
    """Stop if the Ollama version or the model digest differs from the pinned values.

    Returns the values, so a caller can store them next to each model response.
    """
    version = _get("/api/version")["version"]
    digests = {m["name"]: m["digest"] for m in _get("/api/tags")["models"]}
    if version != PINNED_OLLAMA_VERSION:
        raise RuntimeError(f"Ollama is {version}, pinned is {PINNED_OLLAMA_VERSION} (rule D-003c)")
    if model not in digests:
        raise RuntimeError(f"model {model} is not installed")
    if model not in PINNED_DIGESTS:
        raise RuntimeError(f"model {model} has no pinned digest yet; add {digests[model]} to PINNED_DIGESTS")
    if digests[model] != PINNED_DIGESTS[model]:
        raise RuntimeError(f"digest of {model} changed: {digests[model]} (rule D-003c)")
    return {"ollama_version": version, "model_tag": model, "model_digest": digests[model], "options": OPTIONS}


def make_llm(model: str = AGENT_MODEL, think: bool = False, **overrides):
    """Returns (llm, pins). `pins` holds everything that decides an answer, so it is part of every cache key."""
    pins = check_pins(model)
    options = {**OPTIONS, **overrides}
    pins["options"] = {**options, "think": think}
    return ChatOllama(model=model, reasoning=think, keep_alive="30m", client_kwargs={"timeout": 1800}, **options), pins
