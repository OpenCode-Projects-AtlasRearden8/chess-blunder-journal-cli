"""Optional plain-English musings via an OpenAI-compatible endpoint.

Works with Ollama's built-in OpenAI compatibility (http://localhost:11434/v1)
or any other OpenAI-compatible server. No API key is required or sent: this
tool is built for local model servers like Ollama.

The request uses only the Python standard library (urllib), so there are no
extra dependencies and no secrets on disk. If the server is unreachable, you
get a friendly plain-English hint instead of a stack trace.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TIMEOUT = 90


def build_prompt(entries: list, tally: dict, causes: list) -> str:
    """Compose the musing prompt from the journal's own aggregates."""
    phase = tally["counts"]
    phase_text = ", ".join(f"{p}: {n}" for p, n in phase.items()) or "none yet"
    cause_text = (
        "; ".join(f"{c} (x{n})" for c, n in causes) or "no recurring causes yet"
    )
    type_hist = {}
    for e in entries:
        t = e.get("blunder_type", "unspecified")
        type_hist[t] = type_hist.get(t, 0) + 1
    types = ", ".join(f"{t} x{n}" for t, n in type_hist.items()) or "none yet"
    return (
        "You are a warm, plain-English chess coach for a club player. "
        "Never condescending, concrete, encouraging, under 150 words.\n\n"
        "Journal summary:\n"
        f"- Blunders by phase: {phase_text}\n"
        f"- Blunder types: {types}\n"
        f"- Recurring causes: {cause_text}\n\n"
        "In plain English: what single pattern do you see, what does it say "
        "about my thinking between moves (not just my chess knowledge), and "
        "what one habit should I practice this week?"
    )


def ask(endpoint: str = DEFAULT_ENDPOINT, model: str = DEFAULT_MODEL,
        prompt: str = "", timeout: int = DEFAULT_TIMEOUT) -> str:
    """POST /chat/completions to an OpenAI-compatible server; no API key."""
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt or "Say hi in one sentence."}
        ],
        "temperature": 0.4,
        "stream": False,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return (
            f"Could not reach the model server at {endpoint} ({reason}).\n"
            "Is Ollama running? Try:  ollama serve  and pull a model with:  "
            f"ollama pull {model}\n"
            "The rest of this journal works fine offline without the muse."
        )
    except TimeoutError:
        return (
            f"The model at {endpoint} took longer than {timeout}s to answer. "
            "Try a smaller model or a longer --timeout."
        )
    try:
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        return (
            f"Got a reply from {endpoint} but could not read it "
            f"(unexpected format): {json.dumps(body)[:400]}"
        )
