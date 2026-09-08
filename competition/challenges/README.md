# Frozen challenge data (`acms-v3`)

**Freeze discipline: before public launch, freeze `manifest.json`,
`move_spec.json`, `stable_move_spec.json`, `training_424.json` and
`stable_training_424.json` in git**, and record the commit hash in
`competition.yaml` (DESIGN.md §9.3). Regenerate only via
`build/build_manifest_v2.py`, never by hand.

> `freeze_date` is currently the **D-9 placeholder**
> `2026-09-01T00:00:00Z`. It is deliberately outside `instance_hash`
> (§3.2), so fixing D-9 later does not invalidate any certificate, but
> it must be updated here and in `competition.yaml` at the same time.

Upstream is no longer `reference/index.html`. The scored pool is
distilled from the private SAIR dataset release into `build/data/`
(`scored_pool_source.jsonl` + `SOURCES.json`, written by
`build/sync_dataset.py`), and `build/build_manifest_v2.py` turns that
into `manifest.json`. `reference/index.html` remains the source of the
MS-1190 denominator and of the 424 published trivializations only, and
`move_spec.json`, `stable_move_spec.json`, `training_424.json` and
`stable_training_424.json` are byte-frozen: the generator aborts if any
of them would change.

## Files

| File | Contents |
|---|---|
| `manifest.json` | The 20,230 scored challenges — the 10,115 presentations under each of the two move specifications — `base_score = 1` each (D-8), with `instance_hash` per challenge and the top-level `move_specs` / `manifest_hash` / `challenge_count` / `presentation_count` and frozen `limits` (`max_path_length` 100000, `max_total_relator_length` 10000, `max_work` 5000000) |
| `move_spec.json` | Machine-readable `ac-r2-v1`: the 14 frozen moves (the exact rows covered by its `move_spec_hash`), letter encoding, and the §1.2 canonicalization table |
| `stable_move_spec.json` | Machine-readable `sac-r8-v1`: the 257 frozen moves, ids 0–256 (the exact rows covered by its `move_spec_hash`), letter encoding for generators 1..8, `max_rank: 8`, applicability conditions, and the rank-2 canonicalization table to the empty presentation |
| `ms1190_metadata.csv` | The full MS-1190 "denominator": all 1190 instances with `status_at_freeze` ∈ open (550) / uncertified (216) / certified (424). Reference material, **not** the pool listing |
| `training_424.json` | 424 known trivializations converted to `ac-r2-v1` (not scored challenges — published training data) |
| `stable_training_424.json` | The same 424 instances in `sac-r8-v1`, each certificate extended by `[16, 15]` so that it ends at the empty presentation — published warm-up data for track 2 |
| `golden_vectors.json` | Conformance vectors for both specifications: run them to prove your verifier agrees with the official one (`python3 -m acms_verify --golden ...`) |

## `manifest.json` top-level fields

`manifest_version` is `acms-v3`. The singular `move_spec_version` /
`move_spec_hash` / `target_relators` fields of `acms-v2` are replaced by
a `move_specs` list, one entry per frozen specification:

| Field | Semantics |
|---|---|
| `move_spec_version` | `ac-r2-v1` or `sac-r8-v1` |
| `move_spec_hash` | SHA-256 of the canonical JSON of that file's `moves` array |
| `file` | `move_spec.json` or `stable_move_spec.json` |
| `target_relators` | `[[1],[2]]` or `[]` |
| `max_rank` | 2 or 8 |
| `id_prefix` | `ac-v1-` or `sac-v1-` — the prefix that selects this specification |

(`competition.yaml` publishes the same list with the shorter key names
`version` / `hash` / `target`.)

`challenge_count` is 20230; `presentation_count` is 10115, the number
of distinct presentations, each of which appears once per track.

## `manifest.json` challenge fields

Every challenge record carries **exactly** these nine keys, and nothing
else — no difficulty, family, tier, or provenance signal (O-4):

| Field | Semantics |
|---|---|
| `challenge_id` | `ac-v1-NNNNN` (`ac-v1-00001` … `ac-v1-10115`) or `sac-v1-NNNNN` (`sac-v1-00001` … `sac-v1-10115`). `sac-v1-N` is the **same presentation** as `ac-v1-N`, and the prefix selects the move specification. The numbering is a fixed seeded shuffle of the pool: it is deliberately meaningless, so neighbouring ids say nothing about difficulty or origin |
| `generators` | Always `["x", "y"]` — the generators of the initial presentation; under `sac-r8-v1` the rank varies along the path, up to 8 |
| `initial_relators` | The balanced 2-generator presentation, two freely reduced words over `{±1, ±2}` (`1 = x`, `-1 = x^-1`, `2 = y`, `-2 = y^-1`); total length ≤ 40. Identical for `ac-v1-N` and `sac-v1-N` |
| `target_relators` | `[[1], [2]]` (exact ordered) for an `ac-v1-` challenge; `[]`, the empty presentation, for a `sac-v1-` one |
| `move_spec_version` | `ac-r2-v1` for an `ac-v1-` challenge, `sac-r8-v1` for a `sac-v1-` one |
| `scored` | Always `true` — every challenge in the pool is scored, in its own track |
| `base_score` | Always `1` (D-8) |
| `instance_hash` | §3.2 hash over `challenge_id`, generators, both relator lists, `move_spec_version`, `move_spec_hash`. The template is unchanged, so every `ac-v1-` hash is the same as in `acms-v2`; a `sac-v1-` record differs from its `ac-v1-` twin in id, target, and the two spec fields |
| `freeze_date` | The D-9 placeholder above; outside `instance_hash` by design |

Pool composition: the 10000-row SAIR competition draw, minus the 89
draw instances that have a public replayable certificate (they are in
`training_424.json`), plus the 204 MS-1190 **open** instances the draw
missed — so all 550 open MS-1190 instances are scored, no certified one
is, and no two presentations are the same up to relator order, cyclic
rotation, and inversion. That pool of 10,115 presentations is
then listed twice, once per track.

## `ms1190_metadata.csv` columns

| Column | Semantics |
|---|---|
| `seq` | 1-based position in the original MS-1190 table |
| `n`, `w`, `w_vector` | Miller–Schupp parameters; `w_vector` is the canonical integer form (space-separated), `w` is human-readable TeX |
| `status_at_freeze` | `open` = no known trivialization; `uncertified` = literature reports solved, no public replayable certificate (D-3); `certified` = public replayable path exists (training data) |
| `reported_class` | AC-equivalence class label from the source dataset. **Non-normative** (§2.3): computed under a different move metric, never a merging basis |
| `training_id` | `ms-train-NNNN` for the 424 certified instances (see `training_424.json` and `stable_training_424.json`) |
| `prototype_path_length` | Original 12-move path length, certified rows only |

There is deliberately no `challenge_id` or `scored` column: the pool is
no longer MS-1190, and either column would disclose which manifest
entries are Miller–Schupp instances. Recover the MS-1190 presentation
from `n` and `w_vector` with the frozen D-2 encoding below.

Instance encoding (D-2, frozen) for the MS family: `r0 = x^-1 y^n x
y^-(n+1)`, `r1 = x w^-1`, both freely reduced; the target is the exact
ordered pair `[[1],[2]]` under `ac-r2-v1` and the empty presentation
under `sac-r8-v1`.
