# Andrews–Curtis Conjecture Challenge (ACC) — development repository

**Prelaunch development preview.** Registration is scheduled for September
8, 2026, Discovery for September 11, and Proof for September 20; the
submission deadline is November 30. Exact UTC times and the official data
freeze remain pending. Registration and online submissions are not open.

ACC is one competition with **two tracks**, each containing **AC** and
**Stable AC** problems:

| Track | Task |
|---|---|
| **Discovery Track** | Find short verified trivializations, with separate AC and Stable AC leaderboards |
| **Proof Track** | Prove or disprove either full conjecture |

Discovery uses the same 10,115 presentations for both problems. The AC
problem fixes rank 2; Stable AC permits ranks up to 8. Proof Track concerns
the full conjectures without search bounds. Proof results do not automatically
end Discovery. The public package follows SAIR's IGP24 structure.

ACC is co-organized by (in alphabetical order by surname): Lucas Fagan,
Sergei Gukov, Terence Tao.

For the full conjectures, start with the
[mathematical statement](competition/rules/statement.md) and
[Lean build instructions](competition/tools/lean/README.md).

Proof submissions identify the conjecture, claim type, and description, with a complete
argument in the description, a PDF or paper, a GitHub repository at a
fixed commit, or an arXiv paper at a fixed version. Submissions and their
immutable versions are public, with comments for community peer review,
shared learning, and improvement. Lean submissions are open to the same
scrutiny. Organizers may assess selected claims for competition recognition.
Priority follows the earliest eligible complete correct version, with
references and contributions recorded separately.

SAIR is the competition platform for registration, teams, submissions,
community discussion, and leaderboard presentation. The integration and persistent
submission service remain to be implemented. Outstanding scoring work
includes event ordering, `current_best_solver` and `solved` semantics,
and complete configuration snapshots for reproducible scoring. The
reference engine requires a separate move-spec selection for each Discovery
leaderboard and rejects an unselected mixed manifest. The
local verifier and release checks do not establish that these platform
features are ready.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `competition/` | **The IGP24-aligned public tree** (single source of truth): `rules/`, current `challenges/` data + hashes, `examples/`, `tools/verifier/` (reference verifier), `tools/lean/`, `competition.yaml` | yes — exported by `build/release.py`, excluding caches and build products |
| `spec/` | Internal design doc (`DESIGN.md`) | no |
| `build/` | `competition_state.json` (maintained release state and schedule), `sync_dataset.py` + `build_manifest_v2.py` (regenerate data and synchronize metadata), `build_manifest.py` (v1 manifest library), `release.py` (checks and exports previews or official releases), `checks/` (original verification scripts) | no |
| `tests/` | Verifier + frozen-data acceptance tests | no |
| `server/` | Scoring engine; SAIR adapter, persistent submission service, and remaining scoring fixes are pending | no |
| `reference/` | Frozen prototype `index.html` — read-only, never a production dependency | no |

Publish the generated public package, not this development repository.
The development tree and its Git history contain organizer-only data,
including source records and direct challenge mappings under `build/`;
they are excluded from the export and must not be exposed by making the
development repository public as a substitute for publishing the package.

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

# official full-conjecture statements (first-use setup: competition/tools/lean/README.md)
(cd competition/tools/lean && lake build)

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
`submissions_open`, `prove_submissions_open`, `submission_deadline`, and `certificate_release`
are all `null`. Date-only plans are recorded separately in `announced_dates`:
registration September 8, Discovery September 11, Proof September 20,
and the deadline November 30, 2026. `submissions_open` supplies Discovery UTC opening and
`prove_submissions_open` supplies Proof UTC opening; each track exposes its
relevant `opens_at`. `build/build_manifest_v2.py` synchronizes the manifest
and `competition.yaml` from that state.

Before an official release:

1. Set the approved schedule and freeze date in the maintained state,
   then run `python3 build/build_manifest_v2.py`.
2. Freeze `manifest.json`, `move_spec.json`, and `stable_move_spec.json` in git.
3. Record that commit as `freeze_commit` in `build/competition_state.json`,
   then run `python3 build/build_manifest_v2.py` again to synchronize YAML.
4. Run `python3 build/release.py`.

The default release command rejects incomplete metadata or an unverified
git freeze; `--preview` allows local review without claiming an official
release. See `competition/examples/README.md` for the sample receipt and
the separate rejection example.
