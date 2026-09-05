"""The contestant's documented example commands must work through the CLI."""

import json
import os
import subprocess
import sys
import unittest

from tests import util


EXAMPLES = util.REPO / "competition" / "examples"


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
        self.assertTrue(verdict["results"][0]["ok"])

    def test_training_manifest_matches_published_data_and_has_valid_hashes(self):
        manifest = util.load(EXAMPLES / "training_manifest.json")
        sample = util.load(EXAMPLES / "sample_submission.json")
        self.assertEqual(manifest["challenge_count"], 1)
        self.assertEqual(len(manifest["challenges"]), 1)
        challenge = manifest["challenges"][0]
        source = next(e for e in util.load_training()["instances"]
                      if e["training_id"] == challenge["challenge_id"])
        self.assertIs(challenge["scored"], False)
        self.assertEqual(challenge["base_score"], 0)
        self.assertIsNone(challenge["freeze_date"])
        self.assertIsNone(manifest["freeze_date"])
        for key in ("generators", "initial_relators", "target_relators",
                    "move_spec_version"):
            self.assertEqual(challenge[key], source[key], key)
        official = util.load_manifest()
        self.assertEqual(manifest["limits"], official["limits"])
        self.assertEqual(manifest["move_spec_hash"], official["move_spec_hash"])
        self.assertEqual(sample, {"solutions": [{
            "challenge_id": source["training_id"], "moves": source["moves"]}]})
        self.assertEqual(util.load(EXAMPLES / "sample_verdict.json")
                         ["results"][0]["certificate_hash"],
                         source["certificate_hash"])
        checked = self.run_cli(EXAMPLES / "training_manifest.json", check_hashes=True)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertIn("OK  1 challenges", checked.stdout)

    def test_deliberately_invalid_example_returns_not_target(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "invalid_submission.json")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(json.loads(result.stdout), {
            "accepted": True,
            "results": [{"challenge_id": "ac-v1-00001", "ok": False,
                         "code": "E_NOT_TARGET", "move_index": None,
                         "final_shape": [9, 18]}],
        })

    def test_training_example_is_unknown_to_official_manifest(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "sample_submission.json")
        self.assertEqual(result.returncode, 1, result.stdout)
        verdict = json.loads(result.stdout)
        self.assertTrue(verdict["accepted"])
        self.assertFalse(verdict["results"][0]["ok"])
        self.assertEqual(verdict["results"][0]["code"], "E_UNKNOWN_CHALLENGE")


if __name__ == "__main__":
    unittest.main()
