"""Contestant problem descriptions must preserve the verifier's mathematical inputs.

Parse the published prose independently; never import its renderer or compare
against a second rendering of the same source record.
"""

import re
import unittest

from tests import util


LETTERS = {"x": 1, "x^-1": -1, "y": 2, "y^-1": -2}
PROBLEMS = (("ac.json", util.AC_PREFIX), ("stable_ac.json", util.STABLE_PREFIX))


def read_word(text):
    """Decode the description's literal generator letters in their stated order."""
    if text == "1":
        return []
    tokens = text.split(" ")
    if not tokens or any(token not in LETTERS for token in tokens):
        raise ValueError("invalid word in problem description: " + repr(text))
    return [LETTERS[token] for token in tokens]


def read_description(description):
    """Recover the initial relators, target, and permitted generator changes."""
    presentation = re.fullmatch(
        r"Presentation: <([^<>|]+) \| (.+) = 1; (.+) = 1>\. (.+)",
        description)
    if presentation is None:
        raise ValueError("description does not contain the specified presentation")
    generators, first, second, task = presentation.groups()
    result = {
        "generators": generators.split(", "),
        "initial_relators": [read_word(first), read_word(second)],
    }
    ordinary = re.fullmatch(
        r"Find a short sequence of AC moves to reach the ordered relators "
        r"\(([^()]+)\), without adding or removing generators\.", task)
    if ordinary is not None:
        result.update(
            move_spec_version="ac-r2-v1",
            target_relators=[read_word(word) for word in ordinary.group(1).split(", ")],
            max_rank=len(result["generators"]),
            permits_generator_changes=False,
        )
        return result
    stable = re.fullmatch(
        r"Find a short sequence of Stable AC moves to reach the empty presentation "
        r"\(no generators or relators\), using at most ([0-9]+) generators\.", task)
    if stable is not None:
        result.update(move_spec_version="sac-r8-v1", target_relators=[],
                      max_rank=int(stable.group(1)), permits_generator_changes=True)
        return result
    raise ValueError("description does not state the required target and move constraints")


class TestProblemDescriptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = util.load_manifest()
        cls.documents = {name: util.load(util.PROBLEMS / name) for name, _ in PROBLEMS}

    def test_only_id_and_description_are_published_for_each_problem(self):
        for name, _ in PROBLEMS:
            entries = self.documents[name]
            self.assertIsInstance(entries, list, name)
            self.assertEqual(len(entries), 10115, name)
            for entry in entries:
                self.assertIsInstance(entry, dict, name)
                self.assertEqual(set(entry), {"challenge_id", "description"}, name)
                self.assertIsInstance(entry["challenge_id"], str, name)
                self.assertIsInstance(entry["description"], str, entry["challenge_id"])
                self.assertTrue(entry["description"], entry["challenge_id"])

    def test_ids_match_the_complete_verifier_pool_in_order(self):
        for name, prefix in PROBLEMS:
            expected = util.challenges_by_prefix(self.manifest, prefix)
            ids = [entry["challenge_id"] for entry in self.documents[name]]
            self.assertEqual(ids, [challenge["challenge_id"] for challenge in expected], name)
            self.assertEqual(len(ids), len(set(ids)), name)
        self.assertEqual(
            [entry["challenge_id"][len(util.AC_PREFIX):]
             for entry in self.documents["ac.json"]],
            [entry["challenge_id"][len(util.STABLE_PREFIX):]
             for entry in self.documents["stable_ac.json"]],
        )

    def test_every_description_decodes_to_its_original_problem(self):
        index = {c["challenge_id"]: c for c in self.manifest["challenges"]}
        spec_headers = {s["move_spec_version"]: s for s in self.manifest["move_specs"]}
        for name, _ in PROBLEMS:
            for entry in self.documents[name]:
                cid = entry["challenge_id"]
                challenge = index[cid]
                parsed = read_description(entry["description"])
                for key in ("generators", "initial_relators", "target_relators", "move_spec_version"):
                    self.assertEqual(parsed[key], challenge[key], (cid, key))
                spec = spec_headers[challenge["move_spec_version"]]
                self.assertEqual(parsed["max_rank"], spec["max_rank"], cid)
                self.assertEqual(parsed["permits_generator_changes"],
                                 challenge["move_spec_version"] == "sac-r8-v1", cid)


if __name__ == "__main__":
    unittest.main()
