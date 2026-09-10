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
[Discovery rules](../rules/discovery.md#1-problems-and-move-specifications).

See [Reading a problem](../rules/discovery.md#reading-a-problem) for the
presentation notation, letter encoding, and a worked example.
The [424 training problems](../examples/README.md) use the same notation
and JSONL format.

Read a problem file with Python's standard library, from the repository
or unpacked public package root:

```python
import json

with open("competition/problems/ac.jsonl", encoding="utf-8") as source:
    problems = [json.loads(line) for line in source]
print(problems[0])
```

Submit only the challenge ID and your list of numbered moves. See the
[Discovery rules](../rules/discovery.md) for move definitions, limits, and
scoring, and the [examples guide](../examples/README.md) for a complete
successful submission and its verifier receipt.

## Local verification

The verifier reads the same presentations in integer form from
[`tools/verifier/data/manifest.json`](../tools/verifier/data/manifest.json),
along with their targets and limits. The two problem files are generated
from that manifest, and release checks require them to agree exactly.
From the repository or unpacked public package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission mine.json --pretty
```

Use the IDs in these problem files and replace `mine.json` with your own
submission. Local verification does not register a submission on SAIR.
