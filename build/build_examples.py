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
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import canon, core, submission  # noqa: E402


def json_text(value, *, sort_keys=False):
    return json.dumps(value, indent=2, sort_keys=sort_keys) + "\n"


def build_examples(manifest, training):
    """Return ``{filename: text}`` for the deterministic example bundle."""
    spec_hash = canon.move_spec_hash(core.MOVE_TABLE)
    if not (manifest["move_spec_hash"] == training["move_spec_hash"] == spec_hash):
        raise ValueError("example inputs do not match the frozen move table")
    entry = min(training["instances"],
                key=lambda e: (len(e["moves"]), e["training_id"]))
    cid = entry["training_id"]
    if cid in submission.build_challenge_index(manifest):
        raise ValueError("training example must not be a scored challenge")
    challenge = {
        "challenge_id": cid,
        "generators": entry["generators"],
        "initial_relators": entry["initial_relators"],
        "target_relators": entry["target_relators"],
        "move_spec_version": entry["move_spec_version"],
        "scored": False,
        "base_score": 0,
        "instance_hash": canon.instance_hash(
            cid, entry["generators"], entry["initial_relators"],
            entry["target_relators"], entry["move_spec_version"], spec_hash),
        "freeze_date": None,
    }
    training_manifest = {
        "manifest_version": "acms-example-training-v1",
        "competition": manifest["competition"],
        "move_spec_version": entry["move_spec_version"],
        "move_spec_hash": spec_hash,
        "manifest_hash": canon.manifest_hash([challenge["instance_hash"]]),
        "freeze_date": None,
        "generators": entry["generators"],
        "target_relators": entry["target_relators"],
        "limits": manifest["limits"],
        "challenge_count": 1,
        "note": "Local training example only; not part of the scored challenge pool.",
        "challenges": [challenge],
    }
    sample = {"solutions": [{"challenge_id": cid, "moves": entry["moves"]}]}
    sample_text = json_text(sample)
    verdict = submission.process_submission(sample_text.encode(), training_manifest)
    if not verdict.get("accepted") or not verdict["results"][0].get("ok"):
        raise ValueError("training example failed verification: %r" % verdict)
    for key in ("length", "peak_total_relator_length", "work", "certificate_hash"):
        if verdict["results"][0][key] != entry[key]:
            raise ValueError("training example changed frozen %s" % key)
    verdict_text = json_text(verdict, sort_keys=True)

    # Preserve the former default sample as an explicit negative example.
    invalid = {"solutions": [{"challenge_id": "ac-v1-00001", "moves": [6, 7]}]}
    invalid_text = json_text(invalid)
    rejected = submission.process_submission(invalid_text.encode(), manifest)
    if (not rejected.get("accepted")
            or rejected["results"][0].get("code") != "E_NOT_TARGET"):
        raise ValueError("negative example no longer produces E_NOT_TARGET")

    readme = """# Runnable submission examples

Start with `sample_submission.json`: a complete, successful submission for
the published training instance `%s`, copied from
[`training_424.json`](../challenges/training_424.json). It uses %d atomic
moves and the same verifier and JSON submission format as the scored track.

This is **local training only and earns no points**. The accompanying
`training_manifest.json` contains just this training instance, marked
`scored: false` with `base_score: 0`; its limits and move specification match
the official manifest. Its instance and manifest hashes are independently
checkable. It is not a new official challenge pool or freeze.

## Run a successful submission

From the development repository root **or the unpacked public package root**
(the directory containing `competition/`), run:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/examples/training_manifest.json \\
  --submission competition/examples/sample_submission.json --pretty
```

The full input, [`sample_submission.json`](sample_submission.json), is:

```json
%s```

Expected output, also saved as [`sample_verdict.json`](sample_verdict.json):

```json
%s```

The command exits with **status 0**. `accepted: true` means the document
passed submission-level checks; each solution must also have `ok: true` to
count as a verified path. Only `challenge_id` and `moves` belong in each
solution. The verifier obtains the move-spec version from the manifest and
computes all result fields itself. Do not upload the verdict as a submission.

You can also check the training manifest's hashes:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/examples/training_manifest.json --check-hashes
```

Do **not** upload this training solution to the scored competition. Training
IDs are absent from `competition/challenges/manifest.json`; checking this
same sample against that official manifest returns `E_UNKNOWN_CHALLENGE`
and exit status 1. For your scored entries, use IDs from the official manifest
and verify your own submission against it.

## Run the deliberately invalid submission

[`invalid_submission.json`](invalid_submission.json) preserves the old sample:
on scored challenge `ac-v1-00001`, move 6 conjugates the first relator by `x`
and move 7 undoes it. The path returns to its initial state, not the target.

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \\
  --manifest competition/challenges/manifest.json \\
  --submission competition/examples/invalid_submission.json --pretty
```

Expected: **exit status 1**, top-level `accepted: true`, and a per-solution
verdict of `ok: false`, `code: "E_NOT_TARGET"`, `final_shape: [9, 18]`.
This checks that a well-formed document with legal moves can still contain
a mathematically unsuccessful path.
""" % (cid, len(entry["moves"]), sample_text, verdict_text)
    return {
        "README.md": readme,
        "training_manifest.json": json_text(training_manifest),
        "sample_submission.json": sample_text,
        "sample_verdict.json": verdict_text,
        "invalid_submission.json": invalid_text,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if any generated example is missing or stale")
    args = parser.parse_args(argv)
    challenges = REPO / "competition" / "challenges"
    manifest = json.loads((challenges / "manifest.json").read_text(encoding="utf-8"))
    training = json.loads((challenges / "training_424.json").read_text(encoding="utf-8"))
    examples = REPO / "competition" / "examples"
    stale = []
    for name, content in build_examples(manifest, training).items():
        path = examples / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            examples.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print("wrote %s" % path.relative_to(REPO))
    if stale:
        print("stale examples: %s; run python3 build/build_examples.py"
              % ", ".join(stale), file=sys.stderr)
        return 1
    if args.check:
        print("OK: examples match the published training data and official limits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
