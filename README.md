# ACC — The Andrews–Curtis Conjecture Competition (development repository)

**Prelaunch development preview.** Registration and submissions are not
open. The release schedule and official data freeze have not been set.

Backend for ACC: trivializing balanced presentations of the trivial
group with atomic Andrews–Curtis moves over a 10,115-instance
pool, plus a counterexample track for purported disproofs of the
conjecture. Structured after SAIR's IGP24 competition.

ACC is co-organized by (in alphabetical order by surname): Lucas Fagan,
Sergei Gukov, Terence Tao.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `competition/` | **The IGP24-aligned public tree** (single source of truth): `rules/`, current `challenges/` data + hashes, `examples/`, `tools/verifier/` (reference verifier), `tools/lean/`, `competition.yaml` | yes — exported verbatim by `build/release.py` |
| `spec/` | Internal design doc (`DESIGN.md`) | no |
| `build/` | `competition_state.json` (maintained release state and schedule), `sync_dataset.py` + `build_manifest_v2.py` (regenerate data and synchronize metadata), `build_manifest.py` (v1 manifest library), `release.py` (checks and exports previews or official releases), `checks/` (original verification scripts) | no |
| `tests/` | Verifier + frozen-data acceptance tests | no |
| `server/` | Scoring engine (P2); submission service pending decision O-1 | no |
| `lean/` | Formalization workspace (O-3 spike → P4) | no |
| `reference/` | Frozen prototype `index.html` — read-only, never a production dependency | no |

## Commands

```sh
# regenerate data from the SAIR dataset release and synchronize release metadata
python3 build/sync_dataset.py --release ../sair_dataset/release
python3 build/build_manifest_v2.py

# regenerate the successful training example and its expected receipt
python3 build/build_examples.py

# full test suite (verifier + data + scoring)
python3 -m unittest discover -s tests -t .
(cd server && python3 -m unittest discover -s tests)

# Lean spike
(cd lean/Competition && lake build)

# run the successful, unscored training example
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty

# assemble + verify a clearly marked development preview
python3 build/release.py --preview  # -> dist/ACMS-public

# official release gate; currently fails because schedule/freeze are not set
python3 build/release.py
```

Release metadata is maintained in `build/competition_state.json`, not
edited independently in generated files. Current `status` is
`prelaunch`; `freeze_date`, `freeze_commit`, `registration_opens`,
`submissions_open`, `submission_deadline`, and `certificate_release`
are all `null`. `build/build_manifest_v2.py` synchronizes the manifest
and `competition.yaml` from that state.

Before an official release:

1. Set the approved schedule and freeze date in the maintained state,
   then run `python3 build/build_manifest_v2.py`.
2. Freeze the generated `manifest.json` and `move_spec.json` in git.
3. Record that commit as `freeze_commit` in `build/competition_state.json`,
   then run `python3 build/build_manifest_v2.py` again to synchronize YAML.
4. Run `python3 build/release.py`.

The default release command rejects incomplete metadata or an unverified
git freeze; `--preview` allows local review without claiming an official
release. See `competition/examples/README.md` for the sample receipt and
the separate rejection example.
