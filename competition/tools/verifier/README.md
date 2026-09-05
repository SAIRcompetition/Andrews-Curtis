# ACMS reference verifier (`acms_verify`)

**Prelaunch preview.** This Python reference verifier is available for
local self-checking now; competition submissions are not open. The
planned competition service will use these same standard-library-only
sources, with no separate port.

> Local results are self-checks. Once the competition opens, the
> server-side verifier will be the authority for official results.

## Layout

| Module | Contents | DESIGN.md |
|---|---|---|
| `acms_verify/core.py` | frozen 14-move table, free reduction, deterministic `verify()` | §1.3, §4.2 |
| `acms_verify/canon.py` | explicit byte templates for `instance_hash` / `certificate_hash`, JCS hashing for `move_spec_hash` / `manifest_hash` | §3.2, §3.3 |
| `acms_verify/submission.py` | submission parsing, whole-vs-per-item rejection, forbidden result keys, check priority | §4.1, §4.2, O-5 |
| `acms_verify/golden.py` | self-contained conformance vector runner | §9.2 |
| `acms_verify/cli.py` | `acms-verify` command line | §4.5 |

## Usage

Each entry in a submission's `solutions` array contains only
`challenge_id` and `moves`. The verifier obtains the move-spec version
from the official challenge for replay and certificate hashing.

Start with a successful, unscored training example. Run from the
repository or exported package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

The expected full receipt and a separate rejection example are in the
[examples guide](../../examples/README.md).

For other checks, run from this directory (`competition/tools/verifier/`):

```sh
# verify a submission against the current competition manifest
python3 -m acms_verify --manifest ../../challenges/manifest.json \
                       --submission mine.json --pretty

# run the reference conformance vectors
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
