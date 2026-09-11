# Discovery Track verifier data (`acms-v3`) — prelaunch preview

**The official data freeze is not yet set.** This preview contains
20,230 challenges: the same **10,115 presentations** in the AC and Stable AC
problems within Discovery Track. The status is `prelaunch`; Discovery opens at
16:00 UTC on September 11, 2026. See the
[Discovery rules](../../../rules/discovery.md) for the schedule and submission window.

Before public launch, the organizers will freeze `manifest.json`,
`move_spec.json`, and `stable_move_spec.json` in git and publish the commit.
`freeze_date` is outside `instance_hash`, so setting the date does not
change the mathematical instance or certificate hashes. See
[Hash specification](#hash-specification) for hash semantics.

The scored pool is derived from the SAIR dataset release and the full
MS-1190 open set as described below. The public package excludes the
organizers' internal source records and direct challenge mappings.
The move tables and published training certificates are frozen.

## Files

For the contestant-facing problem lists, see
[`problems/ac.jsonl`](../../../problems/ac.jsonl) and
[`problems/stable_ac.jsonl`](../../../problems/stable_ac.jsonl). Each file
uses JSON Lines, with one object per line containing only `challenge_id`
and `description` of the initial presentation. These lists are generated
from this manifest; release checks reject any disagreement. The verifier
uses `manifest.json` for exact integer-encoded words and verification limits.

| File | Contents |
|---|---|
| [manifest.json](manifest.json) | The 20,230 scored challenges, `base_score = 1` each, with `instance_hash` per challenge and top-level `move_specs`, `manifest_hash`, `challenge_count`, and `presentation_count` and frozen `limits` (`max_path_length` 100000, `max_total_relator_length` 10000, `max_work` 5000000) |
| [move_spec.json](move_spec.json) | Machine-readable `ac-r2-v1`: the 14 frozen moves (the exact rows covered by `move_spec_hash`), letter encoding, and word-normalization conventions |
| [stable_move_spec.json](stable_move_spec.json) | Machine-readable `sac-r8-v1`: 257 moves, rank cap 8, stabilization/deletion conditions, and canonical finishes to empty |
| [ms1190_metadata.csv](ms1190_metadata.csv) | The full MS-1190 "denominator": all 1190 instances with `status_at_freeze` ∈ open (550) / uncertified (216) / certified (424). Reference material, **not** the pool listing |
| [golden_vectors.json](golden_vectors.json) | Conformance vectors for the reference verifier (`python3 -m verifier --golden ...`) |

The 424 training presentations and their AC and Stable AC certificates are
in [`examples/training_424.json`](../../../examples/training_424.json) and
[`examples/stable_training_424.json`](../../../examples/stable_training_424.json).
The corresponding problem descriptions are in
[`examples/ac.jsonl`](../../../examples/ac.jsonl) and
[`examples/stable_ac.jsonl`](../../../examples/stable_ac.jsonl).

For a complete successful replay, start with the
[training example](../../../examples/README.md). It supplies a separate
unscored manifest for all 424 presentations in both versions, a sample
submission, and the expected verifier receipt.
The 424 training instances are outside both scored problem sets.

## `manifest.json` challenge fields

Every challenge record carries **exactly** these nine keys. It omits
internal difficulty labels and direct source-ID mappings. This is not
a promise of anonymity: the relators and public MS metadata can allow
participants to recognize instances and their origins.

| Field | Semantics |
|---|---|
| `challenge_id` | `ac-NNNNN` or `sac-NNNNN`, with N from 00001 to 10115; matching suffixes name the same initial presentation. The numbering is a fixed seeded shuffle of the pool: it is deliberately meaningless, so neighbouring ids say nothing about difficulty or origin |
| `generators` | Always `["x", "y"]` |
| `initial_relators` | The balanced 2-generator presentation, two freely reduced words over `{±1, ±2}` (`1 = x`, `-1 = x^-1`, `2 = y`, `-2 = y^-1`); total length ≤ 40 |
| `target_relators` | Exact ordered pair `[[1], [2]]` for AC; empty list `[]` for Stable AC |
| `move_spec_version` | `ac-r2-v1` for `ac-`; `sac-r8-v1` for `sac-`; supplied by the challenge, never the contestant |
| `scored` | Always `true` — every challenge in the pool is scored |
| `base_score` | Always `1` |
| `instance_hash` | Hash over `challenge_id`, generators, both relator lists, `move_spec_version`, `move_spec_hash`; see the [hash specification](#hash-specification) |
| `freeze_date` | `null` until the official freeze is set; outside `instance_hash` by design |

Pool composition: the 10000-row SAIR competition draw, minus the 89
draw instances that have a public replayable certificate (they are in
[the AC training file](../../../examples/training_424.json)), plus the 204 MS-1190 **open** instances the draw
missed — so all 550 open MS-1190 instances are scored, no certified one
is. Within each Discovery problem, no two challenges are the same presentation
up to relator order, cyclic rotation, and inversion. The other problem repeats
that pool with its own target and move specification.

## Hash specification

[canon.py](../canon.py) defines all four hashes as
`"sha256:" + lowercase_hex(SHA256(utf8(canonical_text)))`.

- `move_spec_hash`: canonical JSON of the corresponding specification's
  `moves` array, with sorted object keys, no whitespace, and ASCII output.
  Array order is preserved. Explanatory notes are excluded.
- `instance_hash` and `certificate_hash`: the fixed-key-order templates below,
  with no whitespace, ASCII only, and shortest-decimal integers (`-1`, never
  `-01`; no `-0`). Line breaks shown here are illustrative only.

```text
instance_canon    = {"challenge_id":"<id>","generators":["x","y"],
                     "initial_relators":[[...],[...]],
                     "target_relators":<target>,
                     "move_spec_version":"<ver>","move_spec_hash":"<sha256:...>"}
certificate_canon = {"challenge_id":"<id>","move_spec_version":"<ver>",
                     "moves":[m0,m1,...]}
```

`<target>` is `[[1],[2]]` for AC or `[]` for Stable AC. The matching
records have distinct IDs, targets, and instance hashes. `<ver>` is the
official challenge's `move_spec_version`, not a contestant-supplied field.
Submission comments and formatting do not enter certificate hashes.

`manifest_hash` hashes the canonical JSON of the sorted list of all
20,230 `instance_hash` strings, using the same JSON convention as
`move_spec_hash`. The instance template excludes other metadata, including
`scored`, `base_score`, `status_at_freeze`, `source`, and `freeze_date`.
The manifest hash identifies the encoded instances, not the complete scoring
policy or resource limits. Changes to excluded fields leave it unchanged;
changes to hashed instance fields or the hashed move table change the
relevant hashes.

Official scoring records must also retain the complete frozen configuration
(base scores, eligibility, limits, and scoring rules), identified by an
immutable release commit or archived snapshot. Each scoring run records that
configuration, the manifest hash, and verifier version. These are organizer
records, not extra submission fields.

Optional local hash check, from the repository or public package root:

```sh
PYTHONPATH=competition/tools python3 -m verifier \
  --manifest competition/tools/verifier/data/manifest.json --check-hashes
```

## `ms1190_metadata.csv` columns

| Column | Semantics |
|---|---|
| `seq` | 1-based position in the original MS-1190 table |
| `n`, `w`, `w_vector` | Miller–Schupp parameters; `w_vector` is the canonical integer form (space-separated), `w` is human-readable TeX |
| `status_at_freeze` | `open` = no known trivialization; `uncertified` = literature reports solved, no public replayable certificate; `certified` = public replayable path exists (training data) |
| `reported_class` | AC-equivalence class label from the source dataset. **Non-normative**: computed under a different move metric, never a merging basis |
| `training_id` | `ms-train-NNNN` for the 424 certified instances (see [the AC training file](../../../examples/training_424.json)) |
| `prototype_path_length` | Original 12-move path length, certified rows only |

There is no direct `challenge_id` or `scored` column. Nevertheless, an
MS-1190 presentation can be reconstructed from `n` and `w_vector` using
the encoding below and compared with the manifest.

Frozen instance encoding for the MS family: `r0 = x^-1 y^n x
y^-(n+1)`, `r1 = x w^-1`, both freely reduced; the target is the exact
ordered pair `[[1],[2]]` for AC and `[]` for Stable AC.
