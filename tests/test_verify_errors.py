"""Acceptance rows 2, 2b, 3 and §4.2 error-code contract.

Every per-move error carries a 0-based ``move_index``.
"""

import time
import unittest

from verifier import core, stable_core
from tests import util


class TestVerifyErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.limits = cls.manifest["limits"]
        training = util.load_training()["instances"]
        cls.entry = min(training, key=lambda e: e["length"])
        cls.challenge = util.training_challenge(cls.entry)

    def verify(self, moves, limits=None, version=core.MOVE_SPEC_VERSION,
               challenge=None):
        return core.verify(challenge or self.challenge, moves, version,
                           limits or self.limits)

    # -- acceptance row 2: illegal move ids, with index ------------------
    def test_bad_move_ids(self):
        for bad in (-1, 14, 1.5, "3", None, True, [], {}):
            v = self.verify([0, bad])
            self.assertEqual(v["code"], "E_BAD_MOVE_ID", bad)
            self.assertEqual(v["move_index"], 1, bad)
            self.assertFalse(v["ok"])

    def test_spec_mismatch(self):
        v = self.verify(self.entry["moves"], version="ac-r1-v0")
        self.assertEqual(v["code"], "E_SPEC_MISMATCH")
        self.assertEqual(v["expected"], "ac-r2-v1")

    def test_path_too_long(self):
        v = self.verify([6, 7] * 3, dict(self.limits, max_path_length=5))
        self.assertEqual(v["code"], "E_PATH_TOO_LONG")
        self.assertIsNone(v["move_index"])

    def test_length_limit_carries_index(self):
        pump = {"challenge_id": "pump", "move_spec_version": "ac-r2-v1",
                "initial_relators": [[1, 2], [1, 1, 2]],
                "target_relators": [[1], [2]]}
        v = self.verify([2] * 50, dict(self.limits,
                                       max_total_relator_length=20),
                        challenge=pump)
        self.assertEqual(v["code"], "E_LENGTH_LIMIT")
        # r0 grows by 3 per move from total 5: first total > 20 is 23,
        # reached after the 6th multiplication (index 5).
        self.assertEqual(v["move_index"], 5)
        self.assertEqual(v["total_relator_length"], 23)

    # -- acceptance row 2b: work budget under production limits ----------
    def test_work_budget_production_limits(self):
        """A legal path that exceeds max_work = 5_000_000 while staying
        inside the length limits must fail fast (well under 30 s)."""
        pump = {"challenge_id": "pump", "move_spec_version": "ac-r2-v1",
                "initial_relators": [[1, 2], [1, 1, 2]],
                "target_relators": [[1], [2]]}
        # Multiplications double-ish the total length (Fibonacci-style)
        # up to ~9000, then conjugations hold it there while work grows.
        grow = []
        state = ((1, 2), (1, 1, 2))
        while True:
            m = 2 if len(state[0]) <= len(state[1]) else 4
            nxt = core.apply_move(state, m)
            if len(nxt[0]) + len(nxt[1]) > 9000:
                break
            state = nxt
            grow.append(m)
        moves = grow + [6, 7] * 400
        t0 = time.monotonic()
        v = self.verify(moves, challenge=pump)
        elapsed = time.monotonic() - t0
        self.assertEqual(v["code"], "E_WORK_BUDGET")
        self.assertGreater(v["work"], self.limits["max_work"])
        self.assertLess(elapsed, 30.0)

    # -- acceptance row 3: legal moves, wrong endpoint -------------------
    def test_truncated_real_path(self):
        v = self.verify(self.entry["moves"][:-1])
        self.assertEqual(v["code"], "E_NOT_TARGET")

    def test_wrong_order_endpoint(self):
        yx = {"challenge_id": "yx", "move_spec_version": "ac-r2-v1",
              "initial_relators": [[2], [1]], "target_relators": [[1], [2]]}
        v = self.verify([], challenge=yx)
        self.assertEqual(v["code"], "E_NOT_TARGET")
        self.assertEqual(v["final_shape"], [1, 1])

    def test_moves_not_array_is_malformed(self):
        v = self.verify({"0": 1})
        self.assertEqual(v["code"], "E_MALFORMED")


class TestStableVerifyErrors(unittest.TestCase):
    """The same §4.2 contract under sac-r8-v1, plus the one code the
    stable spec adds: E_MOVE_NOT_APPLICABLE."""

    SUFFIX = [16, 15]

    @classmethod
    def setUpClass(cls):
        cls.limits = util.load_manifest()["limits"]
        cls.entry = min(util.load_stable_training()["instances"],
                        key=lambda e: e["length"])
        cls.challenge = util.training_challenge(cls.entry)
        cls.xy = {"challenge_id": "xy", "move_spec_version": "sac-r8-v1",
                  "initial_relators": [[1], [2]], "target_relators": []}
        cls.pump = {"challenge_id": "pump", "move_spec_version": "sac-r8-v1",
                    "initial_relators": [[1, 2], [1, 1, 2]],
                    "target_relators": []}

    def verify(self, moves, limits=None, version=stable_core.MOVE_SPEC_VERSION,
               challenge=None):
        return stable_core.verify(challenge or self.challenge, moves,
                                  version, limits or self.limits)

    def test_accepts_the_training_certificate(self):
        v = self.verify(self.entry["moves"])
        self.assertTrue(v["ok"], v)
        self.assertEqual(v["length"], self.entry["length"])
        self.assertEqual(v["work"], self.entry["work"])
        self.assertEqual(v["certificate_hash"], self.entry["certificate_hash"])

    def test_bad_move_ids(self):
        for bad in (-1, 257, 300, 1.5, "3", None, True, [], {}):
            v = self.verify([0, bad])
            self.assertEqual(v["code"], "E_BAD_MOVE_ID", bad)
            self.assertEqual(v["move_index"], 1, bad)
            self.assertEqual(v["move"], bad, bad)
            self.assertFalse(v["ok"])

    def test_move_id_256_is_legal(self):
        """The last row exists: 256 (r7 <- g8^-1 r7 g8) is in range, it
        is simply not applicable at rank 2 — the relator index is
        checked before the generator, so the reason names the relator."""
        v = self.verify([256], challenge=self.xy)
        self.assertEqual(v["code"], "E_MOVE_NOT_APPLICABLE")
        self.assertEqual(v["reason"], "relator_out_of_rank")
        self.assertEqual(stable_core.MOVE_TABLE[256],
                         {"id": 256, "category": "conjugation", "relator": 7,
                          "conjugator": -8, "inverse": 255})

    def test_spec_mismatch(self):
        v = self.verify(self.entry["moves"], version="ac-r2-v1")
        self.assertEqual(v["code"], "E_SPEC_MISMATCH")
        self.assertEqual(v["expected"], "sac-r8-v1")
        self.assertEqual(v["got"], "ac-r2-v1")

    def test_path_too_long(self):
        v = self.verify([6, 7] * 3, dict(self.limits, max_path_length=5))
        self.assertEqual(v["code"], "E_PATH_TOO_LONG")
        self.assertIsNone(v["move_index"])

    def test_not_applicable_reasons_with_index(self):
        cases = [
            ([16, 1], 1, "relator_out_of_rank"),
            ([16, 8], 1, "generator_out_of_rank"),
            ([14] * 7, 6, "max_rank_exceeded"),
            ([0, 15], 1, "destabilize_precondition"),
            ([4, 15], 1, "destabilize_precondition"),
        ]
        for moves, index, reason in cases:
            v = self.verify(moves, challenge=self.xy)
            self.assertEqual(v["code"], "E_MOVE_NOT_APPLICABLE", moves)
            self.assertEqual(v["move_index"], index, moves)
            self.assertEqual(v["reason"], reason, moves)
            self.assertEqual(v["move"], moves[index], moves)
            self.assertFalse(v["ok"])

    def test_not_applicable_on_a_long_relator(self):
        v = self.verify([15], challenge=self.pump)
        self.assertEqual((v["code"], v["move_index"], v["reason"]),
                         ("E_MOVE_NOT_APPLICABLE", 0,
                          "destabilize_precondition"))

    def test_bad_move_id_beats_not_applicable(self):
        """Priority: the id range check runs before applicability."""
        v = self.verify([257], challenge=self.xy)
        self.assertEqual(v["code"], "E_BAD_MOVE_ID")

    def test_not_applicable_beats_length_limit(self):
        """Priority: applicability runs before the relator-length check.

        The path stabilizes to rank 8 (legal, total 8), then tries once
        more under a length limit that the successful move would also
        have broken."""
        v = self.verify([14] * 7, dict(self.limits,
                                       max_total_relator_length=8),
                        challenge=self.xy)
        self.assertEqual(v["code"], "E_MOVE_NOT_APPLICABLE")
        self.assertEqual(v["reason"], "max_rank_exceeded")

    def test_length_limit_carries_index(self):
        v = self.verify([2] * 50, dict(self.limits,
                                       max_total_relator_length=20),
                        challenge=self.pump)
        self.assertEqual(v["code"], "E_LENGTH_LIMIT")
        self.assertEqual(v["move_index"], 5)
        self.assertEqual(v["total_relator_length"], 23)

    def test_work_budget(self):
        v = self.verify([6, 7] * 200, dict(self.limits, max_work=200),
                        challenge=self.pump)
        self.assertEqual(v["code"], "E_WORK_BUDGET")
        self.assertGreater(v["work"], 200)

    def test_not_target_final_shape_is_a_list_of_relator_lengths(self):
        v = self.verify([], challenge=self.xy)
        self.assertEqual(v["code"], "E_NOT_TARGET")
        self.assertEqual(v["final_shape"], [1, 1])
        v = self.verify([16], challenge=self.xy)
        self.assertEqual(v["final_shape"], [1])
        v = self.verify([14, 14], challenge=self.xy)
        self.assertEqual(v["final_shape"], [1, 1, 1, 1])
        v = self.verify(self.entry["moves"][:-2])
        self.assertEqual(v["code"], "E_NOT_TARGET")
        self.assertEqual(v["final_shape"], [1, 1])

    def test_empty_target_is_reached_only_by_the_empty_state(self):
        v = self.verify(self.SUFFIX, challenge=self.xy)
        self.assertTrue(v["ok"], v)
        self.assertEqual(v["length"], 2)
        self.assertEqual(v["work"], 2 + 1 + 0)

    def test_moves_not_array_is_malformed(self):
        v = self.verify({"0": 1})
        self.assertEqual(v["code"], "E_MALFORMED")

    def test_organizer_side_data_bugs_raise(self):
        bad = dict(self.xy, initial_relators=[[1, -1], [2]])
        with self.assertRaises(ValueError):
            self.verify([], challenge=bad)
        bad = dict(self.xy, initial_relators=[[3], [2]])
        with self.assertRaises(ValueError):
            self.verify([], challenge=bad)
        bad = dict(self.xy, initial_relators=[[1]] * 9)
        with self.assertRaises(ValueError):
            self.verify([], challenge=bad)


if __name__ == "__main__":
    unittest.main()
