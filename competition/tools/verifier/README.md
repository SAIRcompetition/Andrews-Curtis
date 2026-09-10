# Discovery Track reference verifier (`acms_verify`)

The Python reference verifier checks AC and Stable AC solutions using only
standard-library dependencies. See the [Discovery guide](../../rules/discovery.md)
for the competition workflow and scoring. This reference specifies the
numbered moves, replay, limits, and errors.

## Usage

Run the successful training example from the repository or public package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.txt --pretty
```

Expect exit code `0`, `accepted: true`, and `ok: true` for both results.
The [examples guide](../../examples/README.md) contains the input, complete
receipt, and a rejection example. The 424 training presentations are outside
the scored pool; use their training manifest for local checks.

For a scored problem, use the official manifest and your own TXT file:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json \
  --submission submission.txt --pretty
```

Each nonempty, non-comment line is `challenge_id: [move_id, ...]`.
The move list uses JSON array syntax and stays on one line. Spaces around
the ID, colon, and move IDs are optional. The first `#` begins a comment
through the end of the line; blank lines and full-line comments are ignored.
Methods, sources, links, and expected results may appear in comments and do
not affect verification or hashes. Other text must follow the solution
format. See [Submit](../../rules/discovery.md#submit).

The challenge supplies its `move_spec_version`: `ac-` IDs use `ac-r2-v1`
(moves 0–13), and `sac-` IDs use `sac-r8-v1` (moves 0–256). A file may contain
both; duplicate challenge IDs are rejected. Local verification does not
register a competition submission.

## Problem data

[AC](../../problems/ac.jsonl) and [Stable AC](../../problems/stable_ac.jsonl)
list the same 10,115 initial presentations as JSONL records containing only
`challenge_id` and `description`. See
[Reading a problem](../../problems/README.md#reading-a-problem) for the
notation and integer encoding. The verifier reads exact words, targets,
move specifications, and limits from [manifest.json](data/manifest.json).
The [data guide](data/README.md) covers the schema and provenance;
its [hash specification](data/README.md#hash-specification) defines hash bytes.

## AC moves

A challenge gives you an ordered pair of freely reduced words
`initial_relators = [r0, r1]` over letters `1 = x, -1 = x^-1, 2 = y,
-2 = y^-1`. Transform it into the **exact ordered target**
$T = (x, y) =$ `[[1],[2]]` using the 14 numbered operations of
`move_spec_version = "ac-r2-v1"`:

| id | Effect | Inverse | id | Effect | Inverse |
|---:|---|---:|---:|---|---:|
| 0 | $r_0 \leftarrow r_0^{-1}$ | 0 | 7 | $r_0 \leftarrow x^{-1} r_0 x$ | 6 |
| 1 | $r_1 \leftarrow r_1^{-1}$ | 1 | 8 | $r_0 \leftarrow y r_0 y^{-1}$ | 9 |
| 2 | $r_0 \leftarrow r_0 r_1$ | 3 | 9 | $r_0 \leftarrow y^{-1} r_0 y$ | 8 |
| 3 | $r_0 \leftarrow r_0 r_1^{-1}$ | 2 | 10 | $r_1 \leftarrow x r_1 x^{-1}$ | 11 |
| 4 | $r_1 \leftarrow r_1 r_0$ | 5 | 11 | $r_1 \leftarrow x^{-1} r_1 x$ | 10 |
| 5 | $r_1 \leftarrow r_1 r_0^{-1}$ | 4 | 12 | $r_1 \leftarrow y r_1 y^{-1}$ | 13 |
| 6 | $r_0 \leftarrow x r_0 x^{-1}$ | 7 | 13 | $r_1 \leftarrow y^{-1} r_1 y$ | 12 |

These IDs encode 2 inversions, 4 right multiplications by the other relator
or its inverse, and 8 conjugations by a generator letter or its inverse.
They instantiate the three ordinary AC operation types at rank 2.

Words are freely reduced after every move by a single left-fold: scan
left to right, canceling a letter against the top of the output stack
when they are inverse. The move set is closed under inversion, so
reachability is symmetric.

**The endpoint must be exactly `[[1],[2]]`, in order.** A signed permutation
of `(x,y)` takes at most **5** further moves to reach it. The exhaustively verified
shortest suffixes are also published as `canonicalization_table` in
[move_spec.json](data/move_spec.json):

| Final state | Moves to $T$ | One shortest path (move ids) |
|---|---:|---|
| $(x,y)$ | 0 | — |
| $(x,y^{-1})$ | 1 | `[1]` |
| $(x^{-1},y)$ | 1 | `[0]` |
| $(x^{-1},y^{-1})$ | 2 | `[0,1]` |
| $(y^{-1},x)$ | 4 | `[2,5,2,8]` |
| $(y,x^{-1})$ | 4 | `[3,4,3,10]` |
| $(y^{-1},x^{-1})$ | 4 | `[2,0,4,3]` |
| $(y,x)$ | 5 | `[0,2,5,2,8]` |

Append the matching suffix and verify the complete path against the
[limits](#limits); the suffix counts toward path length and work.

## Stable AC moves

A state is an ordered list of $k$ freely reduced relators over letters
$\pm1,\ldots,\pm k$, where $0\le k\le8$. Each challenge starts at
rank 2; the target is the **empty presentation** `[]`.

| Move IDs | Operation |
|---|---|
| 0–13 | The original AC block, with unchanged meanings |
| 14 | Stabilize: append generator $k+1$ and relator `[k+1]` |
| 15–22 | Destabilize relator $i=0,\ldots,7$ |
| 23–28 | Invert relator $i=2,\ldots,7$ |
| 29–136 | Remaining right multiplications by another relator or its inverse |
| 137–256 | Remaining conjugations by a generator letter or its inverse |

All 257 rows are in [stable_move_spec.json](data/stable_move_spec.json).
The operation IDs cover ranks up to 8: 8 inversions, 112 right multiplications, 128 generator-letter
conjugations, 1 stabilization, and 8 destabilizations. Applicability depends
on the current state. A move may name only existing relators and generators.
Stabilization requires $k<8$. Destabilization requires the selected relator
to be exactly a single positive generator $g$, absent from every other
relator. It deletes that relator and generator, then renumbers generators
above $g$ down by one, preserving the order of the remaining relators.

The rank cap is frozen in `sac-r8-v1`. It restricts this search benchmark
and does not change the full stable conjecture. From a signed permutation
of the $k$ generators, invert negative relators and then destabilize from
the highest relator index down; the shortest finish has $k$ plus the number of negative
relators moves. From either `(x,y)` or `(y,x)`, the suffix is `[16,15]`.

An AC solution followed by `[16,15]` reaches the stable target. It is
accepted for the Stable AC problem only if the extended path also satisfies
its limits: the suffix adds two moves and one unit of work. Submit it
under the corresponding `sac-` ID; points do not transfer between problems.

## Replay and receipts

Deterministic, pure integer arithmetic. The parser reads each TXT solution
line into a challenge ID and move list. Against limits
`{max_path_length, max_total_relator_length, max_work}`, the server
looks up the official challenge by id and uses its `move_spec_version`
for replay and certificate hashing. Comments do not enter replay or the
certificate hash; the verifier computes every result itself.

```
assert len(moves) <= max_path_length       else E_PATH_TOO_LONG
s    = challenge.initial_relators          # freely reduced, from the manifest
work = sum(len(r) for r in s)              # the initial state counts toward work
for k, m in enumerate(moves):
    assert m is an integer in the spec     else E_BAD_MOVE_ID(move_index=k)
    assert m is applicable to s            else E_MOVE_NOT_APPLICABLE(move_index=k)
    s = free_reduce(apply(s, m))
    tot = sum(len(r) for r in s)
    assert tot <= max_total_relator_length else E_LENGTH_LIMIT(move_index=k)
    work += tot
    assert work <= max_work                else E_WORK_BUDGET(move_index=k)
assert s == challenge.target_relators      else E_NOT_TARGET(final_shape=[len(r) for r in s])
return { ok, length = len(moves), work, certificate_hash }
```

The move-ID range is 0–13 for AC and 0–256 for Stable AC. Every AC move
is applicable at rank 2; Stable AC additionally checks the conditions in
[Stable AC moves](#stable-ac-moves).

Move IDs must be integers: `1.0` is a float and is **not** a valid move ID;
`true`/`false` are booleans, not integers; `"3"` is a string. All are
rejected with `E_BAD_MOVE_ID` at their index.

The submission receipt's top-level `accepted` means that the document
passed structural checks. It does **not** mean that any challenge was
solved. Only a solution with `results[i].ok: true` is verified and may
enter scoring. A mixed submission keeps its successful solutions even
when others fail; a structurally accepted document can contain no
successful solutions.

## Limits

The same path limits apply to both Discovery problems. Upload quotas and
batch/body limits are shared per team across the entire Discovery Track.
A batch may mix `ac-` and `sac-` IDs; they are distinct challenges.

| Limit | v1 value |
|---|---:|
| Discovery submissions per team per UTC day (site + API combined) | 100 |
| Solution lines per submission | 500 |
| Raw TXT file size, including comments | 4 MiB (4,194,304 bytes) |
| `max_path_length` | 100 000 |
| `max_total_relator_length` | 10 000 |
| `max_work` = Σ per-step total relator length | 5 000 000 |

Path limits come from the manifest; structural limits have published
defaults in the reference parser and are supplied by the platform's
frozen configuration. Comments have no separate character limit and do
not count as solutions. A structurally accepted upload counts once toward
the daily quota, even if all its solutions fail verification. Structural
rejections do not count. Local self-checks do not consume platform quota.

## Errors

Whole-submission rejections (structural; do **not** count against the
daily quota):

| Code | Trigger |
|---|---|
| `E_MALFORMED` | file too large, invalid UTF-8, malformed solution line or move list, no solutions, or too many solutions; `detail` identifies the cause and line errors include `line_number` |
| `E_DUPLICATE_CHALLENGE` | same `challenge_id` twice in one submission |

Per-solution rejections (other solutions in the same submission are
processed normally):

| Code | Trigger |
|---|---|
| `E_UNKNOWN_CHALLENGE` | `challenge_id` not in the manifest |
| `E_PATH_TOO_LONG` | more than `max_path_length` moves |
| `E_BAD_MOVE_ID` | non-integer or move outside the challenge specification (carries `move_index`) |
| `E_MOVE_NOT_APPLICABLE` | Stable AC: unavailable relator/generator, stabilization at rank 8, or failed destabilization condition (carries `move_index`, `move`, and `reason`) |
| `E_LENGTH_LIMIT` | intermediate total relator length exceeds the limit (carries `move_index`) |
| `E_WORK_BUDGET` | cumulative work exceeds `max_work` (carries `move_index`) |
| `E_NOT_TARGET` | every move legal but endpoint differs from the challenge target: `[[1],[2]]` for AC or `[]` for Stable AC (carries `final_shape`) |

**Check priority:** file byte limit → UTF-8 decoding → solution-line parsing
(ignoring comments and blank lines) → solutions count →
duplicates → then per solution: challenge lookup → path length → per-move
id → applicability → relator length → work budget → target. The first
triggered check is the one reported.

`E_MOVE_NOT_APPLICABLE.reason` is `relator_out_of_rank`,
`generator_out_of_rank`, `max_rank_exceeded`, or `destabilize_precondition`.

## Optional checks

Run from the repository or public package root:

```sh
# Run the published conformance vectors.
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --golden competition/tools/verifier/data/golden_vectors.json

# Recompute and check the manifest's hashes.
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/tools/verifier/data/manifest.json --check-hashes
```

| Exit code | Meaning |
|---:|---|
| 0 | All solutions verified successfully |
| 1 | Structurally accepted submission with at least one rejected solution |
| 2 | Whole-submission rejection or failing conformance/hash checks |
| 3 | Usage or input/output error |

The development repository also provides `python3 -m unittest discover -s tests -t .`
for replay, parsing, limits, errors, hashes, and all 424 training paths under
each specification.

## Layout

| Module | Contents |
|---|---|
| `acms_verify/core.py` | AC move table, free reduction, replay |
| `acms_verify/stable_core.py` | Stable AC move table and variable-rank replay |
| `acms_verify/specs.py` | Specification dispatch and move-table validation |
| `acms_verify/canon.py` | Canonical serialization and hashing |
| `acms_verify/submission.py` | TXT parsing, comments, structural checks, receipts |
| `acms_verify/golden.py` | Conformance-vector runner |
| `acms_verify/cli.py` | Command-line interface |
