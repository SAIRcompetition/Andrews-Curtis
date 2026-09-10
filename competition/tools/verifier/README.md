# Discovery Track reference verifier (`acms_verify`)

This directory provides the Python reference verifier for the AC and Stable AC
problems in [Discovery Track](../../rules/discovery.md). It uses only the
Python standard library.
Local self-checks are available now. Discovery submissions open on September 11,
2026 at 16:00 UTC. The SAIR integration will use these same sources,
with no separate port.

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

## Problem statements and verifier data

The official problem statements are
[AC](../../problems/ac.jsonl) and [Stable AC](../../problems/stable_ac.jsonl):
two JSON Lines files covering the same 10,115 initial presentations.
Each line is one JSON object containing only `challenge_id` and `description`.

The verifier reads the supporting files in [data/](data/README.md):

| File | Purpose |
|---|---|
| [manifest.json](data/manifest.json) | Initial relators, targets, specifications, limits, and hashes for replay |
| [move_spec.json](data/move_spec.json), [stable_move_spec.json](data/stable_move_spec.json) | Numbered AC and Stable AC operations |
| [golden_vectors.json](data/golden_vectors.json) | Conformance inputs and expected results |
| [ms1190_metadata.csv](data/ms1190_metadata.csv) | MS-1190 reference metadata |

The [AC training data](../../examples/training_424.json) and
[Stable AC training data](../../examples/stable_training_424.json) contain
the same 424 presentations, all outside the official pool.

## Usage

Each entry in a submission's `solutions` array contains only
`challenge_id` and `moves`. The verifier obtains the move-spec version
from the official challenge for replay and certificate hashing. `ac-`
IDs use `ac-r2-v1` (0–13); `sac-` IDs use `sac-r8-v1` (0–256).
One submission may contain both. The rank cap applies only to the
Stable AC problem in Discovery.

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
python3 -m acms_verify --manifest data/manifest.json \
                       --submission mine.json --pretty

# run the reference conformance vectors
python3 -m acms_verify --golden data/golden_vectors.json

# recompute and check every hash in the manifest
python3 -m acms_verify --manifest data/manifest.json --check-hashes
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
