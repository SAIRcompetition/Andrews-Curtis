# Frozen challenge data (`acms-v2`)

**Freeze discipline: before public launch, freeze both `manifest.json`
and `move_spec.json` in git**, and record the commit hash in
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
`move_spec.json` / `training_424.json` are byte-frozen: the generator
aborts if either would change.

## Files

| File | Contents |
|---|---|
| `manifest.json` | The 10115 scored challenges, `base_score = 1` each (D-8), with `instance_hash` per challenge and the top-level `move_spec_hash` / `manifest_hash` / `challenge_count` and frozen `limits` (`max_path_length` 100000, `max_total_relator_length` 10000, `max_work` 5000000) |
| `move_spec.json` | Machine-readable `ac-r2-v1`: the 14 frozen moves (the exact rows covered by `move_spec_hash`), letter encoding, and the §1.2 canonicalization table |
| `ms1190_metadata.csv` | The full MS-1190 "denominator": all 1190 instances with `status_at_freeze` ∈ open (550) / uncertified (216) / certified (424). Reference material, **not** the pool listing |
| `training_424.json` | 424 known trivializations converted to `ac-r2-v1` (not scored challenges — published training data) |
| `golden_vectors.json` | Conformance vectors: run them to prove your verifier agrees with the official one (`python3 -m acms_verify --golden ...`) |

## `manifest.json` challenge fields

Every challenge record carries **exactly** these nine keys, and nothing
else — no difficulty, family, tier, or provenance signal (O-4):

| Field | Semantics |
|---|---|
| `challenge_id` | `ac-v1-NNNNN`, `ac-v1-00001` … `ac-v1-10115`. The numbering is a fixed seeded shuffle of the pool: it is deliberately meaningless, so neighbouring ids say nothing about difficulty or origin |
| `generators` | Always `["x", "y"]` |
| `initial_relators` | The balanced 2-generator presentation, two freely reduced words over `{±1, ±2}` (`1 = x`, `-1 = x^-1`, `2 = y`, `-2 = y^-1`); total length ≤ 40 |
| `target_relators` | Always the exact ordered pair `[[1], [2]]` |
| `move_spec_version` | Always `ac-r2-v1` |
| `scored` | Always `true` — every challenge in the pool is scored |
| `base_score` | Always `1` (D-8) |
| `instance_hash` | §3.2 hash over `challenge_id`, generators, both relator lists, `move_spec_version`, `move_spec_hash` |
| `freeze_date` | The D-9 placeholder above; outside `instance_hash` by design |

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
| `status_at_freeze` | `open` = no known trivialization; `uncertified` = literature reports solved, no public replayable certificate (D-3); `certified` = public replayable path exists (training data) |
| `reported_class` | AC-equivalence class label from the source dataset. **Non-normative** (§2.3): computed under a different move metric, never a merging basis |
| `training_id` | `ms-train-NNNN` for the 424 certified instances (see `training_424.json`) |
| `prototype_path_length` | Original 12-move path length, certified rows only |

There is deliberately no `challenge_id` or `scored` column: the pool is
no longer MS-1190, and either column would disclose which manifest
entries are Miller–Schupp instances. Recover the MS-1190 presentation
from `n` and `w_vector` with the frozen D-2 encoding below.

Instance encoding (D-2, frozen) for the MS family: `r0 = x^-1 y^n x
y^-(n+1)`, `r1 = x w^-1`, both freely reduced; the target is the exact
ordered pair `[[1],[2]]`.
