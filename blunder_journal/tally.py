"""Tally logic: phase heat counts and top recurring causes.

Pure functions on lists of entry dicts so they are easy to test.
"""

from __future__ import annotations

from collections import Counter

from .store import PHASES, clean_cause

HEAT_CHARS = "▁▂▃▄▅▆▇█"


def phase_tally(entries: list) -> dict:
    """Count blunders per canonical phase, including zero for empty phases.

    Returns:
        {"opening": int, "middlegame": int, "endgame": int}
    """
    counts = Counter(
        e.get("phase", "")
        for e in entries
        if isinstance(e, dict) and e.get("phase") in PHASES
    )
    result = {}
    for phase in PHASES:
        result[phase] = counts.get(phase, 0)
    return result


def infer_phase_from_move(move_number: int) -> str:
    """Rough move-number fallback: opening <= 12, endgame >= 40 else middle."""
    if move_number <= 12:
        return "opening"
    if move_number >= 40:
        return "endgame"
    return "middlegame"


def heat_counts(entries: list) -> dict:
    """Phase counts plus printable heat bars keyed by phase.

    Returns:
        {"counts": phase_tally(entries), "bars": {phase: bar-string}}
    """
    counts = phase_tally(entries)
    peak = max(counts.values())
    bars = {}
    for phase, value in counts.items():
        if peak == 0:
            bars[phase] = ""
            continue
        level = round(value / peak * (len(HEAT_CHARS) - 1))
        bars[phase] = HEAT_CHARS[level] * value if value else ""
    return {"counts": counts, "bars": bars, "peak": peak}


def top_causes(entries: list, limit: int = 3) -> list:
    """Most common normalized likely-causes, descending.

    Returns a list of (cause, count) tuples, at most `limit` items.
    Causes with fewer than 2 occurrences are skipped: one-off mistakes are
    noise; this tool is about recurring patterns.
    """
    counts = Counter(
        clean_cause(e.get("likely_cause", ""))
        for e in entries
        if isinstance(e, dict)
    )
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(cause, n) for cause, n in ranked[:limit] if n >= 2]


def blunder_type_tally(entries: list) -> Counter:
    """Counts of each blunder type, for use by the drill planner."""
    return Counter(
        " ".join((e.get("blunder_type", "")).split()).lower()
        for e in entries
        if isinstance(e, dict) and e.get("blunder_type")
    )


def phase_type_pairs(entries: list) -> Counter:
    """Counts of (phase, blunder_type) combos, the pattern pile."""
    return Counter(
        (e.get("phase", ""), " ".join(e.get("blunder_type", "").split()).lower())
        for e in entries
        if isinstance(e, dict) and e.get("phase") in PHASES
    )
