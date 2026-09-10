"""Acceptance row 11 + §3.2 byte templates.

Any change to the manifest or to either move spec must change at least
one hash, and a mismatched internal move_spec_version must be
rejected with E_SPEC_MISMATCH.

The byte templates in canon.py are frozen: instance_canon already
covers target_relators, move_spec_version and move_spec_hash, which is
exactly why the stable problem could be added without changing the
original AC hashes.  Renaming a challenge ID deliberately changes its
instance hash; test_manifest_data reconstructs the original IDs to
preserve the historical mathematical regression check.
"""

import unittest

from verifier import canon, core, specs, stable_core
from tests import util


class TestByteTemplates(unittest.TestCase):
    """Freeze the §3.2 canonical serialization byte for byte."""

    def test_instance_canon_template(self):
        got = canon.instance_canon(
            "ms-v1-0001", ["x", "y"],
            [[-1, 2, 2, 2, 1, -2, -2, -2, -2], [1, 2, -1, 2, 1]],
            [[1], [2]], "ac-r2-v1", "sha256:0000")
        self.assertEqual(
            got,
            '{"challenge_id":"ms-v1-0001","generators":["x","y"],'
            '"initial_relators":[[-1,2,2,2,1,-2,-2,-2,-2],[1,2,-1,2,1]],'
            '"target_relators":[[1],[2]],'
            '"move_spec_version":"ac-r2-v1","move_spec_hash":"sha256:0000"}')

    def test_instance_canon_template_stable_target(self):
        """The empty target serializes as [] — the same template, no
        special case."""
        got = canon.instance_canon(
            "sac-00001", ["x", "y"], [[1, 2], [2, 1]], [],
            "sac-r8-v1", "sha256:0000")
        self.assertEqual(
            got,
            '{"challenge_id":"sac-00001","generators":["x","y"],'
            '"initial_relators":[[1,2],[2,1]],'
            '"target_relators":[],'
            '"move_spec_version":"sac-r8-v1","move_spec_hash":"sha256:0000"}')

    def test_certificate_canon_template(self):
        got = canon.certificate_canon("ms-v1-0001", "ac-r2-v1", [0, 4, 8, 3])
        self.assertEqual(
            got,
            '{"challenge_id":"ms-v1-0001","move_spec_version":"ac-r2-v1",'
            '"moves":[0,4,8,3]}')

    def test_no_float_or_bool_integers(self):
        for bad in (1.0, True, "1"):
            with self.assertRaises(ValueError):
                canon.canon_int_list([bad])

    def test_hash_shape(self):
        h = canon.sha256_str("x")
        self.assertRegex(h, r"^sha256:[0-9a-f]{64}$")


class TestHashSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.spec_hash = canon.move_spec_hash(core.MOVE_TABLE)
        cls.stable_spec_hash = canon.move_spec_hash(stable_core.MOVE_TABLE)
        cls.spec_hashes = specs.move_spec_hashes()

    def test_registry_hashes_match_the_move_tables(self):
        self.assertEqual(self.spec_hashes,
                         {"ac-r2-v1": self.spec_hash,
                          "sac-r8-v1": self.stable_spec_hash})
        self.assertNotEqual(self.spec_hash, self.stable_spec_hash)
        for entry in self.manifest["move_specs"]:
            self.assertEqual(entry["move_spec_hash"],
                             self.spec_hashes[entry["move_spec_version"]])

    def test_manifest_hashes_recompute(self):
        """All 20230, each under the spec its own record names."""
        hashes = []
        for c in self.manifest["challenges"]:
            h = canon.instance_hash(
                c["challenge_id"], c["generators"], c["initial_relators"],
                c["target_relators"], c["move_spec_version"],
                self.spec_hashes[c["move_spec_version"]])
            self.assertEqual(h, c["instance_hash"], c["challenge_id"])
            hashes.append(h)
        self.assertEqual(len(hashes), 20230)
        self.assertEqual(len(set(hashes)), 20230)
        self.assertEqual(canon.manifest_hash(hashes),
                         self.manifest["manifest_hash"])

    def test_the_wrong_spec_hash_would_be_caught(self):
        """Using one spec hash for every challenge — the bug the
        per-challenge lookup replaces — must not verify."""
        sac = util.challenges_by_prefix(self.manifest, util.STABLE_PREFIX)[0]
        wrong = canon.instance_hash(
            sac["challenge_id"], sac["generators"], sac["initial_relators"],
            sac["target_relators"], sac["move_spec_version"], self.spec_hash)
        self.assertNotEqual(wrong, sac["instance_hash"])

    def test_same_presentation_different_track_different_hash(self):
        ac, sac = util.paired_challenges(self.manifest)[0]
        self.assertEqual(ac["initial_relators"], sac["initial_relators"])
        self.assertNotEqual(ac["instance_hash"], sac["instance_hash"])

    def test_stable_move_table_change_changes_its_spec_hash(self):
        rows = [dict(r) for r in stable_core.MOVE_TABLE]
        rows[161]["conjugator"] = -rows[161]["conjugator"]
        self.assertNotEqual(canon.move_spec_hash(rows), self.stable_spec_hash)
        self.assertNotEqual(canon.move_spec_hash(rows[:-1]),
                            self.stable_spec_hash)

    def test_relator_change_changes_instance_hash(self):
        c = self.manifest["challenges"][0]
        mutated = [list(w) for w in c["initial_relators"]]
        mutated[0][0] = -mutated[0][0]
        h = canon.instance_hash(
            c["challenge_id"], c["generators"], mutated,
            c["target_relators"], c["move_spec_version"], self.spec_hash)
        self.assertNotEqual(h, c["instance_hash"])

    def test_move_table_change_changes_spec_hash(self):
        rows = [dict(r) for r in core.MOVE_TABLE]
        rows[2]["inverse"] = 2
        self.assertNotEqual(canon.move_spec_hash(rows), self.spec_hash)
        rows = [dict(r) for r in core.MOVE_TABLE][:13]
        self.assertNotEqual(canon.move_spec_hash(rows), self.spec_hash)

    def test_instance_hash_change_changes_manifest_hash(self):
        hashes = [c["instance_hash"] for c in self.manifest["challenges"]]
        mutated = list(hashes)
        mutated[0] = canon.sha256_str("mutant")
        self.assertNotEqual(canon.manifest_hash(mutated),
                            canon.manifest_hash(hashes))

    def test_manifest_hash_order_independent(self):
        hashes = [c["instance_hash"] for c in self.manifest["challenges"]]
        self.assertEqual(canon.manifest_hash(list(reversed(hashes))),
                         canon.manifest_hash(hashes))

    def test_stale_spec_version_rejected(self):
        c = self.manifest["challenges"][0]
        v = core.verify(c, [], "ac-r1-v0", self.manifest["limits"])
        self.assertEqual(v["code"], "E_SPEC_MISMATCH")

    def test_cross_track_spec_version_rejected_both_ways(self):
        ac, sac = util.paired_challenges(self.manifest)[0]
        limits = self.manifest["limits"]
        v = specs.verify_challenge(ac, [], "sac-r8-v1", limits)
        self.assertEqual((v["code"], v["expected"], v["got"]),
                         ("E_SPEC_MISMATCH", "ac-r2-v1", "sac-r8-v1"))
        v = specs.verify_challenge(sac, [], "ac-r2-v1", limits)
        self.assertEqual((v["code"], v["expected"], v["got"]),
                         ("E_SPEC_MISMATCH", "sac-r8-v1", "ac-r2-v1"))

    def test_unknown_challenge_spec_is_a_developer_error(self):
        c = dict(self.manifest["challenges"][0], move_spec_version="ac-r9-v9")
        with self.assertRaises(ValueError):
            specs.verify_challenge(c, [], "ac-r9-v9", self.manifest["limits"])


if __name__ == "__main__":
    unittest.main()
