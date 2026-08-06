"""Acceptance rows 2, 2b, 3 and §4.2 error-code contract.

Every per-move error carries a 0-based ``move_index``.
"""

import time
import unittest

from acms_verify import core
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


if __name__ == "__main__":
    unittest.main()
