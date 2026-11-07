"""Data model and JSON storage for the blunder journal.

Everything is stored locally in a plain JSON file. The default location is
``~/.blunder_journal.json``; override it with ``--file`` or the
``BLUNDER_JOURNAL_FILE`` environment variable. No network access happens
unless you explicitly ask for ``muse``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

PHASES = ("opening", "middlegame", "endgame")

DEFAULT_FILE = os.environ.get(
    "BLUNDER_JOURNAL_FILE",
    os.path.join(str(Path.home()), ".blunder_journal.json"),
)

REQUIRED_FIELDS = ("move_number", "phase", "blunder_type", "likely_cause")


def now_utc() -> str:
    """ISO-8601 UTC timestamp, seconds precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_phase(phase: str) -> str:
    """Map loose phase words onto the three canonical phases.

    Raises ValueError for anything unrecognizable.
    """
    text = (phase or "").strip().lower()
    aliases = {
        "opening": "opening",
        "open": "opening",
        "o": "opening",
        "middlegame": "middlegame",
        "middle": "middlegame",
        "mid": "middlegame",
        "m": "middlegame",
        "endgame": "endgame",
        "end": "endgame",
        "e": "endgame",
    }
    if text not in aliases:
        raise ValueError(
            f"unknown phase {phase!r}; use opening, middlegame, or endgame"
        )
    return aliases[text]


def clean_cause(cause: str) -> str:
    """Normalize a cause string so tallies group the same reason together."""
    collapsed = " ".join((cause or "").split()).lower().rstrip(".!")
    return collapsed or "unknown"


def make_entry(move_number: int, phase: str, blunder_type: str,
               likely_cause: str, note: str = "") -> dict:
    """Build one journal entry dict, validating as we go."""
    if not isinstance(move_number, int) or isinstance(move_number, bool):
        raise ValueError("move_number must be an integer")
    if move_number < 1 or move_number > 500:
        raise ValueError("move_number must be between 1 and 500")
    entry = {
        "logged_utc": now_utc(),
        "move_number": move_number,
        "phase": normalize_phase(phase),
        "blunder_type": " ".join((blunder_type or "").split()).lower()
        or "unspecified",
        "likely_cause": clean_cause(likely_cause),
        "note": (note or "").strip(),
    }
    return entry


def load_entries(path: str = DEFAULT_FILE) -> list:
    """Load entries from the JSON store; empty list if file is missing."""
    data_path = Path(path)
    if not data_path.exists():
        return []
    try:
        with data_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"data file {path} is not valid JSON: {exc}") from exc
    if isinstance(data, list):
        return [e for e in data if isinstance(e, dict)]
    raise ValueError(f"data file {path} should contain a JSON list")


def save_entries(entries: list, path: str = DEFAULT_FILE) -> None:
    """Write entries back to the JSON store."""
    data_path = Path(path)
    if data_path.parent and str(data_path.parent):
        data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def add_entry(entry: dict, path: str = DEFAULT_FILE) -> list:
    """Append an entry and persist."""
    entries = load_entries(path)
    entries.append(entry)
    save_entries(entries, path)
    return entries
