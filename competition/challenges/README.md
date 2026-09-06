# Discovery Track challenge data (`acms-v2`) — prelaunch preview

**The official data freeze is not yet set.** This preview contains
10,115 Discovery Track challenges for local inspection and verification
in the Andrews–Curtis Conjecture Challenge (ACC).
`freeze_date` and `freeze_commit` are `null`, as are registration,
submission, deadline, and certificate-release dates in
`competition.yaml`. The competition status is `prelaunch`.

Before public launch, the organizers will freeze `manifest.json` and
`move_spec.json` in git and publish the freeze commit. Release metadata
comes from the development repository's `build/competition_state.json`;
`build/build_manifest_v2.py` synchronizes generated data and metadata.
`freeze_date` is outside `instance_hash`, so setting the date does not
change the mathematical instance or certificate hashes. See
[evaluation.md](../rules/evaluation.md#5-hashes) for hash semantics.

The scored pool is derived from the SAIR dataset release and the full
MS-1190 open set as described below. The public package excludes the
organizers' internal source records and direct challenge mappings.
`move_spec.json` and `training_424.json` remain byte-frozen.

## Files

| File | Contents |
|---|---|
| `manifest.json` | The 10,115 scored challenges, `base_score = 1` each, with `instance_hash` per challenge and the top-level `move_spec_hash` / `manifest_hash` / `challenge_count` and frozen `limits` (`max_path_length` 100000, `max_total_relator_length` 10000, `max_work` 5000000) |
| `move_spec.json` | Machine-readable `ac-r2-v1`: the 14 frozen moves (the exact rows covered by `move_spec_hash`), letter encoding, and word-normalization conventions |
| `ms1190_metadata.csv` | The full MS-1190 "denominator": all 1190 instances with `status_at_freeze` ∈ open (550) / uncertified (216) / certified (424). Reference material, **not** the pool listing |
| `training_424.json` | 424 known trivializations converted to `ac-r2-v1` (not scored challenges — published training data) |
| `golden_vectors.json` | Conformance vectors for the reference verifier (`python3 -m acms_verify --golden ...`) |

For a complete successful replay, start with the
[training example](../examples/README.md). It supplies a separate
unscored manifest, a submission, and the expected verifier receipt.
The 424 training instances are outside the scored pool. A Prove Track
proof concerns the full conjecture; a disproof may use a presentation
outside this pool. See the [official statement](../rules/statement.md).

## `manifest.json` challenge fields

Every challenge record carries **exactly** these nine keys. It omits
internal difficulty labels and direct source-ID mappings. This is not
a promise of anonymity: the relators and public MS metadata can allow
participants to recognize instances and their origins.

| Field | Semantics |
|---|---|
| `challenge_id` | `ac-v1-NNNNN`, `ac-v1-00001` … `ac-v1-10115`. The numbering is a fixed seeded shuffle of the pool: it is deliberately meaningless, so neighbouring ids say nothing about difficulty or origin |
| `generators` | Always `["x", "y"]` |
| `initial_relators` | The balanced 2-generator presentation, two freely reduced words over `{±1, ±2}` (`1 = x`, `-1 = x^-1`, `2 = y`, `-2 = y^-1`); total length ≤ 40 |
| `target_relators` | Always the exact ordered pair `[[1], [2]]` |
| `move_spec_version` | Always `ac-r2-v1` |
| `scored` | Always `true` — every challenge in the pool is scored |
| `base_score` | Always `1` |
| `instance_hash` | Hash over `challenge_id`, generators, both relator lists, `move_spec_version`, `move_spec_hash`; see the [hash specification](../rules/evaluation.md#5-hashes) |
| `freeze_date` | `null` until the official freeze is set; outside `instance_hash` by design |

Pool composition: the 10000-row SAIR competition draw, minus the 89
draw instances that have a public replayable certificate (they are in
`training_424.json`), plus the 204 MS-1190 **open** instances the draw
missed — so all 550 open MS-1190 instances are scored, no certified one
is, and no two challenges are the same presentation up to relator
order, cyclic rotation, and inversion.

## `ms1190_metadata.csv` columns

| Column | Semantics |
|---|---|
| `seq` | 1-based position in the original MS-1190 table |
| `n`, `w`, `w_vector` | Miller–Schupp parameters; `w_vector` is the canonical integer form (space-separated), `w` is human-readable TeX |
| `status_at_freeze` | `open` = no known trivialization; `uncertified` = literature reports solved, no public replayable certificate; `certified` = public replayable path exists (training data) |
| `reported_class` | AC-equivalence class label from the source dataset. **Non-normative**: computed under a different move metric, never a merging basis |
| `training_id` | `ms-train-NNNN` for the 424 certified instances (see `training_424.json`) |
| `prototype_path_length` | Original 12-move path length, certified rows only |

There is no direct `challenge_id` or `scored` column. Nevertheless, an
MS-1190 presentation can be reconstructed from `n` and `w_vector` using
the encoding below and compared with the manifest.

Frozen instance encoding for the MS family: `r0 = x^-1 y^n x
y^-(n+1)`, `r1 = x w^-1`, both freely reduced; the target is the exact
ordered pair `[[1],[2]]`.
