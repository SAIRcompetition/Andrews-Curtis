# Runnable Discovery submission examples

Start with `sample_submission.json`: a complete, successful submission for
the published training instance `ms-train-0160`, copied from
[`training_424.json`](../challenges/training_424.json). It uses 7 atomic
moves and the same verifier and JSON submission format as Discovery Track.

This is **local training only and earns no points**. The accompanying
`training_manifest.json` contains just this training instance, marked
`scored: false` with `base_score: 0`; its limits and move specification match
the official manifest. Its instance and manifest hashes are independently
checkable. It is not a new official challenge pool or freeze.

## Run a successful submission

From the development repository root **or the unpacked public package root**
(the directory containing `competition/`), run:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

The full input, [`sample_submission.json`](sample_submission.json), is:

```json
{
  "solutions": [
    {
      "challenge_id": "ms-train-0160",
      "moves": [
        6,
        4,
        2,
        9,
        1,
        4,
        1
      ]
    }
  ]
}
```

Expected output, also saved as [`sample_verdict.json`](sample_verdict.json):

```json
{
  "accepted": true,
  "results": [
    {
      "certificate_hash": "sha256:80dedf02b91d429b017fb0b3f48e950a9fc5e18363dbdf21c6e27297100c471f",
      "challenge_id": "ms-train-0160",
      "length": 7,
      "ok": true,
      "peak_total_relator_length": 12,
      "work": 46
    }
  ]
}
```

The command exits with **status 0**. `accepted: true` means the document
passed submission-level checks; each solution must also have `ok: true` to
count as a verified path. Only `challenge_id` and `moves` belong in each
solution. The verifier obtains the move-spec version from the manifest and
computes all result fields itself. Do not upload the verdict as a submission.

You can also check the training manifest's hashes:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
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
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/challenges/manifest.json \
  --submission competition/examples/invalid_submission.json --pretty
```

Expected: **exit status 1**, top-level `accepted: true`, and a per-solution
verdict of `ok: false`, `code: "E_NOT_TARGET"`, `final_shape: [9, 18]`.
This checks that a well-formed document with legal moves can still contain
a mathematically unsuccessful path.
