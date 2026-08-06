"""Acceptance rows 6–9 (DESIGN.md §11) for the scoring engine,
including the §5.6 worked example frame by frame and a non-uniform
V_i fixture (1, 7, 100) as required by D-8."""

import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scoring.engine import ScoringEngine, display_score  # noqa: E402


def mini_manifest(base_scores):
    return {
        "manifest_hash": "sha256:test",
        "challenges": [
            {"challenge_id": cid, "scored": True, "base_score": v}
            for cid, v in base_scores.items()
        ],
    }


def engine(base_scores={"c1": 1}):
    return ScoringEngine(mini_manifest(base_scores), "acms-verify 0.1.0")


class TestBestReplacement(unittest.TestCase):
    """Acceptance row 6: shorter replaces, longer does not."""

    def test_shorter_replaces_longer_keeps(self):
        e = engine()
        e.record_accepted("A", "c1", 40, "t1", 1)
        self.assertEqual(e.best[("A", "c1")], 40)
        e.record_accepted("A", "c1", 38, "t2", 2)
        self.assertEqual(e.best[("A", "c1")], 38)
        e.record_accepted("A", "c1", 45, "t3", 3)
        self.assertEqual(e.best[("A", "c1")], 38)


class TestWorkedExample(unittest.TestCase):
    """Acceptance rows 7–9: the five stages of §5.6, V_i = 1."""

    def totals(self, run):
        return {row["team"]: row["total"] for row in run["leaderboard"]}

    def test_five_stages(self):
        e = engine()
        r1 = e.record_accepted("A", "c1", 40, "t1", 1)
        self.assertEqual(self.totals(r1), {"A": Fraction(1)})

        r2 = e.record_accepted("B", "c1", 40, "t2", 2)
        self.assertEqual(self.totals(r2),
                         {"A": Fraction(1, 2), "B": Fraction(1, 2)})

        r3 = e.record_accepted("C", "c1", 40, "t3", 3)
        self.assertEqual(self.totals(r3),
                         {t: Fraction(1, 4) for t in "ABC"})

        # Stage 4: D reaches 38 — A/B/C all drop to zero at once.
        r4 = e.record_accepted("D", "c1", 38, "t4", 4)
        self.assertEqual(self.totals(r4),
                         {"A": Fraction(0), "B": Fraction(0),
                          "C": Fraction(0), "D": Fraction(1)})
        self.assertEqual(r4["leaderboard"][0]["team"], "D")

        # Stage 5: A matches 38.
        r5 = e.record_accepted("A", "c1", 38, "t5", 5)
        self.assertEqual(self.totals(r5),
                         {"A": Fraction(1, 2), "B": Fraction(0),
                          "C": Fraction(0), "D": Fraction(1, 2)})
        # D reached 1/2 via A's event, same event key; ties broken by
        # earliest time-of-current-total then name — both changed at t5,
        # so alphabetical: A before D.
        self.assertEqual([row["team"] for row in r5["leaderboard"]][:2],
                         ["A", "D"])

        # Acceptance row 9: First Solver is A, immutable end to end.
        self.assertEqual(e.first_solver["c1"]["team"], "A")
        self.assertEqual(e.first_solver["c1"]["submission_id"], 1)

    def test_challenge_view_fields(self):
        e = engine()
        e.record_accepted("A", "c1", 40, "t1", 1)
        e.record_accepted("D", "c1", 38, "t2", 2)
        view = e.challenge_view("c1", for_team="A")
        self.assertEqual(view["current_best_length"], 38)
        self.assertEqual(view["current_best_solver"], "D")
        self.assertEqual(view["k_teams"], 1)
        self.assertEqual(view["first_solver"], "A")
        self.assertEqual(view["first_solved_at"], "t1")
        self.assertEqual(view["my_best_length"], 40)


class TestKSharing(unittest.TestCase):
    """Acceptance row 8: k = 1..4 gives V, V/2, V/4, V/8 — exactly."""

    def test_uniform_v(self):
        e = engine()
        shares = {1: Fraction(1), 2: Fraction(1, 2),
                  3: Fraction(1, 4), 4: Fraction(1, 8)}
        for i, team in enumerate("ABCD", 1):
            run = e.record_accepted(team, "c1", 40, "t%d" % i, i)
            totals = {r["team"]: r["total"] for r in run["leaderboard"]}
            for t in list("ABCD")[:i]:
                self.assertEqual(totals[t], shares[i])

    def test_non_uniform_v(self):
        """D-8 fixture: V_i = 1, 7, 100 — the multiplication path must
        not be short-circuited by an all-ones assumption."""
        e = engine({"c1": 1, "c7": 7, "c100": 100})
        e.record_accepted("A", "c1", 10, "t1", 1)
        e.record_accepted("A", "c7", 10, "t2", 2)
        e.record_accepted("B", "c7", 10, "t3", 3)
        e.record_accepted("B", "c100", 10, "t4", 4)
        e.record_accepted("C", "c100", 10, "t5", 5)
        run = e.record_accepted("D", "c100", 9, "t6", 6)
        totals = {r["team"]: r["total"] for r in run["leaderboard"]}
        self.assertEqual(totals["A"], Fraction(1) + Fraction(7, 2))
        self.assertEqual(totals["B"], Fraction(7, 2))  # c100 zeroed by D
        self.assertEqual(totals["C"], Fraction(0))
        self.assertEqual(totals["D"], Fraction(100))
        self.assertEqual([r["team"] for r in run["leaderboard"]][0], "D")

    def test_display_rounding_half_even(self):
        self.assertEqual(display_score(Fraction(1, 8)), "0.1250")
        self.assertEqual(display_score(Fraction(1, 3)), "0.3333")
        self.assertEqual(display_score(Fraction(100)), "100.0000")
        # half-even at the 4th decimal: 0.00005 -> 0.0000, 0.00015 -> 0.0002
        self.assertEqual(display_score(Fraction(5, 100000)), "0.0000")
        self.assertEqual(display_score(Fraction(15, 100000)), "0.0002")
        # exact rounding of a near-tie rational that double rounding
        # (Decimal 28-digit divide, then quantize) would misdisplay
        self.assertEqual(display_score(Fraction(10**29 + 1, 2 * 10**33)),
                         "0.0001")
        self.assertEqual(display_score(Fraction(-1, 8)), "-0.1250")


class TestScoringRuns(unittest.TestCase):
    def test_runs_recorded_and_reproducible(self):
        e = engine()
        e.record_accepted("A", "c1", 40, "t1", 1)
        e.record_accepted("B", "c1", 38, "t2", 2)
        self.assertEqual([r["scoring_run_id"] for r in e.scoring_runs], [1, 2])
        for r in e.scoring_runs:
            self.assertEqual(r["manifest_hash"], "sha256:test")
            self.assertEqual(r["verifier_version"], "acms-verify 0.1.0")
        # recompute is a pure function of best: replaying gives the
        # same leaderboard.
        e2 = engine()
        e2.record_accepted("A", "c1", 40, "t1", 1)
        run = e2.record_accepted("B", "c1", 38, "t2", 2)
        self.assertEqual(run["leaderboard"],
                         e.scoring_runs[1]["leaderboard"])

    def test_first_solver_is_argmin_under_out_of_order_ingestion(self):
        """§5.3: first_solver = argmin (received_at, submission_id),
        even if verification completes out of event order."""
        e = engine()
        e.record_accepted("B", "c1", 40, "t9", 2)
        e.record_accepted("A", "c1", 40, "t9", 1)   # same instant, earlier id
        self.assertEqual(e.first_solver["c1"]["team"], "A")
        e.record_accepted("C", "c1", 30, "t0", 3)   # earlier receipt, later id
        self.assertEqual(e.first_solver["c1"]["team"], "C")
        # ...but never displaced by a later, shorter path
        e.record_accepted("D", "c1", 10, "t5", 4)
        self.assertEqual(e.first_solver["c1"]["team"], "C")

    def test_unknown_challenge_rejected(self):
        e = engine()
        with self.assertRaises(KeyError):
            e.record_accepted("A", "nope", 40, "t1", 1)
        with self.assertRaises(ValueError):
            e.record_accepted("A", "c1", 40.0, "t1", 1)


if __name__ == "__main__":
    unittest.main()
