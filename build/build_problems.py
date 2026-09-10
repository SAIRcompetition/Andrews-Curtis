#!/usr/bin/env python3
"""Generate two contestant-facing JSONL problem files from the verifier manifest."""

import argparse
import json
from pathlib import Path
import re
import sys


REPO = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO / "competition/tools/verifier/data/manifest.json"
PROBLEMS_DIR = REPO / "competition/problems"

LETTERS = {1: "x", -1: "x^-1", 2: "y", -2: "y^-1"}
PROBLEM_SPECS = {
    "ac-r2-v1": ("ac.jsonl", "ac-", [[1], [2]]),
    "sac-r8-v1": ("stable_ac.jsonl", "sac-", []),
}


def _check_version(version):
    if not isinstance(version, str) or version not in PROBLEM_SPECS:
        raise ValueError("unsupported move_spec_version: %r" % (version,))


def _word(word, challenge_id):
    if not isinstance(word, list):
        raise ValueError("%s: each relator must be a list" % challenge_id)
    if any(type(letter) is not int or letter not in LETTERS for letter in word):
        raise ValueError("%s: relator letters must be integers 1, -1, 2, or -2"
                         % challenge_id)
    return " ".join(LETTERS[letter] for letter in word) if word else "1"


def presentation_description(generators, relators, identifier="presentation"):
    """Use the same word notation for official and training problems."""
    if generators != ["x", "y"]:
        raise ValueError("%s: generators must be ['x', 'y']" % identifier)
    if not isinstance(relators, list) or len(relators) != 2:
        raise ValueError("%s: exactly two initial relators are required" % identifier)
    words = [_word(word, identifier) for word in relators]
    return "Presentation: <x, y | %s = 1; %s = 1>." % (words[0], words[1])


def render_problems(manifest):
    """Return descriptions without changing relator order or reducing any word."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if "manifest_version" in manifest and manifest["manifest_version"] != "acms-v3":
        raise ValueError("unsupported manifest_version: %r" % manifest["manifest_version"])
    if "generators" in manifest and manifest["generators"] != ["x", "y"]:
        raise ValueError("manifest generators must be ['x', 'y']")
    if "move_specs" in manifest:
        if not isinstance(manifest["move_specs"], list):
            raise ValueError("manifest move_specs must be a list")
        for spec in manifest["move_specs"]:
            if not isinstance(spec, dict):
                raise ValueError("each move specification must be an object")
            _check_version(spec.get("move_spec_version"))

    challenges = manifest.get("challenges")
    if not isinstance(challenges, list):
        raise ValueError("manifest challenges must be a list")
    if "challenge_count" in manifest and manifest["challenge_count"] != len(challenges):
        raise ValueError("manifest challenge_count does not match its challenges")

    rendered = {"ac.jsonl": [], "stable_ac.jsonl": []}
    seen = set()
    for challenge in challenges:
        if not isinstance(challenge, dict):
            raise ValueError("each challenge must be an object")
        version = challenge.get("move_spec_version")
        _check_version(version)
        filename, prefix, target = PROBLEM_SPECS[version]
        challenge_id = challenge.get("challenge_id")
        if not isinstance(challenge_id, str) or not re.fullmatch(
                re.escape(prefix) + r"[0-9]{5}", challenge_id):
            raise ValueError("invalid challenge_id for %s: %r" % (version, challenge_id))
        if challenge_id in seen:
            raise ValueError("duplicate challenge_id: " + challenge_id)
        seen.add(challenge_id)
        if challenge.get("target_relators") != target:
            raise ValueError("%s: target does not match %s" % (challenge_id, version))
        rendered[filename].append({
            "challenge_id": challenge_id,
            "description": presentation_description(
                challenge.get("generators"), challenge.get("initial_relators"),
                challenge_id),
        })
    return rendered


def serialize(rows):
    """Serialize one problem object per line, with a final newline."""
    return "".join(json.dumps(row) + "\n" for row in rows)


def write_problems(manifest, directory):
    rendered = render_problems(manifest)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in rendered.items():
        (directory / name).write_text(serialize(rows), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH,
                        help="verifier manifest to read")
    parser.add_argument("--output", type=Path, default=PROBLEMS_DIR,
                        help="directory for ac.jsonl and stable_ac.jsonl")
    parser.add_argument("--check", action="store_true",
                        help="fail if either problem list is missing or differs byte for byte")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.check:
            stale = [name for name, rows in render_problems(manifest).items()
                     if not (args.output / name).is_file()
                     or (args.output / name).read_bytes() != serialize(rows).encode("utf-8")]
            if stale:
                print("stale problem lists: %s; run python3 build/build_problems.py"
                      % ", ".join(stale), file=sys.stderr)
                return 1
            print("OK: problem lists match the verifier manifest")
        else:
            write_problems(manifest, args.output)
            print("wrote ac.jsonl and stable_ac.jsonl to %s" % args.output)
    except (OSError, ValueError) as exc:
        print("Problem generation failed: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
