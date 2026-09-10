"""The contestant's documented example commands must work through the CLI."""

import json
import os
import subprocess
import sys
import unittest

from acms_verify import canon
from tests import util


EXAMPLES = util.EXAMPLES


class TestExamples(unittest.TestCase):
    def run_cli(self, manifest, submission=None, *, check_hashes=False):
        args = [sys.executable, "-m", "acms_verify", "--manifest", str(manifest)]
        if submission is not None:
            args.extend(["--submission", str(submission), "--pretty"])
        if check_hashes:
            args.append("--check-hashes")
        env = dict(os.environ,
                   PYTHONPATH=str(util.REPO / "competition" / "tools" / "verifier"))
        result = subprocess.run(args, cwd=util.REPO, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.stderr, "")
        return result

    def test_documented_success_matches_full_verdict(self):
        result = self.run_cli(EXAMPLES / "training_manifest.json",
                              EXAMPLES / "sample_submission.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout,
                         (EXAMPLES / "sample_verdict.json").read_text())
        verdict = json.loads(result.stdout)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(len(verdict["results"]), 2)
        self.assertTrue(all(v["ok"] for v in verdict["results"]))

    def test_training_manifest_matches_published_data_and_has_valid_hashes(self):
        manifest = util.load(EXAMPLES / "training_manifest.json")
        sample = util.load(EXAMPLES / "sample_submission.json")
        self.assertEqual(manifest["challenge_count"], 2)
        self.assertEqual(manifest["presentation_count"], 1)
        self.assertEqual(len(manifest["challenges"]), 2)
        sources = (util.load_training(), util.load_stable_training())
        receipts = util.load(EXAMPLES / "sample_verdict.json")["results"]
        for challenge, solution, source_doc, receipt in zip(
                manifest["challenges"], sample["solutions"], sources, receipts):
            source = next(e for e in source_doc["instances"]
                          if e["initial_relators"] == challenge["initial_relators"])
            self.assertIs(challenge["scored"], False)
            self.assertEqual(challenge["base_score"], 0)
            self.assertIsNone(challenge["freeze_date"])
            for key in ("generators", "initial_relators", "target_relators", "move_spec_version"):
                self.assertEqual(challenge[key], source[key], key)
            self.assertEqual(solution, {"challenge_id": challenge["challenge_id"],
                                        "moves": source["moves"]})
            self.assertEqual(receipt["certificate_hash"], canon.certificate_hash(
                challenge["challenge_id"], challenge["move_spec_version"], source["moves"]))
        self.assertIsNone(manifest["freeze_date"])
        self.assertEqual(manifest["challenges"][0]["initial_relators"],
                         manifest["challenges"][1]["initial_relators"])
        self.assertNotEqual(sample["solutions"][0]["challenge_id"],
                            sample["solutions"][1]["challenge_id"])
        official = util.load_manifest()
        self.assertEqual(manifest["limits"], official["limits"])
        self.assertEqual(manifest["move_specs"], official["move_specs"])
        checked = self.run_cli(EXAMPLES / "training_manifest.json", check_hashes=True)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertIn("OK  2 challenges", checked.stdout)

    def test_deliberately_invalid_example_returns_not_target(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "invalid_submission.json")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(json.loads(result.stdout), {
            "accepted": True,
            "results": [{"challenge_id": "ac-00001", "ok": False,
                         "code": "E_NOT_TARGET", "move_index": None,
                         "final_shape": [9, 18]}],
        })

    def test_training_example_is_unknown_to_official_manifest(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "sample_submission.json")
        self.assertEqual(result.returncode, 1, result.stdout)
        verdict = json.loads(result.stdout)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(len(verdict["results"]), 2)
        for result in verdict["results"]:
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "E_UNKNOWN_CHALLENGE")


if __name__ == "__main__":
    unittest.main()
