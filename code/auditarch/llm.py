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
AUDITOR_MODEL = "glm-4.7-flash:q8_0"
SECOND_AUDITOR_MODEL = "qwen3.8:27b"

# model tag -> full sha256 digest. A tag can be re-uploaded; a digest cannot change.
PINNED_DIGESTS = {
    "glm-4.7-flash:q8_0": "a035bf4bc812e1408631c2d2b14581b99dfe39f71d895aceb269b4a886080196",
}

# The same options for every call. num_ctx is fixed for good in week 3.
OPTIONS = {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 1024}


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


def chat_model(model: str = AGENT_MODEL, **overrides) -> ChatOllama:
    """A ChatOllama with the pinned options and thinking off."""
    return ChatOllama(model=model, reasoning=False, keep_alive="30m", **{**OPTIONS, **overrides})
