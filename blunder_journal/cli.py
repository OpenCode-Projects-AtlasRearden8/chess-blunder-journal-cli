"""Command-line interface for chess-blunder-journal.

Commands:
  add     Log one painful moment from a finished game.
  list    Show the whole journal (or last N entries with --last).
  tally   Phase heat counts: where in the game you leak most.
  causes  Top recurring likely-causes from your pattern pile.
  drill   A printable five-minute drill plan from your own patterns.
  muse    Optional plain-English musing via an OpenAI-compatible endpoint
          (Ollama included, no API key needed).
  demo    Add a handful of sample entries so you can see the reports sing.

Data is stored locally in a JSON file (~/.blunder_journal.json by default);
override with --file or the BLUNDER_JOURNAL_FILE environment variable.
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .store import (
    DEFAULT_FILE,
    PHASES,
    add_entry,
    load_entries,
    make_entry,
)
from .tally import heat_counts, top_causes
from .drill import build_plan, render_plan
from .muse import (
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    ask,
    build_prompt,
)


def _entries_or_exit(args) -> list:
    try:
        return load_entries(args.file)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


def cmd_add(args) -> None:
    try:
        entry = make_entry(
            move_number=args.move_number,
            phase=args.phase,
            blunder_type=args.blunder_type,
            likely_cause=args.cause,
            note=args.note or "",
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    add_entry(entry, args.file)
    cozy = {
        "opening": "early fog",
        "middlegame": "mid-game grind",
        "endgame": "endgame crunch",
    }[entry["phase"]]
    print(f"Logged: move {entry['move_number']} ({cozy}), "
          f"{entry['blunder_type']} - cause: {entry['likely_cause']}")
    print(f"Saved to {args.file}")


def cmd_list(args) -> None:
    entries = _entries_or_exit(args)
    if not entries:
        print("No entries yet. Log one with: blunder-journal add ...")
        return
    if args.last:
        entries = entries[-args.last:]
    print(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'}"
          f"{' (last %d)' % args.last if args.last else ''}:")
    for i, e in enumerate(entries, 1):
        note = f"  note: {e['note']}" if e.get("note") else ""
        print(
            f"{i:>4}. move {e['move_number']:>3} | {e['phase']:<10} | "
            f"{e['blunder_type']:<22} | cause: {e['likely_cause']}{note}"
        )


def cmd_tally(args) -> None:
    entries = _entries_or_exit(args)
    if not entries:
        print("No entries yet - nothing to tally.")
        return
    heat = heat_counts(entries)
    counts, bars = heat["counts"], heat["bars"]
    print("Phase heat counts")
    print("-" * 46)
    for phase in PHASES:
        bar = bars[phase] or ""
        label = bar if bar else "(none)"
        print(f"{phase:<11}{counts[phase]:>3}  {label}")
    print("-" * 46)
    hottest = max(counts, key=lambda p: counts[p])
    if counts[hottest] > 0:
        print(f"Hottest phase: {hottest} ({counts[hottest]} of "
              f"{len(entries)} blunders)")
    else:
        print("No phase-classified entries yet.")


def cmd_causes(args) -> None:
    entries = _entries_or_exit(args)
    if not entries:
        print("No entries yet - nothing to analyze.")
        return
    causes = top_causes(entries, limit=args.top)
    if not causes:
        print("No repeats yet: each cause shows up once. Keep logging - "
              "patterns take a few games to eat their way clear.")
        return
    print("Top recurring causes")
    print("-" * 46)
    for cause, n in causes:
        print(f"{n:>3}x  {cause}")


def cmd_drill(args) -> None:
    entries = _entries_or_exit(args)
    if not entries:
        print("No entries yet - log a few games first so the plan has "
              "patterns to chew on.")
        return
    print(render_plan(build_plan(entries)))


def cmd_muse(args) -> None:
    entries = _entries_or_exit(args)
    if not entries:
        print("No entries yet - the muse wants something to muse about.")
        return
    heat = heat_counts(entries)
    causes = top_causes(entries, limit=3)
    prompt = build_prompt(entries, heat, causes)
    endpoint = args.endpoint or os.environ.get(
        "BLUNDER_JOURNAL_ENDPOINT", DEFAULT_ENDPOINT
    )
    model = args.model or os.environ.get("BLUNDER_JOURNAL_MODEL", DEFAULT_MODEL)
    print(f"Thinking with {model} at {endpoint} ...")
    print(ask(endpoint=endpoint, model=model, prompt=prompt, timeout=args.timeout))


def cmd_demo(args) -> None:
    samples = [
        (12, "opening", "weak pawn move", "unknown opening line"),
        (15, "opening", "bad trade", "misjudged trade"),
        (26, "middlegame", "hanging piece", "time pressure"),
        (31, "middlegame", "missed tactic", "not calculating"),
        (34, "middlegame", "hanging piece", "time pressure"),
        (38, "middlegame", "queen loss", "tiredness"),
        (47, "endgame", "weak pawn move", "tiredness"),
        (52, "endgame", "overworked piece", "haste"),
    ]
    added = 0
    for move, phase, btype, cause in samples:
        add_entry(
            make_entry(move, phase, btype, cause),
            args.file,
        )
        added += 1
    print(f"Added {added} sample entries to {args.file}.")
    print("Now try: blunder-journal tally  |  drill  |  causes")


def _commands_parser() -> argparse.ArgumentParser:
    """Shared parent parsers so options work before AND after subcommands."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--file",
        default=argparse.SUPPRESS,
        help="JSON data file (default: ~/.blunder_journal.json or $BLUNDER_JOURNAL_FILE)",
    )
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blunder-journal",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--file",
        default=os.environ.get("BLUNDER_JOURNAL_FILE", DEFAULT_FILE),
        help="JSON data file (default: ~/.blunder_journal.json or $BLUNDER_JOURNAL_FILE)",
    )
    common = _commands_parser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", parents=[common],
                           help="log one painful moment")
    p_add.add_argument("move_number", metavar="MOVE", type=int,
                       help="move number where the pain happened")
    p_add.add_argument("phase", metavar="PHASE",
                       help="opening | middlegame | endgame")
    p_add.add_argument("blunder_type", metavar="TYPE",
                       help="e.g. 'hanging piece', 'missed tactic'")
    p_add.add_argument("cause", metavar="CAUSE",
                       help="your gut hunch, e.g. 'time pressure'")
    p_add.add_argument("-n", "--note", help="optional free-text note")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", parents=[common], help="show journal entries")
    p_list.add_argument("--last", type=int, default=None,
                        help="show only the last N entries")
    p_list.set_defaults(func=cmd_list)

    p_tally = sub.add_parser("tally", parents=[common], help="phase heat counts")
    p_tally.set_defaults(func=cmd_tally)

    p_causes = sub.add_parser("causes", parents=[common], help="top recurring causes")
    p_causes.add_argument("--top", type=int, default=3,
                          help="how many causes to show (default 3)")
    p_causes.set_defaults(func=cmd_causes)

    p_drill = sub.add_parser("drill", parents=[common], help="print a five-minute drill plan")
    p_drill.set_defaults(func=cmd_drill)

    p_muse = sub.add_parser("muse", parents=[common], help="optional LLM musing (no API key)")
    p_muse.add_argument("--endpoint", default=None,
                        help=f"OpenAI-compatible base URL (default: {DEFAULT_ENDPOINT})")
    p_muse.add_argument("--model", default=None,
                        help=f"model name (default: {DEFAULT_MODEL})")
    p_muse.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="seconds to wait for the model")
    p_muse.set_defaults(func=cmd_muse)

    p_demo = sub.add_parser("demo", parents=[common], help="add 8 sample entries to see reports")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: list = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # --file works before or after the subcommand; fall back to env/default.
    args.file = (
        args.file
        or os.environ.get("BLUNDER_JOURNAL_FILE")
        or DEFAULT_FILE
    )
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
