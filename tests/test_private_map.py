"""Organizer-side invariants of build/private/challenge_map_private.tsv.

The map is the only link between a public ``ac-v1-NNNNN`` id and the
private SAIR master id, and it must never be published.  It is keyed by
the presentation, so it has one row per presentation, not one per
challenge: ``sac-v1-N`` is the same presentation as ``ac-v1-N`` and is
covered by the same row.  It exists only
after ``build/sync_dataset.py`` + ``build/build_manifest_v2.py`` have
run against the private release, so the whole module is skipped when it
is absent (e.g. in the exported public package).
"""

import collections
import csv
import unittest

from tests import util

POOL_SIZE = 10115
TIER_COUNTS = {"T0_warmup": 163, "T1_easy": 4366, "T2_medium": 1769,
               "T3_hard_solvable": 1113, "T4_frontier": 1695,
               "T5_moonshot": 1009}
ADDED_OPEN_NOT_IN_DRAW = 204
UNCERTIFIED_IN_POOL = 183


def load_rows():
    with open(util.PRIVATE_MAP_PATH, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


@unittest.skipUnless(util.PRIVATE_MAP_PATH.exists(),
                     "private challenge map absent (run build/sync_dataset.py "
                     "and build/build_manifest_v2.py)")
class TestPrivateChallengeMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()
        cls.manifest = util.load_manifest()
        cls.ac_ids = [c["challenge_id"] for c in
                      util.challenges_by_prefix(cls.manifest, util.AC_PREFIX)]
        cls.stable_ids = [c["challenge_id"] for c in
                          util.challenges_by_prefix(cls.manifest,
                                                    util.STABLE_PREFIX)]

    def test_row_count(self):
        self.assertEqual(len(self.rows), POOL_SIZE)

    def test_challenge_id_master_id_bijection(self):
        cids = [r["challenge_id"] for r in self.rows]
        mids = [r["master_id"] for r in self.rows]
        self.assertEqual(len(set(cids)), POOL_SIZE)
        self.assertEqual(len(set(mids)), POOL_SIZE)
        self.assertEqual(len({r["public_id"] for r in self.rows}), POOL_SIZE)

    def test_covers_every_manifest_presentation(self):
        self.assertEqual({r["challenge_id"] for r in self.rows},
                         set(self.ac_ids))
        self.assertEqual(len(self.ac_ids), POOL_SIZE)
        self.assertEqual(len(self.stable_ids), POOL_SIZE)
        # One row per presentation, and it reaches the stable track by
        # the shared id number.
        self.assertEqual(len(self.rows), POOL_SIZE)
        self.assertEqual(
            {util.STABLE_PREFIX + r["challenge_id"][len(util.AC_PREFIX):]
             for r in self.rows},
            set(self.stable_ids))

    def test_carries_no_stable_track_id(self):
        """The map is deliberately keyed by the ac-v1 id alone; nothing
        in it names the stable track."""
        text = util.PRIVATE_MAP_PATH.read_text(encoding="utf-8")
        self.assertNotIn(util.STABLE_PREFIX, text)
        self.assertNotIn("sac-r8-v1", text)

    def test_tier_composition_pinned(self):
        self.assertEqual(
            dict(collections.Counter(r["tier"] for r in self.rows)),
            TIER_COUNTS)

    def test_no_certified_ms1190_instance_is_scored(self):
        statuses = collections.Counter(r["ms1190_status"] for r in self.rows)
        self.assertEqual(statuses["certified"], 0)
        self.assertEqual(statuses["open"], 550)
        self.assertEqual(statuses["uncertified"], UNCERTIFIED_IN_POOL)

    def test_added_open_instances_outside_the_draw(self):
        outside = [r for r in self.rows if r["in_draw"] == "false"]
        self.assertEqual(len(outside), ADDED_OPEN_NOT_IN_DRAW)
        for r in outside:
            self.assertEqual(r["ms1190_status"], "open", r["challenge_id"])


if __name__ == "__main__":
    unittest.main()
