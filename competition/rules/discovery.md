# Discovery Track

**Submissions open:** September 11, 2026 at 16:00 UTC.

**Deadline:** November 30, 2026, end of day [AoE](https://www.ieee802.org/16/aoe.html)
(Anywhere on Earth, UTC−12).

## Problems

Find short move sequences that simplify the same **10,115 presentations**
in two independently scored problems:

| Problem file | IDs | Required endpoint |
|---|---|---|
| [AC](../problems/ac.jsonl) | `ac-00001`–`ac-10115` | Exactly `(x, y)`, in order |
| [Stable AC](../problems/stable_ac.jsonl) | `sac-00001`–`sac-10115` | The empty presentation; at most 8 generators at any step |

The [424 training presentations](../examples/README.md) have known solutions
for both problems. They are outside the scored pool and earn no points.

### Reading a problem

Each JSONL line has a `challenge_id` for submissions and a `description`
of the starting presentation. For example, `<x, y | x y = 1; y = 1>` has
ordered generators `x, y` and ordered relators `x y`, then `y`.
Spaces mean multiplication; `x^-1` means the inverse of `x`; `1` means
the identity. Moves transform the relator words, canceling adjacent
inverse letters, such as `x y y^-1` becoming `x`.
[More on notation and integer encoding](../problems/README.md#reading-a-problem).

## Moves

- **AC — IDs 0–13:** invert a relator, multiply it on the right by the other
  relator or its inverse, or conjugate it by a generator or its inverse.
  [Exact move table](../tools/verifier/README.md#ac-moves).
- **Stable AC — IDs 0–256:** the same operations on the current generators
  and relators, plus adding or removing a generator–relator pair. Removal
  requires a relator consisting of one positive generator, absent from all
  other relators. [Exact move table and conditions](../tools/verifier/README.md#stable-ac-moves).

## Submit

Create a UTF-8 `submission.txt`, with one `challenge_id: [moves]` per line.
Move IDs are comma-separated integers. A file may mix AC and Stable AC;
each challenge ID appears once. Use `#` for comments on their own line
or after a solution; comments and blank lines are ignored.

### Quick test

First, try the included [training submission](../examples/sample_submission.txt):

```text
ms-train-0160: [6, 4, 2, 9, 1, 4, 1] # AC training solution
sac-train-0160: [6, 4, 2, 9, 1, 4, 1, 16, 15] # Stable AC training solution
```

From the repository root, run with Python 3:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.txt --pretty
```

Expect exit code **0**, `accepted: true`, and `ok: true` for both solutions.
[Full receipt](../examples/sample_verdict.json).

For your own solutions, use official `ac-` / `sac-` problem IDs and check
against the official manifest:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission submission.txt --pretty
```

Only results with `ok: true` are verified. A failed path does not invalidate
other solutions; a format error rejects the whole file.
[Verifier errors](../tools/verifier/README.md#errors).

### Upload

Upload your file through [SAIR](https://competition.sair.foundation/competitions/acc).
Local checks do not register a submission. Limits are **40 submissions per
team per UTC day**, **500 solutions per file**, **10 MB per file**
(10,000,000 bytes, including comments), and **100,000 moves per solution**.
See [verification limits](../tools/verifier/README.md#limits)
for the verifier's resource limits.

Submissions must arrive complete at or after opening and before the deadline;
verification may finish later. See the [overview](overview.md) for
registration and team rules.

## Scoring

On each challenge, the $k$ teams tied for the shortest verified solution
**each earn $2^{1-k}$ points**; all others earn 0. One team earns 1 point,
two tied teams earn ½ each, and three earn ¼ each. Each team counts once.

A shorter verified solution replaces the previous record, and points are
recalculated. Team totals are summed across challenges, with **separate
AC and Stable AC leaderboards**.
