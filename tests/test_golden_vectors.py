"""Acceptance row 5 (seed): every golden conformance vector passes on
this machine, and the golden file's hash headers match the frozen
artifacts."""

import unittest

from acms_verify import canon, core, golden
from tests import util


class TestGoldenVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = util.load(util.GOLDEN_PATH)

    def test_headers_match_frozen_artifacts(self):
        manifest = util.load_manifest()
        self.assertEqual(self.doc["move_spec_hash"],
                         canon.move_spec_hash(core.MOVE_TABLE))
        self.assertEqual(self.doc["manifest_hash"], manifest["manifest_hash"])
        self.assertEqual(self.doc["default_limits"], manifest["limits"])

    def test_all_vectors_pass(self):
        report = golden.run_vectors(self.doc)
        failures = [r for r in report if not r["passed"]]
        self.assertEqual(failures, [], failures)
        # Every error code of the §4.2 contract is exercised.
        names = " ".join(v["name"] for v in
                         self.doc["verify_vectors"]
                         + self.doc["submission_vectors"])
        for token in ("spec-mismatch", "bad-move-id", "path-too-long",
                      "length-limit", "work-budget", "not-target",
                      "malformed", "duplicate", "client-asserted",
                      "unknown-challenge"):
            self.assertIn(token, names)


if __name__ == "__main__":
    unittest.main()
