"""Frozen-data invariants: manifest schema (§3.1), challenge pool
composition (§2.1–§2.3), and MS formula consistency (§1.1, D-2)."""

import collections
import csv
import unittest

from acms_verify import core
from tests import util


class TestManifestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.challenges = cls.manifest["challenges"]

    def test_pool_composition(self):
        self.assertEqual(len(self.challenges), 550)
        for c in self.challenges:
            self.assertEqual(c["status_at_freeze"], "open")
            self.assertTrue(c["scored"])
            self.assertEqual(c["base_score"], 1)
            self.assertEqual(c["move_spec_version"], "ac-r2-v1")
            self.assertEqual(c["target_relators"], [[1], [2]])
            self.assertEqual(c["generators"], ["x", "y"])

    def test_ids_sequential_and_unique(self):
        ids = [c["challenge_id"] for c in self.challenges]
        self.assertEqual(ids, ["ms-v1-%04d" % i
                               for i in range(1, len(ids) + 1)])

    def test_limits_frozen_values(self):
        self.assertEqual(self.manifest["limits"],
                         {"max_path_length": 100000,
                          "max_total_relator_length": 10000,
                          "max_work": 5000000})

    def test_initial_relators_reduced_and_match_ms_formula(self):
        for c in self.challenges:
            r0, r1 = c["initial_relators"]
            self.assertEqual(list(core.free_reduce(r0)), r0, c["challenge_id"])
            self.assertEqual(list(core.free_reduce(r1)), r1, c["challenge_id"])
            n, wv = c["n"], c["w_vector"]
            self.assertEqual(
                tuple(r0),
                core.free_reduce([-1] + [2] * n + [1] + [-2] * (n + 1)))
            # D-2 frozen convention: r1 = x w^-1
            self.assertEqual(
                tuple(r1),
                core.free_reduce((1,) + core.invert(tuple(wv))))
            self.assertEqual(
                sum(1 if a == 1 else -1 for a in wv if abs(a) == 1), 0)

    def test_reported_class_metadata(self):
        sizes = collections.Counter(
            c["source"]["reported_class"] for c in self.challenges)
        hist = collections.Counter(sizes.values())
        self.assertEqual(dict(hist),
                         {1: 193, 2: 16, 3: 19, 4: 10, 5: 8, 6: 5,
                          8: 4, 9: 2, 16: 1, 22: 1, 34: 1, 36: 1})
        self.assertEqual(len(sizes), 261)
        for c in self.challenges:
            src = c["source"]
            self.assertIs(src["reported_class_normative"], False)
            self.assertEqual(src["reported_class_size"],
                             sizes[src["reported_class"]])

    def test_metadata_csv_denominator(self):
        with open(util.MANIFEST_PATH.parent / "ms1190_metadata.csv",
                  encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 1190)
        by_status = collections.Counter(r["status_at_freeze"] for r in rows)
        self.assertEqual(by_status,
                         {"certified": 424, "uncertified": 216, "open": 550})
        scored_ids = [r["challenge_id"] for r in rows if r["scored"] == "true"]
        self.assertEqual(scored_ids,
                         [c["challenge_id"] for c in self.challenges])
        for r in rows:
            self.assertEqual(r["scored"] == "true",
                             r["status_at_freeze"] == "open")
            self.assertEqual(bool(r["training_id"]),
                             r["status_at_freeze"] == "certified")


if __name__ == "__main__":
    unittest.main()
