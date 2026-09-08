"""Acceptance row 1, stable track: all 424 sac-r8-v1 training paths
verify OK with the pinned statistics, and each is exactly its ac-r2-v1
counterpart plus the two-move canonicalization suffix."""

import unittest

from acms_verify import canon, core, stable_core
from tests import util

#: Aggregate statistics of the 424 stable paths (min, median, max, mean).
LEN_STATS = (9, 28, 161, 35.6)
PEAK_STATS = (7, 14, 25, 14.7)
WORK_STATS = (44, 230, 2162, 348.0)

#: The suffix that turns an ac-r2-v1 certificate into a sac-r8-v1 one,
#: and what it costs: destabilize r1 (total 2 -> 1), then r0 (1 -> 0).
SUFFIX = [16, 15]
DELTA = {"length": 2, "peak_total_relator_length": 0, "work": 1}


def stats(values):
    xs = sorted(values)
    return xs[0], xs[len(xs) // 2], xs[-1], round(sum(xs) / len(xs), 1)


class TestStableTrainingReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limits = util.load_manifest()["limits"]
        cls.training = util.load_training()
        cls.stable = util.load_stable_training()

    def test_all_424_accepted_and_stats_match(self):
        entries = self.stable["instances"]
        self.assertEqual(len(entries), 424)
        lens, peaks, works = [], [], []
        for e in entries:
            v = stable_core.verify(util.training_challenge(e), e["moves"],
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
        self.assertEqual(stats(lens), LEN_STATS)
        self.assertEqual(stats(peaks), PEAK_STATS)
        self.assertEqual(stats(works), WORK_STATS)
        self.assertEqual(self.stable["length_stats"],
                         dict(zip(("min", "median", "max", "mean"),
                                  LEN_STATS)))

    def test_each_entry_is_its_ac_counterpart_plus_the_suffix(self):
        ac = {e["training_id"]: e for e in self.training["instances"]}
        stable = {e["training_id"]: e for e in self.stable["instances"]}
        self.assertEqual(set(ac), set(stable))
        for tid, e in sorted(stable.items()):
            a = ac[tid]
            self.assertEqual(e["moves"], a["moves"] + SUFFIX, tid)
            self.assertEqual(e["initial_relators"], a["initial_relators"], tid)
            self.assertEqual(e["generators"], a["generators"], tid)
            self.assertEqual(e["target_relators"], [], tid)
            self.assertEqual(a["target_relators"], [[1], [2]], tid)
            for key, delta in DELTA.items():
                self.assertEqual(e[key], a[key] + delta, (tid, key))
            for key in ("family", "n", "w", "w_vector",
                        "prototype_path_length"):
                self.assertEqual(e[key], a[key], (tid, key))
            self.assertNotEqual(e["certificate_hash"], a["certificate_hash"],
                                tid)

    def test_every_ac_certificate_extends_under_the_stable_spec(self):
        """The published claim: moves + [16, 15] verifies for all 424."""
        for a in self.training["instances"]:
            challenge = {"challenge_id": a["training_id"],
                         "move_spec_version": stable_core.MOVE_SPEC_VERSION,
                         "initial_relators": a["initial_relators"],
                         "target_relators": []}
            v = stable_core.verify(challenge, a["moves"] + SUFFIX,
                                   stable_core.MOVE_SPEC_VERSION, self.limits)
            self.assertTrue(v["ok"], (a["training_id"], v))
            self.assertEqual(v["length"], a["length"] + 2)
            self.assertEqual(v["peak_total_relator_length"],
                             a["peak_total_relator_length"])
            self.assertEqual(v["work"], a["work"] + 1)

    def test_ac_moves_alone_do_not_reach_the_empty_presentation(self):
        for e in self.stable["instances"][:20]:
            v = stable_core.verify(util.training_challenge(e),
                                   e["moves"][:-len(SUFFIX)],
                                   e["move_spec_version"], self.limits)
            self.assertEqual(v["code"], "E_NOT_TARGET", e["training_id"])
            self.assertEqual(v["final_shape"], [1, 1], e["training_id"])

    def test_file_hash_headers(self):
        self.assertEqual(self.stable["format"], "acms-training-v1")
        self.assertEqual(self.stable["move_spec_version"], "sac-r8-v1")
        self.assertEqual(self.stable["move_spec_hash"],
                         canon.move_spec_hash(stable_core.MOVE_TABLE))
        self.assertNotEqual(self.stable["move_spec_hash"],
                            canon.move_spec_hash(core.MOVE_TABLE))

    def test_certificate_hashes_are_bound_to_the_stable_spec(self):
        for e in self.stable["instances"][:50]:
            self.assertEqual(
                e["certificate_hash"],
                canon.certificate_hash(e["training_id"], "sac-r8-v1",
                                       e["moves"]))

    def test_stable_training_is_disjoint_from_the_pool(self):
        pool = {util.canon_pair(c["initial_relators"])
                for c in util.load_manifest()["challenges"]}
        train = {util.canon_pair(e["initial_relators"])
                 for e in self.stable["instances"]}
        self.assertEqual(len(train), 424)
        self.assertEqual(train & pool, set())


if __name__ == "__main__":
    unittest.main()
