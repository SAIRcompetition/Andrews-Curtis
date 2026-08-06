"""Golden-vector conformance runner (DESIGN.md §9.2, acceptance rows 5 and 15).

``golden_vectors.json`` is self-contained: it embeds every challenge its
vectors reference, so third parties can confirm conformance with nothing
but this package and that file.  Expected values are compared as
subsets: every key present in ``expected`` must match the actual result
exactly.
"""

import json

from . import core, submission

FORMAT = "acms-golden-v1"


def _subset_match(expected, actual):
    mismatches = []
    for k, v in expected.items():
        if k == "results":
            actual_list = actual.get("results", [])
            if len(actual_list) != len(v):
                mismatches.append("results: expected %d entries, got %d"
                                  % (len(v), len(actual_list)))
                continue
            for i, (e, a) in enumerate(zip(v, actual_list)):
                mismatches += ["results[%d].%s" % (i, m)
                               for m in _subset_match(e, a)]
        elif actual.get(k) != v:
            mismatches.append("%s: expected %r, got %r" % (k, v, actual.get(k)))
    return mismatches


def run_vectors(doc):
    """Run all vectors; returns a list of {name, passed, mismatches}."""
    if doc.get("format") != FORMAT:
        raise ValueError("unsupported golden vector format: %r"
                         % (doc.get("format"),))
    challenges = doc["challenges"]
    default_limits = doc["default_limits"]
    mini_manifest = {
        "limits": default_limits,
        "challenges": list(challenges.values()),
    }
    report = []

    for vec in doc.get("verify_vectors", []):
        challenge = challenges[vec["challenge_id"]]
        limits = vec.get("limits", default_limits)
        version = vec.get("move_spec_version", challenge["move_spec_version"])
        actual = core.verify(challenge, vec["moves"], version, limits)
        mism = _subset_match(vec["expected"], actual)
        report.append({"name": vec["name"], "passed": not mism,
                       "mismatches": mism})

    for vec in doc.get("submission_vectors", []):
        raw = vec["raw"].encode("utf-8")
        actual = submission.process_submission(raw, mini_manifest)
        mism = _subset_match(vec["expected"], actual)
        report.append({"name": vec["name"], "passed": not mism,
                       "mismatches": mism})

    return report


def run_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        return run_vectors(json.load(fh))
