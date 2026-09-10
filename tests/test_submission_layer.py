"""TXT grammar, whole-submission rejection, and unchanged per-path verdicts."""

import json
import unittest

from acms_verify import core, stable_core, submission
from tests import util


def txt(*solutions):
    """Write test records without importing the production parser or builders."""
    return "".join(s["challenge_id"] + ": " + json.dumps(s["moves"]) + "\n"
                   for s in solutions)


class TestSubmissionLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.index = submission.build_challenge_index(cls.manifest)
        cls.entry = min(util.load_training()["instances"], key=lambda e: e["length"])
        cls.sol = {"challenge_id": cls.entry["training_id"], "moves": cls.entry["moves"]}
        stable = dict(cls.entry,
                      training_id="sac-train-" + cls.entry["training_id"].rsplit("-", 1)[1],
                      move_spec_version=stable_core.MOVE_SPEC_VERSION,
                      target_relators=[], moves=cls.entry["moves"] + [16, 15])
        cls.stable_challenge = util.training_challenge(stable)
        cls.stable_sol = {"challenge_id": stable["training_id"], "moves": stable["moves"]}
        cls.mini = {"limits": cls.manifest["limits"],
                    "challenges": cls.manifest["challenges"][:3]
                    + [util.training_challenge(cls.entry), cls.stable_challenge]}

    def run_sub(self, raw, manifest=None, **kwargs):
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return submission.process_submission(raw, manifest or self.mini, **kwargs)

    def assert_malformed(self, raw, detail, line_number=None, **kwargs):
        verdict = self.run_sub(raw, **kwargs)
        expected = {"accepted": False, "code": "E_MALFORMED",
                    "counts_against_quota": False, "detail": detail}
        if line_number is not None:
            expected["line_number"] = line_number
        self.assertEqual(verdict, expected)

    def test_success_uses_official_spec_and_unchanged_certificate(self):
        verdict = self.run_sub(txt(self.sol))
        self.assertTrue(verdict["accepted"])
        self.assertTrue(verdict["results"][0]["ok"])
        self.assertEqual(verdict["results"][0]["certificate_hash"],
                         self.entry["certificate_hash"])
        expected = core.verify(util.training_challenge(self.entry), self.sol["moves"],
                               self.entry["move_spec_version"], self.mini["limits"])
        expected.pop("peak_total_relator_length")
        self.assertEqual(verdict["results"], [dict(expected, challenge_id=self.sol["challenge_id"])])

    def test_per_item_errors_do_not_reject_submission(self):
        verdict = self.run_sub(txt(
            {"challenge_id": "unknown-9999", "moves": []},
            {"challenge_id": "ac-00001", "moves": [14]},
            {"challenge_id": "ac-00002", "moves": []}, self.sol))
        self.assertTrue(verdict["accepted"])
        self.assertEqual([r.get("code") for r in verdict["results"][:3]],
                         ["E_UNKNOWN_CHALLENGE", "E_BAD_MOVE_ID", "E_NOT_TARGET"])
        self.assertEqual(verdict["results"][1]["move_index"], 0)
        self.assertTrue(verdict["results"][3]["ok"])

    def test_mixed_problems_dispatch_without_client_version(self):
        verdict = self.run_sub(txt(self.sol, self.stable_sol))
        self.assertTrue(verdict["accepted"])
        self.assertEqual([r["ok"] for r in verdict["results"]], [True, True])
        for result in verdict["results"]:
            self.assertNotIn("peak_total_relator_length", result)
        expected = stable_core.verify(self.stable_challenge, self.stable_sol["moves"],
                                      stable_core.MOVE_SPEC_VERSION, self.mini["limits"])
        expected.pop("peak_total_relator_length")
        self.assertEqual(verdict["results"][1], dict(
            expected, challenge_id=self.stable_sol["challenge_id"]))
        self.assertEqual(verdict["results"][1]["length"], self.entry["length"] + 2)
        self.assertEqual(verdict["results"][1]["work"], self.entry["work"] + 1)

    def test_both_problems_still_enforce_relator_growth_limit(self):
        challenges = [
            {"challenge_id": cid, "move_spec_version": version,
             "initial_relators": [[1], [2]], "target_relators": target}
            for cid, version, target in (
                ("test-ac", "ac-r2-v1", [[1], [2]]),
                ("test-stable", "sac-r8-v1", []),
            )
        ]
        manifest = {"challenges": challenges,
                    "limits": {"max_path_length": 10,
                               "max_total_relator_length": 2, "max_work": 100}}
        # Move 2 changes (x, y) to (xy, y), exceeding the limit of two letters.
        verdict = self.run_sub("test-ac: [2]\ntest-stable: [2]", manifest=manifest)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(verdict["results"], [
            {"challenge_id": c["challenge_id"], "ok": False,
             "code": "E_LENGTH_LIMIT", "move_index": 0,
             "total_relator_length": 3, "max_total_relator_length": 2}
            for c in challenges
        ])

    def test_challenge_id_selects_target_and_valid_move_ids(self):
        verdict = self.run_sub(txt(dict(self.sol, moves=self.stable_sol["moves"]),
                                   dict(self.stable_sol, moves=self.sol["moves"])))
        self.assertTrue(verdict["accepted"])
        self.assertEqual([r["code"] for r in verdict["results"]],
                         ["E_BAD_MOVE_ID", "E_NOT_TARGET"])

    def test_comments_never_change_verdict_or_certificate(self):
        baseline = txt(self.sol, self.stable_sol)
        decorated = "\n# 方法：搜索； score=999, ok=true\n# " + "a" * 3000 + "\n"
        decorated += "# " + txt(self.sol)  # A commented duplicate is not a record.
        decorated += "\n".join(line + " # length=0; move_spec_version=wrong; anything"
                                for line in baseline.splitlines())
        self.assertEqual(self.run_sub(decorated), self.run_sub(baseline))

    def test_utf8_bom_crlf_and_surrounding_whitespace(self):
        baseline = txt(self.sol, self.stable_sol)
        decorated = "\ufeff# 中文注释\r\n\t\r\n"
        decorated += "\r\n".join(" \t" + line.replace(": ", " \t: \t") + " \t"
                                  for line in baseline.splitlines())
        self.assertEqual(self.run_sub(bytearray(decorated.encode())), self.run_sub(baseline))
        self.assertEqual(self.run_sub(baseline.rstrip("\n")), self.run_sub(baseline))

    def test_invalid_utf8_is_rejected_before_line_syntax(self):
        self.assert_malformed(b"not a record\n#\xff", "bad_utf8")

    def test_bare_text_and_bad_ids_are_not_silently_ignored(self):
        for line in ("a note without #", "ac-00001 [0]", ": []", "bad id: []",
                     '"ac-00001": []', "ac-00001: [] score=99"):
            detail = "bad_moves_json" if line.startswith("ac-00001:") else "bad_solution_line"
            with self.subTest(line=line):
                self.assert_malformed("# comment\n\n" + line, detail, 3)

    def test_moves_must_be_an_array_on_the_same_line(self):
        for value in ("", "null", "false", "0", '"[0]"', "{\"moves\": []}"):
            with self.subTest(value=value):
                self.assert_malformed("ac-00001: " + value, "moves_not_array", 1)
        for value in ("[", "[0,]", "[0 1]", "[0] [1]", "[0]\n1]", "[0,\n1]"):
            with self.subTest(value=value):
                line_number = 2 if value == "[0]\n1]" else 1
                detail = "bad_solution_line" if line_number == 2 else "bad_moves_json"
                self.assert_malformed("ac-00001: " + value, detail, line_number)

    def test_legacy_json_envelopes_are_rejected(self):
        doc = {"method": "search", "notes": "old format", "solutions": [self.sol]}
        for raw in (json.dumps(doc), json.dumps(doc, indent=2), json.dumps([self.sol]), "{}"):
            with self.subTest(raw=raw):
                self.assert_malformed(raw, "bad_solution_line", 1)

    def test_extra_submission_fields_must_be_comments(self):
        for suffix in ("method: bfs", "notes: explanation", "score: 1",
                       "move_spec_version: ac-r2-v1"):
            self.assert_malformed(txt(self.sol) + suffix, "moves_not_array", 2)
            self.assertEqual(self.run_sub(txt(self.sol) + "# " + suffix),
                             self.run_sub(txt(self.sol)))

    def test_invalid_move_values_remain_per_path_errors(self):
        for value in (True, False, 1.0, "1", None, [1], {"score": 1}, -1, 257):
            for solution in (self.sol, self.stable_sol):
                with self.subTest(value=value, challenge=solution["challenge_id"]):
                    verdict = self.run_sub(txt(dict(solution, moves=[0, value])))
                    self.assertTrue(verdict["accepted"])
                    self.assertEqual(verdict["results"], [{
                        "challenge_id": solution["challenge_id"], "ok": False,
                        "code": "E_BAD_MOVE_ID", "move_index": 1, "move": value}])

    def test_deep_nesting_and_huge_integers_fail_without_echoing_payload(self):
        for payload in ("[" * 3000 + "0" + "]" * 3000,
                        "[" + "9" * 10000 + "]",
                        "[-" + "9" * 10000 + "]"):
            self.assert_malformed("# comment\nac-00001: " + payload,
                                  "bad_moves_json", 2)

    def test_non_json_and_nonfinite_numbers_are_rejected(self):
        for payload in ("[NaN]", "[Infinity]", "[-Infinity]", "[1e9999]"):
            self.assert_malformed("ac-00001: " + payload, "bad_moves_json", 1)

    def test_json_strings_do_not_confuse_nesting_or_physical_line_count(self):
        value = "[" * 100 + '\\"' + "\u2028"
        raw = self.sol["challenge_id"] + ": " + json.dumps([value], ensure_ascii=False)
        verdict = self.run_sub(raw)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(verdict["results"][0]["code"], "E_BAD_MOVE_ID")
        self.assertEqual(verdict["results"][0]["move"], value)
        # The verdict remains valid, bounded JSON even for a nested bad move.
        nested = [0]
        for _ in range(30):
            nested = [nested]
        json.dumps(self.run_sub(txt(dict(self.sol, moves=[nested]))), allow_nan=False)

    def test_duplicate_ids_reject_the_whole_file_with_record_and_line_indexes(self):
        raw = "# heading\n\n" + txt(self.sol) + "# separator\n" + txt(dict(self.sol, moves=[]))
        self.assertEqual(self.run_sub(raw), {
            "accepted": False, "code": "E_DUPLICATE_CHALLENGE", "counts_against_quota": False,
            "challenge_id": self.sol["challenge_id"], "index": 1, "line_number": 5})

    def test_solution_count_limit_counts_records_not_comments(self):
        records = "".join("unknown-%d: []\n# comment\n\n" % i for i in range(500))
        verdict = self.run_sub(records)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(len(verdict["results"]), 500)
        self.assertEqual(self.run_sub(records + "unknown-500: []\n"), {
            "accepted": False, "code": "E_MALFORMED", "counts_against_quota": False,
            "detail": "too_many_solutions", "solutions": 501, "max_solutions": 500})

    def test_body_limit_includes_comments_and_precedes_decoding(self):
        prefix = txt(self.sol).encode("utf-8") + b"#"
        padding = 10_000_000 - len(prefix)
        raw = prefix + "é".encode("utf-8") * (padding // 2) + b"a" * (padding % 2)
        # A real solution with multibyte notes fits exactly at 10 MB.
        self.assertEqual(len(raw), 10_000_000)
        self.assertEqual(self.run_sub(raw), self.run_sub(txt(self.sol)))
        self.assertEqual(self.run_sub(raw + b"\xff"), {
            "accepted": False, "code": "E_MALFORMED", "counts_against_quota": False,
            "detail": "body_too_large", "body_bytes": 10_000_001,
            "max_body_bytes": 10_000_000})

    def test_empty_and_comment_only_files_have_no_solutions(self):
        for raw in ("", " \r\n\t\n", "# notes\n# score: 100", "\ufeff"):
            self.assert_malformed(raw, "no_solutions")

    def test_structural_limits_remain_configurable(self):
        raw = "c1: []\nc2: []\nc3: []\n"
        self.assertTrue(self.run_sub(raw)["accepted"])
        limited = self.run_sub(raw, structural_limits={"max_solutions": 2})
        self.assertEqual((limited["code"], limited["detail"], limited["max_solutions"]),
                         ("E_MALFORMED", "too_many_solutions", 2))
        limited = self.run_sub(raw, structural_limits={"max_body_bytes": 10})
        self.assertEqual((limited["code"], limited["detail"], limited["max_body_bytes"]),
                         ("E_MALFORMED", "body_too_large", 10))

    def test_all_line_syntax_precedes_count_duplicates_and_per_path_errors(self):
        raw = "ac-00001: [14]\nac-00001: []\ninvalid text"
        self.assert_malformed(raw, "bad_solution_line", 3,
                              structural_limits={"max_solutions": 1})
        counted = self.run_sub("ac-00001: [14]\nac-00001: []",
                               structural_limits={"max_solutions": 1})
        self.assertEqual(counted["detail"], "too_many_solutions")
        self.assertEqual(self.run_sub("ac-00001: [14]\nac-00001: []")["code"],
                         "E_DUPLICATE_CHALLENGE")

    def test_path_length_still_precedes_invalid_move_values(self):
        manifest = dict(self.mini, limits=dict(self.mini["limits"], max_path_length=1))
        verdict = self.run_sub(txt(dict(self.sol, moves=[True, 0])), manifest=manifest)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(verdict["results"][0]["code"], "E_PATH_TOO_LONG")

    def test_real_manifest_challenge_wrong_path(self):
        verdict = self.run_sub("ac-00001: [6, 7]", manifest=self.manifest)
        self.assertTrue(verdict["accepted"])
        self.assertEqual(verdict["results"][0]["code"], "E_NOT_TARGET")

    def test_current_ids_dispatch_and_retired_ids_are_unknown(self):
        ids = ("ac-00001", "sac-00001", "ac-v1-00001", "sac-v1-00001")
        verdict = self.run_sub("\n".join(cid + ": [14]" for cid in ids), manifest=self.manifest)
        self.assertTrue(verdict["accepted"])
        self.assertEqual([r["challenge_id"] for r in verdict["results"]], list(ids))
        self.assertEqual([r["code"] for r in verdict["results"]], [
            "E_BAD_MOVE_ID", "E_NOT_TARGET", "E_UNKNOWN_CHALLENGE", "E_UNKNOWN_CHALLENGE"])
        self.assertEqual(verdict["results"][0]["move_index"], 0)
        self.assertEqual(verdict["results"][1]["final_shape"],
                         [len(w) for w in self.index["sac-00001"]["initial_relators"]] + [1])


if __name__ == "__main__":
    unittest.main()
