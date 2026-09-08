# ACMS reference verifier (`acms_verify`)

The single authoritative verifier implementation for the ACMS
competition (decision D-10: Python only, standard library only). The
same sources run inside the competition system and ship in the public
release package — there is no port.

Two frozen move specs, one per trivialization track:

| Spec | Track | Moves | Rank | Target |
|---|---|---|---|---|
| `ac-r2-v1` | `ac-v1-NNNNN` | 14 (ids 0–13) | 2 | the exact ordered pair `[[1],[2]]` |
| `sac-r8-v1` | `sac-v1-NNNNN` | 257 (ids 0–256) | up to 8 | the empty presentation `[]` |

Ids 0–13 are row for row identical in both tables, so an accepted
`ac-r2-v1` certificate followed by `[16, 15]` (destabilize `r1`, then
`r0`) is an accepted `sac-r8-v1` certificate for the same presentation:
+2 moves, +0 peak, +1 work. A challenge names its spec in
`move_spec_version`; a solution that names a different one is rejected
with `E_SPEC_MISMATCH`, and a single submission may mix both tracks.

> The reference verifier is for contestant self-checking only; the
> server-side verifier is the sole authority for official results.

## Layout

| Module | Contents | DESIGN.md |
|---|---|---|
| `acms_verify/core.py` | frozen 14-move `ac-r2-v1` table, free reduction, deterministic `verify()` | §1.3, §4.2 |
| `acms_verify/stable_core.py` | frozen 257-move `sac-r8-v1` table, variable-rank state, deterministic `verify()` | §1.3, §4.2 |
| `acms_verify/specs.py` | move-spec registry: version → table, hash, target, `verify` | §3.3, §4.2 |
| `acms_verify/canon.py` | explicit byte templates for `instance_hash` / `certificate_hash`, JCS hashing for `move_spec_hash` / `manifest_hash` | §3.2, §3.3 |
| `acms_verify/submission.py` | submission parsing, per-spec dispatch, whole-vs-per-item rejection, forbidden result keys, check priority | §4.1, §4.2, O-5 |
| `acms_verify/golden.py` | self-contained conformance vector runner | §9.2 |
| `acms_verify/cli.py` | `acms-verify` command line | §4.5 |

## Usage

Run from this directory (`competition/tools/verifier/`):

```sh
# verify a submission against the frozen manifest
python3 -m acms_verify --manifest ../../challenges/manifest.json \
                       --submission mine.json --pretty

# prove this verifier agrees with the official one
python3 -m acms_verify --golden ../../challenges/golden_vectors.json

# recompute and check every hash in the manifest
python3 -m acms_verify --manifest ../../challenges/manifest.json --check-hashes
```

Exit codes: `0` all verified OK · `1` accepted but some solution
rejected · `2` whole-submission rejection / golden failures · `3`
usage or IO error.

`--check-hashes` recomputes each `instance_hash` under the spec its own
challenge names and checks every entry of the manifest's `move_specs`
list against this verifier's frozen tables; `--submission` refuses to
run at all (exit `3`) if any of them disagrees.

## Error codes

Per-move errors carry a 0-based `move_index`; the check order inside
`verify` is path length → move id → **applicability** → relator length →
work budget → target.

`E_MOVE_NOT_APPLICABLE` is `sac-r8-v1` only: a move id is legal at every
rank, but whether it *applies* depends on the current rank. The verdict
carries `move`, `move_index` and one `reason`:

| Reason | Meaning |
|---|---|
| `relator_out_of_rank` | the move names a relator index ≥ the current rank |
| `generator_out_of_rank` | the conjugator names a generator > the current rank |
| `max_rank_exceeded` | stabilizing (id 14) at rank 8 |
| `destabilize_precondition` | the relator is not exactly one positive generator letter, or that generator occurs in another relator |

## Tests

The acceptance suite lives in the development repository
(`tests/`, run with `python3 -m unittest discover -s tests -t .` from
its root); it covers acceptance rows 1, 2, 2b, 3, 4, 5 (local half) and
11 of DESIGN.md §11, including the full 424-path training replay per
track with the [Verified] statistics of §1.5 asserted exactly, and a
breadth-first re-derivation of both canonicalization tables. The public package
ships the golden vectors instead — anyone can re-verify conformance
with the `--golden` command above.
