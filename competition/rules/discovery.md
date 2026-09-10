# Discovery Track

## Quick start

Try the included [training submission](../examples/sample_submission.txt):

```text
# Known training solutions
ms-train-0160: [6, 4, 2, 9, 1, 4, 1] # AC
sac-train-0160: [6, 4, 2, 9, 1, 4, 1, 16, 15] # Stable AC
```

From the repository root, run with Python 3:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.txt --pretty
```

Expected: exit code **0**, `accepted: true`, and `ok: true` for both
solutions. See the [full receipt](../examples/sample_verdict.json).

## Problems

Find short move sequences that simplify the same **10,115 presentations**
in two independently scored problems:

| Problem file | IDs | Required endpoint |
|---|---|---|
| [AC](../problems/ac.jsonl) | `ac-00001`–`ac-10115` | Exactly `(x, y)`, in order |
| [Stable AC](../problems/stable_ac.jsonl) | `sac-00001`–`sac-10115` | The empty presentation; at most 8 generators at any step |

Each JSONL line contains `challenge_id` and `description`. In
`<x, y | u = 1; v = 1>`, `u` and `v` are the ordered relators;
spaces mean multiplication, and `x^-1` means the inverse of `x`.
See [how to read a problem](../problems/README.md#reading-a-problem)
for the notation and integer encoding.

The [424 training presentations](../examples/README.md) have known solutions
for both problems. They are outside the scored pool and earn no points.

## Moves

- **AC — IDs 0–13:** invert a relator, multiply it on the right by the other
  relator or its inverse, or conjugate it by a generator or its inverse.
  [Exact move table](../tools/verifier/README.md#ac-moves).
- **Stable AC — IDs 0–256:** the same operations on the current generators
  and relators, plus adding or removing a generator–relator pair. Removal
  requires a relator consisting of one positive generator, absent from all
  other relators. [Exact move table and conditions](../tools/verifier/README.md#stable-ac-moves).

Cancel adjacent inverse letters after each move. Words must reach the
specified endpoint exactly.

## Submit

Create a UTF-8 `submission.txt`, with one `challenge_id: [moves]` per line,
using IDs from the official problem files. Move IDs are comma-separated
integers. A file may mix AC and Stable AC; each challenge ID appears once.

Use `#` for notes on their own line or after a solution. Blank lines and
comments are ignored.

Check your file locally:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission submission.txt --pretty
```

Only results with `ok: true` are verified. A failed path does not invalidate
other solutions; a format error rejects the whole file.
[Verifier errors and limits](../tools/verifier/README.md#errors).

Upload the file through [SAIR](https://competition.sair.foundation/competitions/acc).
Local checks do not register a submission. Limits are **100 submissions per
team per UTC day**, **500 solutions per file**, and **4 MiB per file**,
including comments. Paths must also satisfy the
[search limits](../tools/verifier/README.md#limits).
See the [overview](overview.md) for dates, registration, and team rules.
Submissions must arrive complete at or after opening and before the deadline;
verification may finish later.

## Scoring

On each challenge, the $k$ teams tied for the shortest verified solution
**each earn $2^{1-k}$ points**; all others earn 0. One team earns 1 point,
two tied teams earn ½ each, and three earn ¼ each. Each team counts once.

A shorter verified solution replaces the previous record, and points are
recalculated. Team totals are summed across challenges, with **separate
AC and Stable AC leaderboards**.

Rank by exact total score. Ties go to the team that last reached its current
total earlier, then by team ID. Priority uses server receipt times for
complete submissions.

**First Solver** recognizes the earliest submitted verified solution for
each challenge, regardless of length. A later, shorter solution does not
take away this record.
