# Discovery Track reference verifier (`acms_verify`)

This Python reference verifier supports the AC and Stable AC problems in
Discovery Track of the Andrews–Curtis Conjecture (ACC) Challenge. Local
self-checks are available now. Discovery submissions open on September 11,
2026 at 16:00 UTC.
The SAIR integration will use these same standard-library-only sources,
with no separate port. Proofs and disproofs belong to the Proof Track
and are not processed by this path verifier.

> Local results are self-checks. Once the competition opens, the
> server-side verifier will be the authority for official results.

## Layout

| Module | Contents |
|---|---|
| `acms_verify/core.py` | table of 14 move IDs, free reduction, deterministic `verify()` |
| `acms_verify/stable_core.py` | table of 257 move IDs, variable-rank replay up to rank 8, empty target |
| `acms_verify/specs.py` | Dispatch by the challenge's specification; validate both move tables |
| `acms_verify/canon.py` | explicit byte templates for `instance_hash` / `certificate_hash`, JCS hashing for `move_spec_hash` / `manifest_hash` |
| `acms_verify/submission.py` | submission parsing, whole-vs-per-item rejection, forbidden result keys, check priority |
| `acms_verify/golden.py` | self-contained conformance vector runner |
| `acms_verify/cli.py` | `acms-verify` command line |

The public [evaluation rules](../../rules/discovery.md) specify move
semantics, the submission contract, limits, hashes, and error codes.

## Usage

Each entry in a submission's `solutions` array contains only
`challenge_id` and `moves`. The verifier obtains the move-spec version
from the official challenge for replay and certificate hashing. `ac-v1-`
IDs use `ac-r2-v1` (0–13); `sac-v1-` IDs use `sac-r8-v1` (0–256).
One submission may contain both. The rank cap applies only to the
Stable AC problem in Discovery; proving either conjecture uses the
separate Lean targets.

Start with a successful, unscored training example. Run from the
repository or exported package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

The expected full receipt and a separate rejection example are in the
[examples guide](../../examples/README.md).

`accepted: true` means only that the submission passed structural
validation. A solution succeeds only when its own `results[].ok` is
`true`. A well-formed submission can therefore have `accepted: true`
even when every solution fails; inspect each result and its error code.

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

Exit codes: `0` all solutions verified OK · `1` structurally accepted but some solution
rejected · `2` whole-submission rejection / golden failures · `3`
usage or IO error.

## Tests

The acceptance suite lives in the development repository
(`tests/`, run with `python3 -m unittest discover -s tests -t .` from
its root). It covers move replay, parsing, limits, errors, hashes, and
all 424 training paths under each specification. The public package includes golden vectors
that anyone can run with the `--golden` command above.
