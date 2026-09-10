# The Andrews–Curtis Conjecture (ACC) Challenge — development repository

[Registration is open on SAIR](https://competition.sair.foundation/competitions/acc).
The competition launches with **Discovery Track on September 11, 2026 at
16:00 UTC**, followed by **Proof Track on September 20, 2026**. The
submission deadline is November 30, 2026.

The ACC Challenge is co-organized by Caltech and the SAIR Foundation, with
Lucas Fagan, Sergei Gukov, and Terence Tao. It has **two tracks**, each
covering **AC** and **Stable AC**:

| Guide | Contents |
|---|---|
| [Overview](competition/rules/overview.md) | Background, tracks, dates, registration, and common rules; identical to `prelaunch.md` |
| [Discovery Track](competition/rules/discovery.md) | The 10,115-presentation pool, moves, examples, verifier contract, and separate AC/Stable AC scoring |
| [Proof Track](competition/rules/proof.md) | Full mathematical statements, proof/disproof materials, Lean targets, public versions, and community peer review |

Discovery works with explicit finite move sequences. Proof accepts a
complete proof or disproof of either full conjecture, written or formalized;
submissions are public, versioned, and open to community discussion.

SAIR hosts registration, teams, submissions, and leaderboards. This
repository supplies the data, reference mathematical checks, and an internal
scoring engine. The development repository does not implement or certify
all platform services. See [the integration guide](spec/DESIGN.md#8-sair-platform-integration)
for implementation responsibilities and the separate acceptance checks for
each track. Discovery launch does not wait for the later Proof launch.

## Discovery Track resources

The two problem files contain the AC and Stable AC versions of the **same
10,115 initial presentations**. Each uses JSON Lines: one JSON object per
line, containing only `challenge_id` and `description` of the initial presentation.

| File or guide | Contents |
|---|---|
| [AC problems](competition/problems/ac.jsonl) | 10,115 AC problem statements |
| [Stable AC problems](competition/problems/stable_ac.jsonl) | 10,115 Stable AC problem statements |
| [Examples](competition/examples/README.md) | The same 424 separate training presentations in both versions, plus runnable submissions and receipts |
| [Discovery verifier](competition/tools/verifier/README.md) | [Discovery Track](competition/rules/discovery.md) replay commands and supporting [data](competition/tools/verifier/data/README.md) |

The 424 training presentations are outside the scored pool. The verifier
reads `competition/tools/verifier/data/manifest.json` to check submissions.

## Proof Track resources

The [Proof Track guide](competition/rules/proof.md) contains the full conjecture
statements, submission instructions, and review rules. The
[Lean guide](competition/tools/lean/README.md) explains how to use the official
[AC.lean definitions](competition/tools/lean/AC.lean); using Lean is optional.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `competition/` | **The IGP24-aligned public tree**: `rules/`, `problems/` (problem statements), `examples/` (training data and submissions), `tools/verifier/` (Discovery verifier and its `data/`), `tools/lean/` (optional Proof tools); generated `competition.yaml` is added during export | yes — exported by `build/release.py`, excluding caches and build products |
| `spec/` | Internal design doc (`DESIGN.md`) | no |
| `build/` | Maintained release state, dataset builders, problem and example generators, release checks and export tools | no |
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
# regenerate or check problem statements from the committed verifier manifest
# (no private dataset inputs are needed)
python3 build/build_problems.py
python3 build/build_problems.py --check

# regenerate data from the SAIR dataset release and synchronize release metadata
python3 build/sync_dataset.py --release ../sair_dataset/release
python3 build/build_manifest_v2.py

# regenerate the successful training example and its expected receipt
python3 build/build_examples.py

# full test suite (verifier + data + scoring)
python3 -m unittest discover -s tests -t .
(cd server && python3 -m unittest discover -s tests)

# build the official Proof Track statements (optional; first-use setup: competition/tools/lean/README.md)
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

Release metadata is maintained in `build/competition_state.json`.
`competition/competition.yaml` is generated, ignored by Git, and not required
for submissions or local verification. `build/release.py` generates fresh
metadata directly into the export, even if a local YAML file is missing or
stale. To generate an optional local copy without rebuilding the dataset:

```sh
python3 build/build_manifest_v2.py --metadata-only
```

Do not edit the generated YAML as a source of configuration. Current `status` is
`prelaunch`; `submissions_open` is `2026-09-11T16:00:00Z`.
`freeze_date`, `freeze_commit`, `registration_opens`, `prove_submissions_open`,
and `submission_deadline` remain `null`. This records submission-release
readiness; it does not close registration.
Calendar dates are recorded separately in `announced_dates`:
registration September 8, Discovery September 11, Proof September 20,
and the deadline November 30, 2026. `submissions_open` supplies Discovery UTC opening and
`prove_submissions_open` supplies Proof UTC opening; each track exposes its
relevant `opens_at`. `build/build_manifest_v2.py` synchronizes the manifest
and `competition.yaml` from that state and also generates the problem statements.

Before an official release:

1. Set the approved schedule and freeze date in the maintained state,
   then run `python3 build/build_manifest_v2.py`.
2. Freeze `manifest.json`, `move_spec.json`, and `stable_move_spec.json`
   under `competition/tools/verifier/data/` in git.
3. Record that commit as `freeze_commit` in `build/competition_state.json`.
4. Run `python3 build/release.py`; it generates the YAML automatically.

The default release command requires Discovery opening and deadline timestamps
and a verified data freeze. A later Proof opening timestamp may remain unset
for the Discovery release; it must be supplied before Proof submissions open.
It rejects incomplete Discovery metadata or an unverified git freeze; `--preview` allows local review without claiming an official
release. See `competition/examples/README.md` for the sample receipt and
the separate rejection example.
