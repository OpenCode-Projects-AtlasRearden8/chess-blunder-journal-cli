# chess-blunder-journal

Turn post-game feelings into fixes. Log each painful moment - move number, phase, blunder type, likely cause - then print phase-tally heat counts, top recurring causes, and a printable five-minute drill plan built from your own pattern pile.

Made by **Asdale Dynamics, LLC** (Dylan Asdale) - plain-English, beginner-friendly tools that are local-first, tested, and free of secrets.

## Why this is different

- **chess-tactics-postmortem-webapp** is for full game review (PGN, engine analysis).
- **chess-opening-journal-cli** is for repertoire study (which lines you play).
- **blunder-journal** is for *you*: the human habits behind the blunders. No chess boards, no engines - just an honest log and a five-minute plan.

## Quick start

Requires Python 3.9+. No third-party dependencies.

```bash
pip install .
blunder-journal demo          # 8 sample entries so the reports sing
blunder-journal tally         # phase heat counts
blunder-journal causes        # top recurring causes
blunder-journal drill         # your five-minute drill plan
blunder-journal list --last 3
```

## Logging a painful moment

```bash
blunder-journal add 34 middlegame "hanging piece" "time pressure"
blunder-journal add 12 opening "weak pawn move" "unknown opening line" -n "misjudged g6 pawn shield"
```

Positional arguments: `MOVE  PHASE  TYPE  CAUSE`, plus an optional `--note`.

- `MOVE`: move number where it went wrong (1-500)
- `PHASE`: `opening`, `middlegame` (or `mid`), `endgame` (or `end`)
- `TYPE`: your words, e.g. `hanging piece`, `missed tactic`, `bad trade`
- `CAUSE`: your gut hunch, e.g. `time pressure`, `tiredness`, `tilt`

## Where your data lives

Local-first: a single JSON file at `~/.blunder_journal.json`. Override it with:

```bash
blunder-journal tally --file ./my-club-year.json
# or
export BLUNDER_JOURNAL_FILE=~/.blunder_journal.json
```

Nothing is uploaded unless you explicitly ask for `muse`. No secrets or personal data are ever written to any file by this tool.

## The five-minute drill plan

`blunder-journal drill` turns your pattern pile into up to five sixty-second blocks: the hottest phase, your most common blunder type, one habit-reset per top recurring cause, and a recap. Deterministic by design - the same journal, the same plan. Print it, tape it to your monitor, do it before your next game.

## Optional: plain-English musings (LLM, no API key)

`blunder-journal muse` asks an OpenAI-compatible endpoint - **Ollama included** - for a short, warm, plain-English read of your pattern pile. No API key is required or sent.

```bash
# with default Ollama settings (default model: llama3.2)
ollama serve &
ollama pull llama3.2
blunder-journal muse

# any other OpenAI-compatible server
blunder-journal muse --endpoint http://localhost:8000/v1 --model my-model
# or: export BLUNDER_JOURNAL_ENDPOINT=... and BLUNDER_JOURNAL_MODEL=...
```

Offline? The rest of the journal works fine without the muse - you get a friendly hint instead of a stack trace.

## Example output

```
$ blunder-journal tally
Phase heat counts
----------------------------------------------
opening      2  ▅▅
middlegame   4  ████
endgame      2  ▅▅
----------------------------------------------
Hottest phase: middlegame (4 of 8 blunders)

$ blunder-journal causes
Top recurring causes
----------------------------------------------
  2x  time pressure
  2x  tiredness
```

## How to run tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT - see [LICENSE](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.
