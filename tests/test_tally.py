"""Tests for tally logic and friends (no network, no filesystem)."""

import unittest

from blunder_journal.tally import (
    blunder_type_tally,
    heat_counts,
    infer_phase_from_move,
    phase_tally,
    phase_type_pairs,
    top_causes,
)
from blunder_journal.drill import build_plan, render_plan
from blunder_journal.store import clean_cause, make_entry, normalize_phase


def e(move, phase, btype, cause):
    return make_entry(move, phase, btype, cause)


class PhaseTallyTest(unittest.TestCase):
    def test_counts_include_zero_phases(self):
        entries = [e(5, "opening", "bad trade", "misjudged trade")]
        self.assertEqual(
            phase_tally(entries),
            {"opening": 1, "middlegame": 0, "endgame": 0},
        )

    def test_counts_multiple_phases(self):
        entries = [
            e(5, "opening", "weak pawn move", "unknown opening line"),
            e(30, "middlegame", "hanging piece", "time pressure"),
            e(33, "middlegame", "hanging piece", "time pressure"),
            e(45, "endgame", "weak pawn move", "tiredness"),
        ]
        self.assertEqual(
            phase_tally(entries),
            {"opening": 1, "middlegame": 2, "endgame": 1},
        )

    def test_empty_journal(self):
        self.assertEqual(
            phase_tally([]),
            {"opening": 0, "middlegame": 0, "endgame": 0},
        )

    def test_ignores_bad_phases(self):
        entries = [{"phase": "voidworld"}, e(5, "opening", "x", "y")]
        self.assertEqual(
            phase_tally(entries),
            {"opening": 1, "middlegame": 0, "endgame": 0},
        )


class HeatCountsTest(unittest.TestCase):
    def test_bars_proportional_to_peak(self):
        entries = [
            e(10, "opening", "bad trade", "haste"),
            e(30, "middlegame", "hanging piece", "time pressure"),
            e(31, "middlegame", "hanging piece", "time pressure"),
            e(33, "middlegame", "missed tactic", "haste"),
        ]
        heat = heat_counts(entries)
        self.assertEqual(heat["counts"], {"opening": 1, "middlegame": 3, "endgame": 0})
        self.assertEqual(heat["peak"], 3)
        self.assertEqual(len(heat["bars"]["middlegame"]), 3)
        self.assertEqual(len(heat["bars"]["opening"]), 1)
        self.assertEqual(len(heat["bars"]["endgame"]), 0)
        self.assertLess(heat["bars"]["opening"], heat["bars"]["middlegame"][-1])

    def test_empty_journal_bars(self):
        heat = heat_counts([])
        self.assertEqual(heat["peak"], 0)
        self.assertEqual(heat["bars"], {"opening": "", "middlegame": "", "endgame": ""})


class TopCausesTest(unittest.TestCase):
    def test_recurring_causes_ranked(self):
        entries = [
            e(10, "opening", "a", "Time pressure!"),
            e(20, "middlegame", "b", "  time   pressure "),
            e(30, "endgame", "c", "tiredness"),
            e(40, "endgame", "d", "tiredness"),
            e(50, "endgame", "e", "tiredness"),
        ]
        self.assertEqual(
            top_causes(entries, limit=3),
            [("tiredness", 3), ("time pressure", 2)],
        )

    def test_single_causes_are_noise(self):
        entries = [e(10, "opening", "a", "storm outside"), e(11, "middlegame", "b", "rain")]
        self.assertEqual(top_causes(entries, limit=3), [])

    def test_limit_caps_results(self):
        entries = [
            e(1, "opening", "a", "haste"),
            e(2, "opening", "b", "haste"),
            e(3, "opening", "c", "tilt"),
            e(4, "opening", "d", "tilt"),
            e(5, "opening", "e", "laziness"),
            e(6, "opening", "f", "laziness"),
        ]
        self.assertEqual(len(top_causes(entries, limit=2)), 2)

    def test_ties_break_alphabetically(self):
        entries = [
            e(1, "opening", "a", "zeta"),
            e(2, "opening", "b", "alpha"),
            e(3, "opening", "c", "zeta"),
            e(4, "opening", "d", "alpha"),
        ]
        self.assertEqual(
            top_causes(entries, limit=3),
            [("alpha", 2), ("zeta", 2)],
        )


class TypeTallyTest(unittest.TestCase):
    def test_blunder_type_counts(self):
        entries = [
            e(10, "middlegame", "Hanging Piece", "time pressure"),
            e(11, "middlegame", "hanging piece", "haste"),
            e(40, "endgame", "weak pawn move", "tiredness"),
        ]
        types = blunder_type_tally(entries)
        self.assertEqual(types["hanging piece"], 2)
        self.assertEqual(types["weak pawn move"], 1)

    def test_phase_type_pairs(self):
        entries = [
            e(30, "middlegame", "hanging piece", "time pressure"),
            e(33, "middlegame", "hanging piece", "haste"),
        ]
        pairs = phase_type_pairs(entries)
        self.assertEqual(pairs[("middlegame", "hanging piece")], 2)


class PhaseHelpersTest(unittest.TestCase):
    def test_infer_phase_from_move(self):
        self.assertEqual(infer_phase_from_move(5), "opening")
        self.assertEqual(infer_phase_from_move(12), "opening")
        self.assertEqual(infer_phase_from_move(25), "middlegame")
        self.assertEqual(infer_phase_from_move(40), "endgame")

    def test_normalize_phase_aliases(self):
        self.assertEqual(normalize_phase("Mid"), "middlegame")
        self.assertEqual(normalize_phase("End"), "endgame")
        self.assertEqual(normalize_phase(" Opening "), "opening")
        with self.assertRaises(ValueError):
            normalize_phase("retrograde")


class CleanCauseTest(unittest.TestCase):
    def test_cleaning(self):
        self.assertEqual(clean_cause("  Time   Pressure! "), "time pressure")
        self.assertEqual(clean_cause(""), "unknown")


class EntryValidationTest(unittest.TestCase):
    def test_move_number_bounds(self):
        for bad in (0, -3, 501):
            with self.assertRaises(ValueError):
                make_entry(bad, "opening", "x", "y")

    def test_bad_phase_rejected(self):
        with self.assertRaises(ValueError):
            make_entry(10, "someday", "x", "y")


class DrillPlanTest(unittest.TestCase):
    def test_plan_has_five_blocks(self):
        entries = [
            e(10, "opening", "weak pawn move", "unknown opening line"),
            e(30, "middlegame", "hanging piece", "time pressure"),
            e(31, "middlegame", "hanging piece", "time pressure"),
            e(40, "endgame", "overworked piece", "tiredness"),
        ]
        plan = build_plan(entries)
        self.assertEqual(len(plan["blocks"]), 5)
        text = render_plan(plan)
        self.assertIn("middlegame", text)
        self.assertIn("time pressure", text)

    def test_plan_deterministic(self):
        entries = [e(30, "middlegame", "hanging piece", "time pressure")]
        first = render_plan(build_plan(entries))
        second = render_plan(build_plan(entries))
        self.assertEqual(first, second)

    def test_empty_journal_still_five_blocks(self):
        plan = build_plan([])
        self.assertEqual(len(plan["blocks"]), 5)


if __name__ == "__main__":
    unittest.main()
