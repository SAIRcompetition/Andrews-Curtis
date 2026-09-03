"""Frozen-data invariants: manifest schema (§3.1), challenge pool
composition (§2.1-§2.3), MS-1190 denominator consistency (§1.1, D-2),
and the O-4 no-signal rule for the public manifest.

Everything here is recomputed from the published artifacts alone — no
``build/`` import, no private data — so the suite also runs inside the
exported public package.
"""

import collections
import csv
import re
import unittest

from acms_verify import core
from tests import util

POOL_SIZE = 10115
CHALLENGE_KEYS = {"challenge_id", "generators", "initial_relators",
                  "target_relators", "move_spec_version", "scored",
                  "base_score", "instance_hash", "freeze_date"}
MAX_TOTAL_RELATOR_LENGTH = 40

#: Provenance/difficulty vocabulary that must never reach contestants.
#: Every token is checkable without any private data.
BANNED_TOKENS = ("family", "tier", "pool", "provenance", "w_vector",
                 "status_at_freeze", "MS-", "AUTH-", "INTL")

MS1190_STATUS_COUNTS = {"certified": 424, "uncertified": 216, "open": 550}
MS1190_UNCERTIFIED_IN_POOL = 183


def ms1190_rows():
    with open(util.MS1190_PATH, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ms1190_keys():
    """``status -> set of canonical relator pairs`` for all 1190 rows."""
    keys = collections.defaultdict(set)
    for r in ms1190_rows():
        wv = [int(a) for a in r["w_vector"].split()]
        keys[r["status_at_freeze"]].add(
            util.canon_pair(util.ms_initial(int(r["n"]), wv)))
    return keys


class TestManifestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.challenges = cls.manifest["challenges"]

    def test_pool_size(self):
        self.assertEqual(len(self.challenges), POOL_SIZE)
        self.assertEqual(self.manifest["challenge_count"], POOL_SIZE)
        self.assertEqual(self.manifest["manifest_version"], "acms-v2")

    def test_challenge_keys_are_exactly_the_allowed_set(self):
        for c in self.challenges:
            self.assertEqual(set(c), CHALLENGE_KEYS, c["challenge_id"])

    def test_all_scored_base_score_one(self):
        for c in self.challenges:
            self.assertIs(c["scored"], True, c["challenge_id"])
            self.assertEqual(c["base_score"], 1, c["challenge_id"])
            self.assertEqual(c["move_spec_version"], "ac-r2-v1")
            self.assertEqual(c["target_relators"], [[1], [2]])
            self.assertEqual(c["generators"], ["x", "y"])
            self.assertEqual(c["freeze_date"], self.manifest["freeze_date"])

    def test_ids_sequential_unique_and_in_file_order(self):
        ids = [c["challenge_id"] for c in self.challenges]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids, ["ac-v1-%05d" % i
                               for i in range(1, POOL_SIZE + 1)])
        # File order is id order, so nothing is inferable from position.
        self.assertEqual(ids, sorted(ids))

    def test_limits_frozen_values(self):
        self.assertEqual(self.manifest["limits"],
                         {"max_path_length": 100000,
                          "max_total_relator_length": 10000,
                          "max_work": 5000000})


class TestChallengePresentations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.challenges = util.load_manifest()["challenges"]

    def test_relators_reduced_alphabet_and_length(self):
        for c in self.challenges:
            cid = c["challenge_id"]
            self.assertEqual(len(c["initial_relators"]), 2, cid)
            total = 0
            for w in c["initial_relators"]:
                self.assertEqual(list(core.free_reduce(w)), w, cid)
                self.assertTrue(w, cid)
                for a in w:
                    self.assertIn(a, (-2, -1, 1, 2), cid)
                total += len(w)
            self.assertLessEqual(total, MAX_TOTAL_RELATOR_LENGTH, cid)

    def test_no_duplicate_presentations(self):
        keys = collections.Counter(
            util.canon_pair(c["initial_relators"]) for c in self.challenges)
        dupes = [k for k, n in keys.items() if n > 1]
        self.assertEqual(dupes, [])
        self.assertEqual(len(keys), POOL_SIZE)


class TestMS1190Invariants(unittest.TestCase):
    """The MS-1190 open set is fully scored, the certified 424 are not."""

    @classmethod
    def setUpClass(cls):
        cls.pool_keys = {util.canon_pair(c["initial_relators"])
                         for c in util.load_manifest()["challenges"]}
        cls.ms = ms1190_keys()

    def test_all_550_open_instances_are_scored(self):
        self.assertEqual(len(self.ms["open"]), 550)
        self.assertEqual(self.ms["open"] - self.pool_keys, set())

    def test_all_424_certified_instances_are_excluded(self):
        self.assertEqual(len(self.ms["certified"]), 424)
        self.assertEqual(self.ms["certified"] & self.pool_keys, set())

    def test_training_424_is_disjoint_from_the_pool(self):
        train = {util.canon_pair(e["initial_relators"])
                 for e in util.load_training()["instances"]}
        self.assertEqual(len(train), 424)
        self.assertEqual(train & self.pool_keys, set())

    def test_uncertified_overlap_is_pinned(self):
        self.assertEqual(len(self.ms["uncertified"] & self.pool_keys),
                         MS1190_UNCERTIFIED_IN_POOL)


class TestMS1190Metadata(unittest.TestCase):
    def setUp(self):
        self.rows = ms1190_rows()

    def test_denominator_counts(self):
        self.assertEqual(len(self.rows), 1190)
        self.assertEqual(
            collections.Counter(r["status_at_freeze"] for r in self.rows),
            MS1190_STATUS_COUNTS)

    def test_columns_carry_no_pool_membership(self):
        expected = ["seq", "n", "w", "w_vector", "status_at_freeze",
                    "reported_class", "training_id", "prototype_path_length"]
        self.assertEqual(list(self.rows[0].keys()), expected)
        self.assertNotIn("challenge_id", self.rows[0])
        self.assertNotIn("scored", self.rows[0])

    def test_training_id_exactly_on_certified_rows(self):
        for r in self.rows:
            self.assertEqual(bool(r["training_id"]),
                             r["status_at_freeze"] == "certified", r["seq"])

    def test_ms_formula_balanced(self):
        for r in self.rows:
            wv = [int(a) for a in r["w_vector"].split()]
            self.assertEqual(
                sum(1 if a == 1 else -1 for a in wv if abs(a) == 1), 0,
                r["seq"])
            r0, r1 = util.ms_initial(int(r["n"]), wv)
            self.assertEqual(list(core.free_reduce(r0)), r0, r["seq"])
            self.assertEqual(list(core.free_reduce(r1)), r1, r["seq"])


class TestManifestLeakage(unittest.TestCase):
    """O-4: the raw manifest text discloses no provenance vocabulary."""

    @classmethod
    def setUpClass(cls):
        with open(util.MANIFEST_PATH, encoding="utf-8") as fh:
            cls.text = fh.read()

    def test_no_banned_tokens(self):
        for token in BANNED_TOKENS:
            self.assertNotIn(token, self.text, token)

    def test_lowercase_ascii_apart_from_the_freeze_date(self):
        freeze = util.load_manifest()["freeze_date"]
        self.assertIsNone(re.search(r"[A-Z]", self.text.replace(freeze, "")))


if __name__ == "__main__":
    unittest.main()
