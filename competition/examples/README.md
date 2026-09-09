# Training data and submission examples

This folder contains **the same 424 training presentations in AC and Stable AC
versions**. They are **outside the official pool of 10,115 presentations** and
earn no points. The scored problem statements are in
[`problems/ac.json`](../problems/ac.json) and
[`problems/stable_ac.json`](../problems/stable_ac.json).

| File | Contents |
|---|---|
| [`training_424.json`](training_424.json) | 424 training presentations with AC move sequences |
| [`stable_training_424.json`](stable_training_424.json) | The same 424 presentations with Stable AC move sequences |
| [`sample_submission.json`](sample_submission.json) | One successful submission covering both problems |
| [`training_manifest.json`](training_manifest.json) | Unscored verifier input for that submission |
| [`sample_verdict.json`](sample_verdict.json) | Complete expected success receipt |
| [`invalid_submission.json`](invalid_submission.json) | A deliberately unsuccessful submission |

Start with `sample_submission.json`: a complete, successful submission for
the AC and Stable AC problems in Discovery Track, using training instance `ms-train-0160`. The AC
path uses 7 moves from [`training_424.json`](training_424.json);
the Stable AC path appends `[16, 15]` from
[`stable_training_424.json`](stable_training_424.json), reaching
the empty presentation. Both use the official verifier and JSON format.

This is **local training only and earns no points**. The accompanying
`training_manifest.json` contains the AC and Stable AC versions of this instance, each
marked `scored: false` with `base_score: 0`; its limits and move specifications
match the official manifest. The Stable example ID is `sac-train-0160`;
training files share `ms-train-0160`, so the example gives each problem a
distinct ID for mixed submissions. Its instance and manifest hashes are independently
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
    },
    {
      "challenge_id": "sac-train-0160",
      "moves": [
        6,
        4,
        2,
        9,
        1,
        4,
        1,
        16,
        15
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
    },
    {
      "certificate_hash": "sha256:e94492471688db5cb52971611a3617e75c165d89e3ed51cea9a3f5d96ccbb77e",
      "challenge_id": "sac-train-0160",
      "length": 9,
      "ok": true,
      "peak_total_relator_length": 12,
      "work": 47
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
IDs are absent from `competition/tools/verifier/data/manifest.json`; checking this
same sample against that official manifest returns `E_UNKNOWN_CHALLENGE`
and exit status 1.

## Check a scored submission

Use challenge IDs from [`problems/ac.json`](../problems/ac.json) or
[`problems/stable_ac.json`](../problems/stable_ac.json) and your own move
sequences. Verify `mine.json` against the official verifier data:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission mine.json --pretty
```

## Run the deliberately invalid submission

[`invalid_submission.json`](invalid_submission.json) preserves the old sample:
on scored challenge `ac-v1-00001`, move 6 conjugates the first relator by `x`
and move 7 undoes it. The path returns to its initial state, not the target.

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission competition/examples/invalid_submission.json --pretty
```

Expected: **exit status 1**, top-level `accepted: true`, and a per-solution
verdict of `ok: false`, `code: "E_NOT_TARGET"`, `final_shape: [9, 18]`.
This checks that a well-formed document with legal moves can still contain
a mathematically unsuccessful path.
