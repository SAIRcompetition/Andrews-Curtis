# Frozen challenge data (`acms-ms-v1`)

**Freeze discipline: before public launch, freeze both `manifest.json`
and `move_spec.json` in git**, and record the commit hash in
`competition.yaml` (DESIGN.md §9.3). Regenerate only via
`build/build_manifest.py`, never by hand.

> `freeze_date` is currently the **D-9 placeholder**
> `2026-09-01T00:00:00Z`. It is deliberately outside `instance_hash`
> (§3.2), so fixing D-9 later does not invalidate any certificate, but
> it must be updated here and in `competition.yaml` at the same time.

## Files

| File | Contents |
|---|---|
| `manifest.json` | The 550 open (T1) scored challenges, `base_score = 1` each (D-8), with `instance_hash` per challenge and the top-level `move_spec_hash` / `manifest_hash` and frozen `limits` (`max_path_length` 100000, `max_total_relator_length` 10000, `max_work` 5000000) |
| `move_spec.json` | Machine-readable `ac-r2-v1`: the 14 frozen moves (the exact rows covered by `move_spec_hash`), letter encoding, and the §1.2 canonicalization table |
| `ms1190_metadata.csv` | The full MS-1190 "denominator": all 1190 instances with `status_at_freeze` ∈ open (550) / uncertified (216) / certified (424) |
| `training_424.json` | 424 known trivializations converted to `ac-r2-v1` (not scored challenges — published training data) |
| `golden_vectors.json` | Conformance vectors: run them to prove your verifier agrees with the official one (`python3 -m acms_verify --golden ...`) |

## `ms1190_metadata.csv` columns

| Column | Semantics |
|---|---|
| `seq` | 1-based position in the original MS-1190 table (also the challenge numbering order — neutral, no difficulty signal, per O-4) |
| `n`, `w`, `w_vector` | Miller–Schupp parameters; `w_vector` is the canonical integer form (space-separated), `w` is human-readable TeX |
| `status_at_freeze` | `open` = no known trivialization (T1, scored); `uncertified` = literature reports solved, no public replayable certificate (T2, **not** in v1 pool, D-3); `certified` = public replayable path exists (training data) |
| `reported_class` | AC-equivalence class label from the source dataset. **Non-normative** (§2.3): computed under a different move metric, never a merging basis |
| `scored` / `challenge_id` | `true` + `ms-v1-NNNN` exactly for the 550 open instances |
| `training_id` | `ms-train-NNNN` for the 424 certified instances (see `training_424.json`) |
| `prototype_path_length` | Original 12-move path length, certified rows only |

Instance encoding (D-2, frozen): `r0 = x^-1 y^n x y^-(n+1)`,
`r1 = x w^-1`, both freely reduced; target is the exact ordered pair
`[[1],[2]]`.
