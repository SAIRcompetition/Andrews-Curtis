"""Acceptance row 1: all 424 converted training paths verify OK and the
aggregate statistics equal the [Verified] table in DESIGN.md §1.5."""

import unittest

from verifier import canon, core
from tests import util


def stats(values):
    xs = sorted(values)
    return xs[0], xs[len(xs) // 2], xs[-1], round(sum(xs) / len(xs), 1)


class TestTrainingReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limits = util.load_manifest()["limits"]
        cls.training = util.load_training()

    def test_all_424_accepted_and_stats_match(self):
        entries = self.training["instances"]
        self.assertEqual(len(entries), 424)
        lens, peaks, works = [], [], []
        for e in entries:
            v = core.verify(util.training_challenge(e), e["moves"],
                            e["move_spec_version"], self.limits)
            self.assertTrue(v["ok"], (e["training_id"], v))
            self.assertEqual(v["length"], e["length"])
            self.assertEqual(v["peak_total_relator_length"],
                             e["peak_total_relator_length"])
            self.assertEqual(v["work"], e["work"])
            self.assertEqual(v["certificate_hash"], e["certificate_hash"])
            lens.append(v["length"])
            peaks.append(v["peak_total_relator_length"])
            works.append(v["work"])
        self.assertEqual(stats(lens), (7, 26, 159, 33.6))
        self.assertEqual(stats(peaks), (7, 14, 25, 14.7))
        self.assertEqual(stats(works), (43, 229, 2161, 347.0))

    def test_training_file_hash_headers(self):
        self.assertEqual(self.training["move_spec_version"], "ac-r2-v1")
        self.assertEqual(self.training["move_spec_hash"],
                         canon.move_spec_hash(core.MOVE_TABLE))


if __name__ == "__main__":
    unittest.main()
