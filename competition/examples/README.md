# Training data and submission examples

This folder contains **the same 424 training presentations in AC and Stable AC
versions**. They are **outside the official pool of 10,115 presentations** and
earn no points. Read them in [`ac.jsonl`](ac.jsonl) and
[`stable_ac.jsonl`](stable_ac.jsonl), using the same format as the official
[AC](../problems/ac.jsonl) and [Stable AC](../problems/stable_ac.jsonl) problem files.
Each line contains only `challenge_id` and `description` of the initial
presentation. See [Reading a problem](../problems/README.md#reading-a-problem)
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
using training instance `ms-train-0160`. The AC
path uses 7 moves from [`training_424.json`](training_424.json);
the Stable AC path appends `[16, 15]` from
[`stable_training_424.json`](stable_training_424.json), reaching
the empty presentation. Both use the [reference verifier](../tools/verifier/README.md)
and official submission format.

This is **local training only and earns no points**. The accompanying
`training_manifest.json` lets you verify any of the 848 training challenges,
all marked `scored: false` with `base_score: 0`, using the official limits
and move specifications. AC training IDs are `ms-train-NNNN`; the matching
Stable AC IDs are `sac-train-NNNN`. The Stable sample ID is `sac-train-0160`;
both frozen source files use `ms-train-0160` in their `training_id` field.
The instance and manifest hashes are independently checkable.

The JSONL files list problems. Submit a UTF-8 **TXT file**, with one solution
per line: `challenge_id: [comma-separated moves]`. Blank lines, full-line
`#` comments, and trailing `#` comments are ignored. Use comments for optional
notes; they have no separate length limit. The whole file, including comments,
must be at most 10 MB (10,000,000 bytes), with at most 500 solution lines.

## Run a successful submission

From the development repository root **or the unpacked public package root**
(the directory containing `competition/`), run:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.txt --pretty
```

To check your own training submission, replace
`competition/examples/sample_submission.txt` with your TXT file and keep
the same training manifest.

The full input, [`sample_submission.txt`](sample_submission.txt), is:

```text
# Successful AC and Stable AC training paths.
# Comments can describe your method or acknowledge other work.

ms-train-0160: [6, 4, 2, 9, 1, 4, 1] # AC: reach (x, y).
sac-train-0160: [6, 4, 2, 9, 1, 4, 1, 16, 15] # Stable AC: reach the empty presentation.
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
      "work": 46
    },
    {
      "certificate_hash": "sha256:e94492471688db5cb52971611a3617e75c165d89e3ed51cea9a3f5d96ccbb77e",
      "challenge_id": "sac-train-0160",
      "length": 9,
      "ok": true,
      "work": 47
    }
  ]
}
```

The command exits with **status 0**. `accepted: true` means the document
passed submission-level checks; each solution must also have `ok: true` to
count as a verified path. Each solution line gives only its challenge ID and
move list. The verifier obtains the move-spec version from the manifest and
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

Use challenge IDs from [`problems/ac.jsonl`](../problems/ac.jsonl) or
[`problems/stable_ac.jsonl`](../problems/stable_ac.jsonl) and your own move
sequences. Verify `mine.txt` against the official verifier data:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission mine.txt --pretty
```

## Run the deliberately invalid submission

[`invalid_submission.txt`](invalid_submission.txt) preserves the old sample's path:
on scored challenge `ac-00001`, move 6 conjugates the first relator by `x`
and move 7 undoes it. The path returns to its initial state, not the target.

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission competition/examples/invalid_submission.txt --pretty
```

Expected: **exit status 1**, top-level `accepted: true`, and a per-solution
verdict of `ok: false`, `code: "E_NOT_TARGET"`, `final_shape: [9, 18]`.
This checks that a well-formed document with legal moves can still contain
a mathematically unsuccessful path.
