"""Frozen-data invariants: manifest schema (§3.1), challenge pool
composition (§2.1-§2.3), MS-1190 denominator consistency (§1.1, D-2),
and the O-4 no-signal rule for the public manifest.

Everything here is recomputed from the packaged verifier data and
public examples, without importing ``build/`` or reading private data.
"""

import collections
import csv
import hashlib
import re
import unittest

from acms_verify import canon, core, specs
from tests import util

POOL_SIZE = 10115
TRACKS = 2
CHALLENGE_COUNT = POOL_SIZE * TRACKS
CHALLENGE_KEYS = {"challenge_id", "generators", "initial_relators",
                  "target_relators", "move_spec_version", "scored",
                  "base_score", "instance_hash", "freeze_date"}
MAX_TOTAL_RELATOR_LENGTH = 40

#: Provenance/difficulty vocabulary that must never reach contestants.
#: Every token is checkable without any private data.
BANNED_TOKENS = ("family", "tier", "pool", "provenance", "w_vector",
                 "status_at_freeze", "MS-", "AUTH-", "INTL", "ACP-")

#: Per-track expectations, keyed by challenge-id prefix.
TRACK_EXPECTATIONS = {
    "ac-": {"move_spec_version": "ac-r2-v1", "target_relators": [[1], [2]]},
    "sac-": {"move_spec_version": "sac-r8-v1", "target_relators": []},
}

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
        self.assertEqual(len(self.challenges), CHALLENGE_COUNT)
        self.assertEqual(self.manifest["challenge_count"], CHALLENGE_COUNT)
        self.assertEqual(self.manifest["presentation_count"], POOL_SIZE)
        self.assertEqual(self.manifest["manifest_version"], "acms-v3")

    def test_challenge_keys_are_exactly_the_allowed_set(self):
        for c in self.challenges:
            self.assertEqual(set(c), CHALLENGE_KEYS, c["challenge_id"])

    def test_move_specs_header_matches_the_registry(self):
        entries = self.manifest["move_specs"]
        self.assertEqual([e["move_spec_version"] for e in entries],
                         list(specs.SPEC_ORDER))
        self.assertEqual(specs.check_move_specs(entries), [])
        for e in entries:
            self.assertEqual(set(e), {"move_spec_version", "move_spec_hash",
                                      "file", "target_relators", "max_rank",
                                      "id_prefix"})
        self.assertEqual([e["file"] for e in entries],
                         ["move_spec.json", "stable_move_spec.json"])
        self.assertEqual([e["max_rank"] for e in entries], [2, 8])
        self.assertEqual([e["id_prefix"] for e in entries],
                         ["ac-", "sac-"])
        # The singular pre-acms-v3 header fields are gone.
        for gone in ("move_spec_version", "move_spec_hash", "target_relators"):
            self.assertNotIn(gone, self.manifest, gone)

    def test_all_scored_base_score_one(self):
        for c in self.challenges:
            self.assertIs(c["scored"], True, c["challenge_id"])
            self.assertEqual(c["base_score"], 1, c["challenge_id"])
            self.assertEqual(c["generators"], ["x", "y"])
            self.assertEqual(c["freeze_date"], self.manifest["freeze_date"])

    def test_track_is_determined_by_the_id_prefix(self):
        for c in self.challenges:
            prefix = c["challenge_id"].rsplit("-", 1)[0] + "-"
            self.assertIn(prefix, TRACK_EXPECTATIONS, c["challenge_id"])
            for key, want in TRACK_EXPECTATIONS[prefix].items():
                self.assertEqual(c[key], want, c["challenge_id"])

    def test_ids_sequential_unique_and_in_file_order(self):
        ids = [c["challenge_id"] for c in self.challenges]
        self.assertEqual(len(set(ids)), len(ids))
        expected = (["ac-%05d" % i for i in range(1, POOL_SIZE + 1)]
                    + ["sac-%05d" % i for i in range(1, POOL_SIZE + 1)])
        # All ac records, then all sac records, each block in id order,
        # so nothing is inferable from position.
        self.assertEqual(ids, expected)
        self.assertEqual(ids[:POOL_SIZE], sorted(ids[:POOL_SIZE]))
        self.assertEqual(ids[POOL_SIZE:], sorted(ids[POOL_SIZE:]))

    def test_the_two_tracks_share_the_same_presentations(self):
        pairs = util.paired_challenges(self.manifest)
        self.assertEqual(len(pairs), POOL_SIZE)
        for ac, sac in pairs:
            cid = ac["challenge_id"]
            self.assertEqual("sac-" + cid[len("ac-"):],
                             sac["challenge_id"])
            self.assertEqual(ac["generators"], sac["generators"], cid)
            self.assertEqual(ac["initial_relators"], sac["initial_relators"],
                             cid)
            self.assertEqual(ac["base_score"], sac["base_score"], cid)
            self.assertEqual(ac["freeze_date"], sac["freeze_date"], cid)
            self.assertNotEqual(ac["instance_hash"], sac["instance_hash"], cid)

    def test_ac_problems_reproduce_the_historical_hashes_under_original_ids(self):
        """Renaming IDs changes hashes, but not the frozen presentations,
        targets, or move semantics.  Recreate the original ac-v1- IDs and
        compare with the unchanged snapshot from before Stable AC existed."""
        snapshot = util.load(util.AC_HASH_SNAPSHOT_PATH)
        spec_hash = canon.move_spec_hash(core.MOVE_TABLE)
        hashes = []
        for c in util.challenges_by_prefix(self.manifest, util.AC_PREFIX):
            original_id = "ac-v1-" + c["challenge_id"][len(util.AC_PREFIX):]
            original_hash = canon.instance_hash(
                original_id, c["generators"], c["initial_relators"],
                c["target_relators"], c["move_spec_version"], spec_hash)
            self.assertNotEqual(original_hash, c["instance_hash"], c["challenge_id"])
            hashes.append(original_hash)
        self.assertEqual(len(hashes), snapshot["count"])
        digest = hashlib.sha256(
            "\n".join(sorted(hashes)).encode("utf-8")).hexdigest()
        self.assertEqual(digest, snapshot["sha256_of_sorted_joined"])
        self.assertEqual(hashes[0], snapshot["first"])
        self.assertEqual(hashes[-1], snapshot["last"])
        self.assertEqual(canon.manifest_hash(hashes),
                         snapshot["manifest_hash_before_stable_track"])

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

    def test_no_duplicate_presentations_within_a_track(self):
        for prefix in TRACK_EXPECTATIONS:
            keys = collections.Counter(
                util.canon_pair(c["initial_relators"])
                for c in self.challenges
                if c["challenge_id"].startswith(prefix))
            dupes = [k for k, n in keys.items() if n > 1]
            self.assertEqual(dupes, [], prefix)
            self.assertEqual(len(keys), POOL_SIZE, prefix)


class TestMS1190Invariants(unittest.TestCase):
    """The MS-1190 open set is fully scored, the certified 424 are not."""

    @classmethod
    def setUpClass(cls):
        cls.pool_keys = {util.canon_pair(c["initial_relators"])
                         for c in util.load_manifest()["challenges"]}
        # Both tracks hold the same presentations, so the set of keys is
        # the pool itself, once.
        cls.ms = ms1190_keys()

    def test_all_550_open_instances_are_scored(self):
        self.assertEqual(len(self.ms["open"]), 550)
        self.assertEqual(self.ms["open"] - self.pool_keys, set())

    def test_all_424_certified_instances_are_excluded(self):
        self.assertEqual(len(self.ms["certified"]), 424)
        self.assertEqual(self.ms["certified"] & self.pool_keys, set())

    def test_training_424_is_disjoint_from_the_pool(self):
        for training in (util.load_training(), util.load_stable_training()):
            train = {util.canon_pair(e["initial_relators"])
                     for e in training["instances"]}
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
        self.assertIsNone(re.search(r"[A-Z]", self.text.replace(freeze, "") if freeze is not None else self.text))


if __name__ == "__main__":
    unittest.main()
