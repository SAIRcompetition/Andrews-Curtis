"""Acceptance row 5 (seed): every golden conformance vector passes on
this machine, and the golden file's hash headers match the frozen
artifacts."""

import unittest

from acms_verify import golden, specs
from tests import util


class TestGoldenVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = util.load(util.GOLDEN_PATH)
        cls.names = " ".join(v["name"] for v in
                             cls.doc["verify_vectors"]
                             + cls.doc["submission_vectors"])

    def test_headers_match_frozen_artifacts(self):
        manifest = util.load_manifest()
        self.assertEqual(self.doc["format"], "acms-golden-v2")
        self.assertEqual(golden.FORMAT, "acms-golden-v2")
        self.assertEqual(self.doc["move_specs"], manifest["move_specs"])
        self.assertEqual(specs.check_move_specs(self.doc["move_specs"]), [])
        self.assertEqual(self.doc["manifest_hash"], manifest["manifest_hash"])
        self.assertEqual(self.doc["default_limits"], manifest["limits"])
        for gone in ("move_spec_version", "move_spec_hash"):
            self.assertNotIn(gone, self.doc, gone)

    def test_wrong_format_or_headers_are_refused(self):
        with self.assertRaises(ValueError):
            golden.run_vectors(dict(self.doc, format="acms-golden-v1"))
        broken = [dict(e) for e in self.doc["move_specs"]]
        broken[1]["move_spec_hash"] = "sha256:0000"
        with self.assertRaises(ValueError):
            golden.run_vectors(dict(self.doc, move_specs=broken))

    def test_all_vectors_pass(self):
        report = golden.run_vectors(self.doc)
        failures = [r for r in report if not r["passed"]]
        self.assertEqual(failures, [], failures)
        self.assertGreaterEqual(len(report), 47)

    def test_every_ac_error_code_is_exercised(self):
        # Every error code of the §4.2 contract.
        for token in ("spec-mismatch", "bad-move-id", "path-too-long",
                      "length-limit", "work-budget", "not-target",
                      "malformed", "duplicate",
                      "unknown-challenge"):
            self.assertIn(token, self.names)

    def test_stable_track_is_covered(self):
        for token in ("accept-stable-shortest", "accept-stable-median",
                      "accept-stable-longest", "accept-stable-canon-xy",
                      "accept-stable-canon-yx", "accept-stable-rank3-detour",
                      "not-target-stable", "bad-move-id-stable-257",
                      "spec-mismatch-ac-version-on-stable-challenge",
                      "spec-mismatch-stable-version-on-ac-challenge",
                      "sub-accept-mixed-tracks",
                      "sub-stable-comment-does-not-select-ac-spec"):
            self.assertIn(token, self.names, token)

    def test_txt_submission_contract_is_covered(self):
        for token in ("sub-accept-comments-and-blank-lines", "sub-accept-crlf-whitespace",
                      "sub-accept-utf8-bom", "sub-accept-long-unicode-comment",
                      "sub-malformed-missing-colon", "sub-malformed-missing-id",
                      "sub-malformed-missing-moves", "sub-malformed-trailing-comma",
                      "sub-malformed-trailing-text", "sub-malformed-multiline-moves",
                      "sub-malformed-comments-only", "sub-negative-move-id",
                      "sub-noninteger-move-id", "sub-bad-move-id-bool",
                      "sub-bad-move-id-string", "sub-bad-move-id-null",
                      "sub-too-many-solutions"):
            self.assertIn(token, self.names, token)
        for vector in self.doc["submission_vectors"]:
            self.assertNotEqual(vector["expected"].get("code"), "E_CLIENT_ASSERTED_RESULT")

    def test_builder_reproduces_vectors_from_committed_public_data(self):
        from build.build_manifest_v2 import build_golden_v3

        regenerated = build_golden_v3(util.load_manifest(), util.load_training(),
                                       util.load_stable_training())
        self.assertEqual(regenerated, self.doc)

    def test_every_not_applicable_reason_is_exercised(self):
        reasons = {v["expected"].get("reason")
                   for v in self.doc["verify_vectors"]
                   if v["expected"].get("code") == "E_MOVE_NOT_APPLICABLE"}
        self.assertEqual(reasons, {"relator_out_of_rank",
                                   "generator_out_of_rank",
                                   "max_rank_exceeded",
                                   "destabilize_precondition"})

    def test_both_tracks_appear_in_the_embedded_challenges(self):
        versions = {c["move_spec_version"]
                    for c in self.doc["challenges"].values()}
        self.assertEqual(versions, {"ac-r2-v1", "sac-r8-v1"})
        for cid, c in self.doc["challenges"].items():
            self.assertEqual(cid, c["challenge_id"])
            if c["move_spec_version"] == "sac-r8-v1":
                self.assertEqual(c["target_relators"], [])
            else:
                self.assertEqual(c["target_relators"], [[1], [2]])


if __name__ == "__main__":
    unittest.main()
