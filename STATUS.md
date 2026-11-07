# STATUS.md - chess-blunder-journal

## What was built

A local-first Python CLI that turns post-game feelings into fixes. You log
each painful moment (move number, phase, blunder type, likely cause), and the
tool reports:

- **Phase-tally heat counts** - where in the game you leak most
  (opening / middlegame / endgame), printed as text heat bars.
- **Top recurring causes** - normalized cause strings counted; single
  one-offs are treated as noise, repeats become patterns.
- **A printable five-minute drill plan** - up to five 60-second blocks built
  from your own pattern pile (hottest phase, worst blunder type, habit
  reset per top cause, recap). Deterministic: same journal, same plan.
- **Optional plain-English musings** - `muse` uses any OpenAI-compatible
  endpoint (Ollama's `/v1` included) with **no API key**. Implemented with
  stdlib `urllib` only; degrades to a friendly offline hint.
- **Sample data** - `demo` command adds 8 realistic entries so reports work
  immediately.

Distinct sibling projects (not included here): full game review lives in
`chess-tactics-postmortem-webapp`; opening repertoire study in
`chess-opening-journal-cli`.

## Layout

- `blunder_journal/store.py` - entry model, validation, JSON storage
- `blunder_journal/tally.py` - tally logic (phases, heat bars, causes, types)
- `blunder_journal/drill.py` - five-minute drill plan builder + renderer
- `blunder_journal/muse.py` - OpenAI-compatible client (no key, no SDKs)
- `blunder_journal/cli.py` - argparse CLI (`add`, `list`, `tally`, `causes`,
  `drill`, `muse`, `demo`)
- `tests/test_tally.py` - 20 tests for tally/drill/store logic
- `pyproject.toml`, `README.md`, `LICENSE` (MIT)

## How to run it

```bash
python3 -m blunder_journal.cli --help        # no install needed
# or install the console script:
pip install .
blunder-journal demo
blunder-journal tally
blunder-journal causes
blunder-journal drill
blunder-journal add 34 middlegame "hanging piece" "time pressure"
blunder-journal muse --endpoint http://localhost:11434/v1 --model llama3.2
```

Data: single JSON file, default `~/.blunder_journal.json`; override with
`--file` (works before or after the subcommand) or
`BLUNDER_JOURNAL_FILE`. No network access unless `muse` is invoked.

## Verification results

Environment: Python 3.13.5, Linux.

- `python3 -m unittest discover -s tests -v` → **20 tests, OK**.
- CLI smoke-tested end to end with a temp data file (`/tmp/opencode/bj-test.json`):
  `demo` (8 entries), `tally` (correct heat bars, hottest phase), `causes`
  (2x time pressure, 2x tiredness), `drill` (5 blocks incl. cause fixes),
  `list --last 3`, `add` (validation, saved to file), `--version`.
- `--file` verified in all three positions: after subcommand, before
  subcommand, and via `BLUNDER_JOURNAL_FILE` env var.
- `muse` verified offline: unreachable endpoint returns a friendly
  plain-English hint (Ollama `ollama serve` + `ollama pull` instructions),
  no stack trace. (No live model server was available in this workspace.)
- Package install verified twice: system pip (`--break-system-packages` was
  required by PEP 668 on this host) and a clean `python3 venv`
  (`/tmp/opencode/bj-venv`); both produced a working `blunder-journal`
  console script. Build artifacts were cleaned up afterwards.
- No third-party runtime dependencies. No secrets, keys, or personal data
  in any file.

## Known gaps

- The `muse` path was verified only against an unreachable endpoint
  (graceful fallback). Response parsing assumes standard OpenAI
  `chat/completions` shape; streaming is not supported.
- Phase is user-supplied; `infer_phase_from_move` exists for callers/tests
  but the CLI does not auto-derive phase from move number.
- Drill plan is rule-based (60-second blocks, fixed drill library for
  common blunder types); it does not read PGNs or connect to engines.
- One install note: this workspace's Python is externally managed, so a
  direct `pip install .` needs `--break-system-packages` (a plain venv
  install needs nothing extra).
- No CI workflow, packaging to PyPI, or shell completions yet.
