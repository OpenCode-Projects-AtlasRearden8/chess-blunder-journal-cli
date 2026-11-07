"""The five-minute drill plan, built from your own pattern pile.

Rule-based and deterministic: the same journal always produces the same plan,
so it is easy to test and easy to trust.
"""

from __future__ import annotations

from .tally import blunder_type_tally, heat_counts, top_causes

# Drills are 60-second blocks; a plan has up to five blocks.
BLOCK_DRILLS = {
    "hanging piece": (
        "60s: Blunder-check scan. Set up any position, do one full sweep "
        "of checks, captures, threats before you say your move out loud."
    ),
    "missed tactic": (
        "60s: Quick tactics. Solve 2-3 easy puzzles, focusing on forcing "
        "moves first (checks, captures, threats)."
    ),
    "bad trade": (
        "60s: Trade filter. Look at three exchange situations and ask "
        "giving up a pawn or a pair helps or hurts my position."
    ),
    "weak pawn move": (
        "60s: Pawn-commit drill. For each candidate move, name the squares "
        "it stops defending before playing it."
    ),
    "time trouble": (
        "60s: Tempo discipline. Play 5 blind blitz moves at 5 seconds per "
        "move, always relocating your hand before each move."
    ),
    "overworked piece": (
        "60s: Piece jobs. Pick your busiest piece and list every duty it "
        "has; then free one."
    ),
    "king safety": (
        "60s: King shield check. Scan open files, missing pawns, and "
        "enemy pieces near your king in three positions."
    ),
    "queen loss": (
        "60s: Queen-escape drill. Put your queen where it is attacked and "
        "find all safe squares, including ones that trade."
    ),
}

DEFAULT_DRILLS = [
    "60s: Blunder-check scan. One position, full sweep of checks, "
    "captures, threats before each move.",
    "60s: Ask aloud what my opponent wants; find their most forcing "
    "idea in one position.",
    "60s: Play through last week's own blunder and describe the fix "
    "in one sentence.",
]

CAUSE_FIXES = {
    "time pressure": "Pre-move checklist: checks, captures, threats.",
    "blitz time pressure": "Count to three in winning positions.",
    "tiredness": "Stop playing after two straight losses.",
    "tilt": "Pause one breath after a mistake before moving on.",
    "overconfidence": "Assume every opponent move has a point.",
    "not calculating": "Force one concrete line before committing.",
    "ignored opponent threat": "Ask what changed after each move.",
    "haste": "Slow down on quiet moves; they hide ideas.",
    "unknown opening line": "Review one line in your main opening today.",
    "misjudged trade": "Count material before and after each trade.",
}


def _cause_drill(cause: str) -> str:
    """One 60s habit block tuned to a specific cause."""
    for key, fix in CAUSE_FIXES.items():
        if key in cause:
            return f"60s: Habit reset - {fix}"
    return (
        f"60s: Habit reset - before each move, name '{cause}' and the "
        "checklist of one thing that prevents it."
    )


def type_drill(blunder_type: str) -> str:
    """Pick the pre-written drill for a blunder type, or a generic block."""
    for key, drill in BLOCK_DRILLS.items():
        if key in blunder_type:
            return drill
    return (
        f"60s: Replay one '{blunder_type}' moment from your journal and "
        "state the defensive resource out loud."
    )


def build_plan(entries: list) -> dict:
    """Return a printable five-minute drill plan dict.

    Blocks, top to bottom:
      1. The phase that burns the most blunders (pattern focus).
      2. The most common blunder type.
      3-4. One habit block per top recurring cause.
      5. Recap block.

    Returns {"blocks": [{"title": str, "drill": str}], "motivation": str}
    """
    blocks = []
    heat = heat_counts(entries)
    counts = heat["counts"]
    hottest = max(counts, key=lambda p: counts[p]) if entries else None

    if hottest and counts[hottest] > 0:
        blocks.append(
            {
                "title": f"1. {hottest.capitalize()} heat ({counts[hottest]} blunders)",
                "drill": (
                    f"60s: Open a game and find the moment your {hottest} "
                    "usually collapses; label the trigger out loud."
                ),
            }
        )

    type_counts = blunder_type_tally(entries)
    if type_counts:
        worst_type, worst_count = type_counts.most_common(1)[0]
        blocks.append(
            {
                "title": f"2. Top blunder type: {worst_type} (x{worst_count})",
                "drill": type_drill(worst_type),
            }
        )

    for cause, n in top_causes(entries, limit=2):
        blocks.append({"title": f"3+. Cause: {cause} (x{n})", "drill": _cause_drill(cause)})

    filler = list(DEFAULT_DRILLS)
    if not blocks:
        blocks.append({"title": "1. Starter block", "drill": filler.pop(0)})
    while len(blocks) < 5:
        if filler:
            drill = filler.pop(0)
        else:
            drill = (
                "60s: One position, one thought - what is my opponent "
                "threatening?  Answer before relaxing."
            )
        blocks.append(
            {
                "title": f"{len(blocks) + 1}. Extra block",
                "drill": drill,
            }
        )
    while len(blocks) > 5:
        # never exceed five blocks; drop the last extra ones
        blocks.pop()

    blocks[-1] = {"title": "5. Recap", "drill": "60s: Say the ONE rule from today's plan you will use in your next game."}
    return {
        "blocks": blocks,
        "motivation": "Small daily sweeps fix big weekly leaks. Five minutes is enough.",
    }


def render_plan(plan: dict) -> str:
    """Turn a plan dict into printable text."""
    lines = ["Five-minute drill plan", "=" * 60]
    for block in plan["blocks"]:
        lines.append(block["title"])
        lines.append(f"    {block['drill']}")
    lines.append("")
    lines.append(plan["motivation"])
    return "\n".join(lines)
