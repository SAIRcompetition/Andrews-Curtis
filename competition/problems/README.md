# Discovery Track problems

| File | Contents | Target |
|---|---|---|
| [ac.jsonl](ac.jsonl) | 10,115 AC problems | The ordered relators `(x, y)`, with the two generators fixed |
| [stable_ac.jsonl](stable_ac.jsonl) | 10,115 Stable AC problems | The empty presentation, using at most 8 generators |

Both files use the same 10,115 initial presentations. Matching ID suffixes
identify the same initial presentation: `ac-00001` and `sac-00001`, for
example. Each problem is scored separately. The 424 training presentations
are outside these files; they and the submission examples are in
[examples/](../examples/README.md).

## File format

Each file uses **JSON Lines**: one JSON object per line, with no enclosing
array. Every object has exactly two fields:

- `challenge_id`: the ID to use in your submission.
- `description`: the initial group presentation.

The shared targets and move rules are specified in the
[Discovery rules](../rules/discovery.md#problems).

See [Reading a problem](#reading-a-problem) for the
presentation notation, letter encoding, and a worked example.
The [424 training problems](../examples/README.md) use the same format.

Read a problem file with Python's standard library, from the repository
or unpacked public package root:

```python
import json

with open("competition/problems/ac.jsonl", encoding="utf-8") as source:
    problems = [json.loads(line) for line in source]
print(problems[0])
```

## Reading a problem

`Presentation: <x, y | u = 1; v = 1>.` specifies generators `x, y`
and two ordered relators: `r0 = u`, then `r1 = v`. The semicolon separates
the relations; `1` on the right is the group identity. Only the words on
the left are encoded as relators.

Read words as products in the written order. Spaces mean multiplication,
`x^-1` and `y^-1` mean inverses, and `x x x` means three copies of `x`.
Moves act in the free group: factor order matters, and free reduction
only cancels adjacent inverse letters, as in `x y y^-1` becoming `x`.
The defining relations are not extra simplification operations.

The verifier and reference training solutions encode letters as integers:

| Letter | Integer |
|---|---:|
| `x` | `1` |
| `x^-1` | `-1` |
| `y` | `2` |
| `y^-1` | `-2` |

The identity word is `[]`; `[1]` is the word `x`. These letter codes are
distinct from the operation IDs in a submitted move list.

For example, `<x, y | x y = 1; y = 1>` has
`initial_relators = [[1, 2], [2]]`. This is an illustration, not a scored
problem. AC move `3` multiplies the first relator by the inverse of the
second: `(x y, y)` becomes the target `(x, y)`, so its solution is `[3]`.
For Stable AC, `[3, 16, 15]` gives
`(x y, y) → (x, y) → (x) → ()`, reaching the empty presentation.

Use the problem's exact `challenge_id` and your operation IDs in the
[TXT submission format](../rules/discovery.md#submit). Problem files are JSONL;
submissions are TXT. The [examples guide](../examples/README.md) has a
complete successful submission and its verifier receipt.

## Local verification

The verifier reads the same presentations in integer form from
[`tools/verifier/data/manifest.json`](../tools/verifier/data/manifest.json),
along with their targets and limits. The two problem files are generated
from that manifest, and release checks require them to agree exactly.
From the repository or unpacked public package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission submission.txt --pretty
```

Use the IDs in these problem files and replace `submission.txt` with your own
submission. Local verification does not register a submission on SAIR.
