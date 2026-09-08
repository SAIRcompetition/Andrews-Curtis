"""Acceptance row 4 + §4.1/§4.2 whole-vs-per-item rejection semantics
and the O-5 check priority."""

import json
import unittest

from acms_verify import submission
from tests import util


class TestSubmissionLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.index = submission.build_challenge_index(cls.manifest)
        entry = min(util.load_training()["instances"],
                    key=lambda e: e["length"])
        stable = {e["training_id"]: e
                  for e in util.load_stable_training()["instances"]}
        # The stable counterpart carries the same training_id, so give it
        # a distinct one inside the mini manifest.
        stable_entry = dict(stable[entry["training_id"]],
                            training_id="sac-" + entry["training_id"])
        # A mini manifest that also knows the solvable training instance
        # in both tracks.
        cls.mini = {"limits": cls.manifest["limits"],
                    "challenges": cls.manifest["challenges"][:3]
                    + [util.training_challenge(entry),
                       util.training_challenge(stable_entry)]}
        cls.entry = entry
        cls.stable_entry = stable_entry
        cls.sol = {"challenge_id": entry["training_id"],
                   "move_spec_version": entry["move_spec_version"],
                   "moves": entry["moves"]}
        cls.stable_sol = {"challenge_id": stable_entry["training_id"],
                          "move_spec_version":
                              stable_entry["move_spec_version"],
                          "moves": stable_entry["moves"]}

    def run_sub(self, doc, manifest=None):
        raw = doc if isinstance(doc, bytes) else json.dumps(doc).encode()
        return submission.process_submission(raw, manifest or self.mini)

    # -- happy path ------------------------------------------------------
    def test_accept(self):
        v = self.run_sub({"method": "bfs", "notes": "hi",
                          "solutions": [self.sol]})
        self.assertTrue(v["accepted"])
        self.assertTrue(v["results"][0]["ok"])
        self.assertEqual(v["results"][0]["certificate_hash"],
                         self.entry["certificate_hash"])

    def test_per_item_errors_do_not_reject_submission(self):
        good, bad = self.sol, {"challenge_id": "ms-v1-9999",
                               "move_spec_version": "ac-r2-v1", "moves": []}
        v = self.run_sub({"solutions": [bad, good]})
        self.assertTrue(v["accepted"])
        self.assertEqual(v["results"][0]["code"], "E_UNKNOWN_CHALLENGE")
        self.assertTrue(v["results"][1]["ok"])

    # -- acceptance row 4: corrupted certificates -----------------------
    def test_malformed_json(self):
        v = self.run_sub(b'{"solutions": [ {"challenge')
        self.assertEqual((v["accepted"], v["code"], v["detail"]),
                         (False, "E_MALFORMED", "bad_json"))
        self.assertFalse(v["counts_against_quota"])

    def test_missing_moves(self):
        v = self.run_sub({"solutions": [{"challenge_id": "x",
                                         "move_spec_version": "ac-r2-v1"}]})
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

    def test_solution_count_limit(self):
        sols = [{"challenge_id": "c%d" % i, "move_spec_version": "ac-r2-v1",
                 "moves": []} for i in range(501)]
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
        sols = [{"challenge_id": "c%d" % i, "move_spec_version": "ac-r2-v1",
                 "moves": []} for i in range(3)]
        v = self.run_sub({"solutions": sols})
        self.assertTrue(v["accepted"])
        raw = json.dumps({"solutions": sols}).encode()
        v = submission.process_submission(raw, self.mini,
                                          structural_limits={"max_solutions": 2})
        self.assertEqual((v["code"], v["detail"]),
                         ("E_MALFORMED", "too_many_solutions"))

    # -- both tracks in one submission ----------------------------------
    def test_accept_mixed_tracks(self):
        """One submission may carry ac-v1 and sac-v1 solutions; each is
        verified by the spec its own challenge names."""
        v = self.run_sub({"solutions": [self.sol, self.stable_sol]})
        self.assertTrue(v["accepted"])
        self.assertEqual([r["ok"] for r in v["results"]], [True, True])
        self.assertEqual(v["results"][0]["certificate_hash"],
                         self.entry["certificate_hash"])
        self.assertEqual(v["results"][1]["length"],
                         self.entry["length"] + 2)
        self.assertEqual(v["results"][1]["work"], self.entry["work"] + 1)
        self.assertEqual([r["challenge_id"] for r in v["results"]],
                         [self.sol["challenge_id"],
                          self.stable_sol["challenge_id"]])

    def test_cross_track_spec_version_is_a_per_item_rejection(self):
        crossed = [dict(self.sol, move_spec_version="sac-r8-v1"),
                   dict(self.stable_sol, move_spec_version="ac-r2-v1")]
        v = self.run_sub({"solutions": crossed})
        self.assertTrue(v["accepted"])
        self.assertEqual([r["code"] for r in v["results"]],
                         ["E_SPEC_MISMATCH", "E_SPEC_MISMATCH"])
        self.assertEqual([r["expected"] for r in v["results"]],
                         ["ac-r2-v1", "sac-r8-v1"])

    def test_stable_moves_on_an_ac_challenge_are_bad_move_ids(self):
        """Move id 16 exists only in sac-r8-v1; on an ac-r2-v1 challenge
        it is out of range."""
        v = self.run_sub({"solutions": [dict(self.sol,
                                             moves=self.stable_sol["moves"])]})
        self.assertTrue(v["accepted"])
        self.assertEqual(v["results"][0]["code"], "E_BAD_MOVE_ID")
        self.assertEqual(v["results"][0]["move"], 16)

    def test_real_manifest_challenge_wrong_path(self):
        """Against the real 20,230-challenge manifest any path that
        merely walks legally but ends elsewhere yields E_NOT_TARGET —
        on either track, with the track's own final_shape shape."""
        ac, sac = util.paired_challenges(self.manifest)[0]
        v = self.run_sub({"solutions": [
            {"challenge_id": ac["challenge_id"],
             "move_spec_version": "ac-r2-v1", "moves": [6, 7]},
            {"challenge_id": sac["challenge_id"],
             "move_spec_version": "sac-r8-v1", "moves": [6, 7]}]},
            manifest=self.manifest)
        self.assertTrue(v["accepted"])
        shape = [len(w) for w in ac["initial_relators"]]
        for r in v["results"]:
            self.assertEqual(r["code"], "E_NOT_TARGET")
            self.assertEqual(r["final_shape"], shape)


if __name__ == "__main__":
    unittest.main()
