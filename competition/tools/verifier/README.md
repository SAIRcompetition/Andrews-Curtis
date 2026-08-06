# ACMS reference verifier (`acms_verify`)

The single authoritative verifier implementation for the ACMS
competition (decision D-10: Python only, standard library only). The
same sources run inside the competition system and ship in the public
release package — there is no port.

> The reference verifier is for contestant self-checking only; the
> server-side verifier is the sole authority for official results.

## Layout

| Module | Contents | DESIGN.md |
|---|---|---|
| `acms_verify/core.py` | frozen 14-move table, free reduction, deterministic `verify()` | §1.3, §4.2 |
| `acms_verify/canon.py` | explicit byte templates for `instance_hash` / `certificate_hash`, JCS hashing for `move_spec_hash` / `manifest_hash` | §3.2, §3.3 |
| `acms_verify/submission.py` | submission parsing, whole-vs-per-item rejection, forbidden result keys, check priority | §4.1, §4.2, O-5 |
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

## Tests

The acceptance suite lives in the development repository
(`tests/`, run with `python3 -m unittest discover -s tests -t .` from
its root); it covers acceptance rows 1, 2, 2b, 3, 4, 5 (local half) and
11 of DESIGN.md §11, including the full 424-path training replay with
the [Verified] statistics of §1.5 asserted exactly. The public package
ships the golden vectors instead — anyone can re-verify conformance
with the `--golden` command above.
