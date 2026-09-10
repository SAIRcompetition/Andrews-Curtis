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
    """Recover the ordered generators and initial relators from the presentation."""
    presentation = re.fullmatch(
        r"Presentation: <([^<>|]+) \| (.+) = 1; (.+) = 1>\.",
        description)
    if presentation is None:
        raise ValueError("description does not contain only the specified presentation")
    generators, first, second = presentation.groups()
    return {
        "generators": generators.split(", "),
        "initial_relators": [read_word(first), read_word(second)],
    }


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
        for name, _ in PROBLEMS:
            for entry in self.documents[name]:
                cid = entry["challenge_id"]
                challenge = index[cid]
                parsed = read_description(entry["description"])
                for key in ("generators", "initial_relators"):
                    self.assertEqual(parsed[key], challenge[key], (cid, key))


if __name__ == "__main__":
    unittest.main()
