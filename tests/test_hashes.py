"""Acceptance row 11 + §3.2 byte templates.

Any change to the manifest or the move spec must change at least one
hash, and submissions carrying a stale move_spec_version must be
rejected with E_SPEC_MISMATCH.
"""

import unittest

from acms_verify import canon, core
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

    def test_manifest_hashes_recompute(self):
        hashes = []
        for c in self.manifest["challenges"]:
            h = canon.instance_hash(
                c["challenge_id"], c["generators"], c["initial_relators"],
                c["target_relators"], c["move_spec_version"], self.spec_hash)
            self.assertEqual(h, c["instance_hash"], c["challenge_id"])
            hashes.append(h)
        self.assertEqual(canon.manifest_hash(hashes),
                         self.manifest["manifest_hash"])
        self.assertEqual(self.manifest["move_spec_hash"], self.spec_hash)

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


if __name__ == "__main__":
    unittest.main()
