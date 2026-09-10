#!/usr/bin/env python3
"""Derive runnable public examples from the existing frozen public data.

From the repository root, run ``python3 build/build_examples.py`` to regenerate,
or add ``--check`` to reject stale examples without writing any files.
The challenge manifest, move specification, and training data are read only.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "build"))
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import canon, specs, submission  # noqa: E402
from build_problems import presentation_description, serialize  # noqa: E402


def json_text(value, *, sort_keys=False):
    return json.dumps(value, indent=2, sort_keys=sort_keys) + "\n"


def _training_index(source, version):
    """Validate a frozen training source and index its 424 distinct IDs."""
    spec = specs.get(version)
    if (source.get("move_spec_version") != version
            or source.get("move_spec_hash") != spec.move_spec_hash):
        raise ValueError("training input does not match its frozen move table")
    entries = source.get("instances")
    if not isinstance(entries, list) or len(entries) != 424:
        raise ValueError("training input must contain exactly 424 instances")
    expected_ids = {"ms-train-%04d" % i for i in range(1, 425)}
    index = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each training instance must be an object")
        tid = entry.get("training_id")
        if not isinstance(tid, str) or tid not in expected_ids or tid in index:
            raise ValueError("invalid or duplicate training_id: %r" % tid)
        if (entry.get("move_spec_version") != version
                or entry.get("target_relators") != spec.target):
            raise ValueError("training instance has the wrong specification or target: " + tid)
        index[tid] = entry
    return index


def build_examples(manifest, training, stable_training):
    """Build all training problems and a deterministic successful submission."""
    if specs.check_move_specs(manifest["move_specs"]):
        raise ValueError("manifest does not match the frozen move tables")
    ac_entries = _training_index(training, "ac-r2-v1")
    stable_entries = _training_index(stable_training, "sac-r8-v1")
    if ac_entries.keys() != stable_entries.keys():
        raise ValueError("AC and Stable AC training IDs do not match")
    for tid in ac_entries:
        for key in ("generators", "initial_relators"):
            if ac_entries[tid].get(key) != stable_entries[tid].get(key):
                raise ValueError("training pair disagrees on %s: %s" % (key, tid))

    entry = min(ac_entries.values(),
                key=lambda e: (len(e["moves"]), e["training_id"]))
    stable_entry = stable_entries[entry["training_id"]]
    entries = [entry, stable_entry]
    ids = [entry["training_id"], "sac-train-" + entry["training_id"].rsplit("-", 1)[1]]
    official_ids = submission.build_challenge_index(manifest)
    challenges = []
    problems = {"ac.jsonl": [], "stable_ac.jsonl": []}
    for filename, indexed, prefix in (
            ("ac.jsonl", ac_entries, "ms-train-"),
            ("stable_ac.jsonl", stable_entries, "sac-train-")):
        for tid, e in sorted(indexed.items()):
            cid = prefix + tid.rsplit("-", 1)[1]
            if cid in official_ids:
                raise ValueError("training example must not be a scored challenge")
            version = e["move_spec_version"]
            spec_hash = specs.get(version).move_spec_hash
            description = presentation_description(e["generators"], e["initial_relators"], cid)
            challenge = {
                "challenge_id": cid,
                "generators": e["generators"],
                "initial_relators": e["initial_relators"],
                "target_relators": e["target_relators"],
                "move_spec_version": version,
                "scored": False,
                "base_score": 0,
                "instance_hash": canon.instance_hash(
                    cid, e["generators"], e["initial_relators"],
                    e["target_relators"], version, spec_hash),
                "freeze_date": None,
            }
            result = specs.verify_challenge(challenge, e["moves"], version, manifest["limits"])
            if not result.get("ok"):
                raise ValueError("training path failed verification: %s: %r" % (cid, result))
            for key in ("length", "peak_total_relator_length", "work"):
                if result[key] != e[key]:
                    raise ValueError("training instance changed frozen %s: %s" % (key, tid))
            if e["certificate_hash"] != canon.certificate_hash(tid, version, e["moves"]):
                raise ValueError("training source certificate hash mismatch: " + tid)
            if result["certificate_hash"] != canon.certificate_hash(cid, version, e["moves"]):
                raise ValueError("training example certificate hash mismatch: " + cid)
            challenges.append(challenge)
            problems[filename].append({"challenge_id": cid, "description": description})
    training_manifest = {
        "manifest_version": "acms-example-training-v2",
        "competition": manifest["competition"],
        "move_specs": manifest["move_specs"],
        "manifest_hash": canon.manifest_hash([c["instance_hash"] for c in challenges]),
        "freeze_date": None,
        "generators": entry["generators"],
        "limits": manifest["limits"],
        "challenge_count": len(challenges),
        "presentation_count": len(ac_entries),
        "note": "Local training examples only; not part of the scored challenge pool.",
        "challenges": challenges,
    }
    sample_text = (
        "# Successful AC and Stable AC training paths.\n"
        "# Comments can describe your method or acknowledge other work.\n\n"
        + ids[0] + ": " + json.dumps(entry["moves"]) + " # AC: reach (x, y).\n"
        + ids[1] + ": " + json.dumps(stable_entry["moves"])
        + " # Stable AC: reach the empty presentation.\n"
    )
    verdict = submission.process_submission(sample_text.encode(), training_manifest)
    if not verdict.get("accepted") or not all(v.get("ok") for v in verdict["results"]):
        raise ValueError("training examples failed verification: %r" % verdict)
    for e, cid, result in zip(entries, ids, verdict["results"]):
        for key in ("length", "peak_total_relator_length", "work"):
            if result[key] != e[key]:
                raise ValueError("training example changed frozen %s" % key)
        expected_hash = canon.certificate_hash(cid, e["move_spec_version"], e["moves"])
        if result["certificate_hash"] != expected_hash:
            raise ValueError("training example certificate hash mismatch")
    verdict_text = json_text(verdict, sort_keys=True)
    cid = ids[0]

    # Preserve the former default sample as an explicit negative example.
    invalid_text = "ac-00001: [6, 7] # This path returns to its initial state.\n"
    rejected = submission.process_submission(invalid_text.encode(), manifest)
    if (not rejected.get("accepted")
            or rejected["results"][0].get("code") != "E_NOT_TARGET"):
        raise ValueError("negative example no longer produces E_NOT_TARGET")

    readme = """# Training data and submission examples

This folder contains **the same 424 training presentations in AC and Stable AC
versions**. They are **outside the official pool of 10,115 presentations** and
earn no points. Read them in [`ac.jsonl`](ac.jsonl) and
[`stable_ac.jsonl`](stable_ac.jsonl), using the same format as the official
[AC](../problems/ac.jsonl) and [Stable AC](../problems/stable_ac.jsonl) problem files.
Each line contains only `challenge_id` and `description` of the initial
presentation. See [Reading a problem](../rules/discovery.md#reading-a-problem)
for the notation and integer encoding.

| File | Contents |
|---|---|
| [`ac.jsonl`](ac.jsonl) | 424 AC training IDs and presentation descriptions |
| [`stable_ac.jsonl`](stable_ac.jsonl) | The matching 424 Stable AC training IDs and descriptions |
| [`training_424.json`](training_424.json) | Frozen AC training data: integer-encoded words, known move sequences, and statistics |
| [`stable_training_424.json`](stable_training_424.json) | The same training presentations with known Stable AC sequences and statistics |
| [`sample_submission.txt`](sample_submission.txt) | One successful submission covering both problems |
| [`training_manifest.json`](training_manifest.json) | All 848 unscored training challenges, covering both versions of the 424 presentations |
| [`sample_verdict.json`](sample_verdict.json) | Complete expected success receipt |
| [`invalid_submission.txt`](invalid_submission.txt) | A deliberately unsuccessful submission |

Start with `sample_submission.txt`: a complete, successful submission for
the AC and Stable AC problems in [Discovery Track](../rules/discovery.md),
using training instance `%s`. The AC
path uses %d moves from [`training_424.json`](training_424.json);
the Stable AC path appends `[16, 15]` from
[`stable_training_424.json`](stable_training_424.json), reaching
the empty presentation. Both use the [reference verifier](../tools/verifier/README.md)
and official submission format.

This is **local training only and earns no points**. The accompanying
`training_manifest.json` lets you verify any of the 848 training challenges,
all marked `scored: false` with `base_score: 0`, using the official limits
and move specifications. AC training IDs are `ms-train-NNNN`; the matching
Stable AC IDs are `sac-train-NNNN`. The Stable sample ID is `%s`;
both frozen source files use `%s` in their `training_id` field.
The instance and manifest hashes are independently checkable.

The JSONL files list problems. Submit a UTF-8 **TXT file**, with one solution
per line: `challenge_id: [comma-separated moves]`. Blank lines, full-line
`#` comments, and trailing `#` comments are ignored. Use comments for optional
notes; they have no separate length limit beyond the 4 MiB file limit.
A file may contain at most 500 solution lines.

## Run a successful submission

From the development repository root **or the unpacked public package root**
(the directory containing `competition/`), run:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/examples/training_manifest.json \\
  --submission competition/examples/sample_submission.txt --pretty
```

To check your own training submission, replace
`competition/examples/sample_submission.txt` with your TXT file and keep
the same training manifest.

The full input, [`sample_submission.txt`](sample_submission.txt), is:

```text
%s```

Expected output, also saved as [`sample_verdict.json`](sample_verdict.json):

```json
%s```

The command exits with **status 0**. `accepted: true` means the document
passed submission-level checks; each solution must also have `ok: true` to
count as a verified path. Each solution line gives only its challenge ID and
move list. The verifier obtains the move-spec version from the manifest and
computes all result fields itself. Do not upload the verdict as a submission.

You can also check the training manifest's hashes:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/examples/training_manifest.json --check-hashes
```

Do **not** upload this training solution to the scored competition. Training
IDs are absent from `competition/tools/verifier/data/manifest.json`; checking this
same sample against that official manifest returns `E_UNKNOWN_CHALLENGE`
and exit status 1.

## Check a scored submission

Use challenge IDs from [`problems/ac.jsonl`](../problems/ac.jsonl) or
[`problems/stable_ac.jsonl`](../problems/stable_ac.jsonl) and your own move
sequences. Verify `mine.txt` against the official verifier data:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/tools/verifier/data/manifest.json \\
  --submission mine.txt --pretty
```

## Run the deliberately invalid submission

[`invalid_submission.txt`](invalid_submission.txt) preserves the old sample's path:
on scored challenge `ac-00001`, move 6 conjugates the first relator by `x`
and move 7 undoes it. The path returns to its initial state, not the target.

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/tools/verifier/data/manifest.json \\
  --submission competition/examples/invalid_submission.txt --pretty
```

Expected: **exit status 1**, top-level `accepted: true`, and a per-solution
verdict of `ok: false`, `code: "E_NOT_TARGET"`, `final_shape: [9, 18]`.
This checks that a well-formed document with legal moves can still contain
a mathematically unsuccessful path.
""" % (cid, len(entry["moves"]), ids[1], cid, sample_text, verdict_text)
    return {
        "README.md": readme,
        "ac.jsonl": serialize(problems["ac.jsonl"]),
        "stable_ac.jsonl": serialize(problems["stable_ac.jsonl"]),
        "training_manifest.json": json_text(training_manifest),
        "sample_submission.txt": sample_text,
        "sample_verdict.json": verdict_text,
        "invalid_submission.txt": invalid_text,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if any generated example is missing or stale")
    args = parser.parse_args(argv)
    verifier_data = REPO / "competition" / "tools" / "verifier" / "data"
    examples = REPO / "competition" / "examples"
    manifest = json.loads((verifier_data / "manifest.json").read_text(encoding="utf-8"))
    training = json.loads((examples / "training_424.json").read_text(encoding="utf-8"))
    stable_training = json.loads((examples / "stable_training_424.json").read_text(encoding="utf-8"))
    stale = []
    for name, content in build_examples(manifest, training, stable_training).items():
        path = examples / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            examples.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print("wrote %s" % path.relative_to(REPO))
    for name in ("sample_submission.json", "invalid_submission.json"):
        path = examples / name
        if path.exists():
            if args.check:
                stale.append(name + " (obsolete; use .txt)")
            else:
                path.unlink()
                print("removed %s" % path.relative_to(REPO))
    if stale:
        print("stale examples: %s; run python3 build/build_examples.py"
              % ", ".join(stale), file=sys.stderr)
        return 1
    if args.check:
        print("OK: examples match the published training data and official limits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
