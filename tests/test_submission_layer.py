"""Acceptance row 4 + §4.1/§4.2 whole-vs-per-item rejection semantics
and the O-5 check priority."""

import json
import unittest

from acms_verify import core, submission
from tests import util


class TestSubmissionLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.index = submission.build_challenge_index(cls.manifest)
        entry = min(util.load_training()["instances"],
                    key=lambda e: e["length"])
        # A mini manifest that also knows the solvable training instance.
        cls.mini = {"limits": cls.manifest["limits"],
                    "challenges": cls.manifest["challenges"][:3]
                    + [util.training_challenge(entry)]}
        cls.entry = entry
        cls.sol = {"challenge_id": entry["training_id"],
                   "moves": entry["moves"]}

    def run_sub(self, doc, manifest=None):
        raw = doc if isinstance(doc, bytes) else json.dumps(doc).encode()
        return submission.process_submission(raw, manifest or self.mini)

    # -- happy path ------------------------------------------------------
    def test_accept_without_client_version_uses_official_hash(self):
        v = self.run_sub({"method": "bfs", "notes": "hi",
                          "solutions": [self.sol]})
        self.assertTrue(v["accepted"])
        self.assertTrue(v["results"][0]["ok"])
        self.assertEqual(v["results"][0]["certificate_hash"],
                         self.entry["certificate_hash"])
        official = core.verify(util.training_challenge(self.entry),
                               self.sol["moves"],
                               self.entry["move_spec_version"],
                               self.mini["limits"])
        self.assertEqual(v["results"][0],
                         dict(official, challenge_id=self.sol["challenge_id"]))

    def test_per_item_errors_do_not_reject_submission(self):
        good, bad = self.sol, {"challenge_id": "ms-v1-9999", "moves": []}
        bad_move = {"challenge_id": self.mini["challenges"][0]["challenge_id"],
                    "moves": [14]}
        wrong_target = {"challenge_id": self.mini["challenges"][1]["challenge_id"],
                        "moves": []}
        v = self.run_sub({"solutions": [bad, bad_move, wrong_target, good]})
        self.assertTrue(v["accepted"])
        self.assertEqual(v["results"][0]["code"], "E_UNKNOWN_CHALLENGE")
        self.assertEqual(v["results"][1]["code"], "E_BAD_MOVE_ID")
        self.assertEqual(v["results"][1]["move_index"], 0)
        self.assertEqual(v["results"][2]["code"], "E_NOT_TARGET")
        self.assertTrue(v["results"][3]["ok"])

    # -- acceptance row 4: corrupted certificates -----------------------
    def test_malformed_json(self):
        v = self.run_sub(b'{"solutions": [ {"challenge')
        self.assertEqual((v["accepted"], v["code"], v["detail"]),
                         (False, "E_MALFORMED", "bad_json"))
        self.assertFalse(v["counts_against_quota"])

    def test_missing_moves(self):
        v = self.run_sub({"solutions": [{"challenge_id": "x"}]})
        self.assertEqual((v["code"], v["detail"], v["key"]),
                         ("E_MALFORMED", "solution_missing_key", "moves"))

    def test_moves_not_array(self):
        v = self.run_sub({"solutions": [dict(self.sol, moves="012")]})
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "moves_not_array"))

    # -- structural whole-submission rejections -------------------------
    def test_duplicate_challenge(self):
        v = self.run_sub({"solutions": [self.sol, dict(self.sol, moves=[])]})
        self.assertEqual(v["code"], "E_DUPLICATE_CHALLENGE")
        self.assertEqual(v["challenge_id"], self.sol["challenge_id"])

    def test_client_asserted_result_top_level(self):
        v = self.run_sub({"solutions": [self.sol], "score": 10})
        self.assertEqual(v["code"], "E_CLIENT_ASSERTED_RESULT")
        self.assertEqual(v["key_path"], "score")

    def test_client_asserted_result_nested(self):
        v = self.run_sub({"solutions": [dict(self.sol, length=7)]})
        self.assertEqual(v["code"], "E_CLIENT_ASSERTED_RESULT")
        self.assertEqual(v["key_path"], "solutions[0].length")

    def test_client_asserted_beats_unknown_key(self):
        """Forbidden-key scan runs before shape checks (probing fields
        get the dedicated code even though they are also unknown keys)."""
        v = self.run_sub({"solutions": [self.sol], "final_state": [[1], [2]]})
        self.assertEqual(v["code"], "E_CLIENT_ASSERTED_RESULT")

    def test_unknown_keys_rejected(self):
        v = self.run_sub({"solutions": [self.sol], "team": "foo"})
        self.assertEqual((v["code"], v["detail"], v["key"]),
                         ("E_MALFORMED", "unknown_key", "team"))
        v = self.run_sub({"solutions": [dict(self.sol, hint=1)]})
        self.assertEqual((v["code"], v["detail"], v["key"]),
                         ("E_MALFORMED", "unknown_key", "hint"))

    def test_client_version_rejects_whole_submission_as_unknown_key(self):
        for version in (self.entry["move_spec_version"], "ac-r1-v0"):
            with self.subTest(version=version):
                v = self.run_sub({"solutions": [
                    dict(self.sol, move_spec_version=version)]})
                self.assertFalse(v["accepted"])
                self.assertFalse(v["counts_against_quota"])
                self.assertEqual((v["code"], v["detail"], v["key"]),
                                 ("E_MALFORMED", "unknown_key",
                                  "move_spec_version"))

    def test_solution_count_limit(self):
        sols = [{"challenge_id": "c%d" % i, "moves": []} for i in range(501)]
        v = self.run_sub({"solutions": sols})
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "too_many_solutions"))

    def test_body_limit_beats_everything(self):
        raw = (b'{"notes": "' + b"a" * submission.MAX_BODY_BYTES + b'"}')
        v = submission.process_submission(raw, self.mini)
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "body_too_large"))

    def test_notes_too_long(self):
        v = self.run_sub({"notes": "a" * 2001, "solutions": [self.sol]})
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "notes_too_long"))

    def test_empty_solutions_rejected(self):
        for doc in ({"solutions": []}, {"solutions": "x"}, {}, [], 5):
            v = self.run_sub(doc)
            self.assertEqual(v["code"], "E_MALFORMED", doc)

    def test_deeply_nested_json_is_malformed_not_crash(self):
        """Pathological nesting must yield a verdict, not a
        RecursionError (whole-submission E_MALFORMED)."""
        raw = b"[" * 3000 + b"]" * 3000
        v = submission.process_submission(raw, self.mini)
        # Which detail fires depends on how deep the host CPython's json
        # parser gets before its recursion guard trips (<=3.12 raises and
        # we report bad_json; 3.13+ parses the nest and we reject the
        # non-object root).  Either way it is a verdict, not a crash.
        self.assertEqual(v["code"], "E_MALFORMED")
        self.assertIn(v["detail"], ("bad_json", "root_not_object"))
        deep = (b'{"solutions": ' + b"[" * 900 + b"]" * 900 + b"}")
        v = submission.process_submission(deep, self.mini)
        self.assertEqual(v["code"], "E_MALFORMED")

    def test_structural_limits_configurable(self):
        sols = [{"challenge_id": "c%d" % i, "moves": []} for i in range(3)]
        v = self.run_sub({"solutions": sols})
        self.assertTrue(v["accepted"])
        raw = json.dumps({"solutions": sols}).encode()
        v = submission.process_submission(raw, self.mini,
                                          structural_limits={"max_solutions": 2})
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "too_many_solutions"))

    def test_real_manifest_challenge_wrong_path(self):
        """Against the scored manifest any path that merely
        walks legally but ends elsewhere yields E_NOT_TARGET."""
        cid = self.manifest["challenges"][0]["challenge_id"]
        v = self.run_sub({"solutions": [{"challenge_id": cid,
                                         "moves": [6, 7]}]},
                         manifest=self.manifest)
        self.assertTrue(v["accepted"])
        self.assertEqual(v["results"][0]["code"], "E_NOT_TARGET")


if __name__ == "__main__":
    unittest.main()
