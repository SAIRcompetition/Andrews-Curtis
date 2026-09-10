"""The contestant's documented example commands must work through the CLI."""

import json
import os
import subprocess
import sys
import unittest

from acms_verify import canon, submission
from tests import util
from tests.test_problems import read_description


EXAMPLES = util.EXAMPLES


def sample_solutions():
    """Read the published TXT sample independently of the submission parser."""
    solutions = []
    for raw_line in (EXAMPLES / "sample_submission.txt").read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            cid, moves = line.split(":", 1)
            solutions.append({"challenge_id": cid.strip(), "moves": json.loads(moves)})
    return solutions


class TestExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.training_manifest = util.load(EXAMPLES / "training_manifest.json")
        cls.training_index = {c["challenge_id"]: c
                              for c in cls.training_manifest["challenges"]}
        cls.problems = (
            ("ac.jsonl", "ms-train-", util.load_training(), "ac-r2-v1", [[1], [2]]),
            ("stable_ac.jsonl", "sac-train-", util.load_stable_training(), "sac-r8-v1", []),
        )
        cls.source_by_id = {
            prefix + entry["training_id"].rsplit("-", 1)[1]: entry
            for _, prefix, source, _, _ in cls.problems
            for entry in source["instances"]
        }

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
                              EXAMPLES / "sample_submission.txt")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout,
                         (EXAMPLES / "sample_verdict.json").read_text())
        verdict = json.loads(result.stdout)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(len(verdict["results"]), 2)
        self.assertTrue(all(v["ok"] for v in verdict["results"]))

    def test_training_manifest_matches_published_data_and_has_valid_hashes(self):
        manifest = self.training_manifest
        sample = sample_solutions()
        self.assertEqual(manifest["challenge_count"], 848)
        self.assertEqual(manifest["presentation_count"], 424)
        self.assertEqual(len(manifest["challenges"]), 848)
        self.assertEqual(set(self.training_index), set(self.source_by_id))
        for _, prefix, source_doc, version, target in self.problems:
            self.assertEqual(len(source_doc["instances"]), 424)
            for entry in source_doc["instances"]:
                cid = prefix + entry["training_id"].rsplit("-", 1)[1]
                challenge = self.training_index[cid]
                self.assertIs(challenge["scored"], False, cid)
                self.assertEqual(challenge["base_score"], 0, cid)
                self.assertIsNone(challenge["freeze_date"], cid)
                self.assertEqual(challenge["move_spec_version"], version, cid)
                self.assertEqual(challenge["target_relators"], target, cid)
                for key in ("generators", "initial_relators", "target_relators", "move_spec_version"):
                    self.assertEqual(challenge[key], entry[key], (cid, key))
        receipts = util.load(EXAMPLES / "sample_verdict.json")["results"]
        self.assertEqual([s["challenge_id"] for s in sample],
                         ["ms-train-0160", "sac-train-0160"])
        self.assertEqual(len(receipts), 2)
        for solution, receipt in zip(sample, receipts):
            cid = solution["challenge_id"]
            challenge = self.training_index[cid]
            source = self.source_by_id[cid]
            self.assertEqual(solution, {"challenge_id": cid,
                                        "moves": source["moves"]})
            self.assertEqual(receipt["challenge_id"], cid)
            self.assertEqual(receipt["certificate_hash"], canon.certificate_hash(
                cid, challenge["move_spec_version"], source["moves"]))
        self.assertIsNone(manifest["freeze_date"])
        sample_challenges = [self.training_index[s["challenge_id"]]
                             for s in sample]
        self.assertEqual(sample_challenges[0]["initial_relators"],
                         sample_challenges[1]["initial_relators"])
        self.assertNotEqual(sample[0]["challenge_id"], sample[1]["challenge_id"])
        official = util.load_manifest()
        self.assertEqual(manifest["limits"], official["limits"])
        self.assertEqual(manifest["move_specs"], official["move_specs"])
        self.assertFalse(set(self.training_index) &
                         {c["challenge_id"] for c in official["challenges"]})
        training_presentations = {util.canon_pair(c["initial_relators"])
                                  for c in manifest["challenges"]}
        self.assertEqual(len(training_presentations), 424)
        self.assertFalse(training_presentations &
                         {util.canon_pair(c["initial_relators"])
                          for c in official["challenges"]})
        checked = self.run_cli(EXAMPLES / "training_manifest.json", check_hashes=True)
        self.assertEqual(checked.returncode, 0, checked.stdout)
        self.assertIn("OK  848 challenges", checked.stdout)

    def test_training_jsonl_descriptions_preserve_all_source_presentations(self):
        for name, prefix, source, _, _ in self.problems:
            raw = (EXAMPLES / name).read_bytes()
            rows = [json.loads(line) for line in raw.splitlines()]
            self.assertEqual(len(rows), 424, name)
            self.assertEqual(raw, "".join(json.dumps(row) + "\n" for row in rows).encode(), name)
            self.assertEqual([row["challenge_id"] for row in rows],
                             [prefix + e["training_id"].rsplit("-", 1)[1]
                              for e in source["instances"]], name)
            for row in rows:
                cid = row["challenge_id"]
                self.assertEqual(set(row), {"challenge_id", "description"}, cid)
                parsed = read_description(row["description"])
                for key in ("generators", "initial_relators"):
                    self.assertEqual(parsed[key], self.source_by_id[cid][key], (cid, key))

    def test_all_published_training_paths_succeed_through_submission_dispatch(self):
        for _, prefix, source, _, _ in self.problems:
            solutions = [{"challenge_id": prefix + e["training_id"].rsplit("-", 1)[1],
                          "moves": e["moves"]} for e in source["instances"]]
            # Each problem's 424 solutions fit the ordinary 500-solution limit.
            verdict = submission.process_submission(
                "".join(s["challenge_id"] + ": " + json.dumps(s["moves"]) + "\n"
                        for s in solutions).encode(), self.training_manifest)
            self.assertTrue(verdict["accepted"], verdict)
            self.assertEqual([r["challenge_id"] for r in verdict["results"]],
                             [s["challenge_id"] for s in solutions])
            for receipt in verdict["results"]:
                cid = receipt["challenge_id"]
                entry = self.source_by_id[cid]
                self.assertTrue(receipt["ok"], receipt)
                for key in ("length", "peak_total_relator_length", "work"):
                    self.assertEqual(receipt[key], entry[key], (cid, key))
                self.assertEqual(receipt["certificate_hash"], canon.certificate_hash(
                    cid, entry["move_spec_version"], entry["moves"]), cid)

    def test_deliberately_invalid_example_returns_not_target(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "invalid_submission.txt")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(json.loads(result.stdout), {
            "accepted": True,
            "results": [{"challenge_id": "ac-00001", "ok": False,
                         "code": "E_NOT_TARGET", "move_index": None,
                         "final_shape": [9, 18]}],
        })

    def test_training_example_is_unknown_to_official_manifest(self):
        result = self.run_cli(util.MANIFEST_PATH,
                              EXAMPLES / "sample_submission.txt")
        self.assertEqual(result.returncode, 1, result.stdout)
        verdict = json.loads(result.stdout)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(len(verdict["results"]), 2)
        for result in verdict["results"]:
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "E_UNKNOWN_CHALLENGE")


if __name__ == "__main__":
    unittest.main()
