# The Andrews–Curtis Conjecture (ACC) Challenge

Co-organized by Caltech and the SAIR Foundation, with Lucas Fagan, Sergei
Gukov, and Terence Tao.

[Registration is open on SAIR](https://competition.sair.foundation/competitions/acc).
The competition launches with **Discovery Track on September 11, 2026 at
16:00 UTC**. **Proof Track opens on September 20, 2026**. Both tracks cover
**AC** and **Stable AC**; the submission deadline is November 30, 2026.

## Competition guides

| Guide | Contents |
|---|---|
| [Overview](rules/overview.md) | Background, both tracks, dates, registration, and common competition rules |
| [Discovery Track](rules/discovery.md) | Data, moves, submission format, verifier semantics, limits, hashes, and scoring |
| [Proof Track](rules/proof.md) | Full conjecture statements, proof/disproof submissions, Lean, public versions, and community peer review |

`rules/prelaunch.md` contains the same overview for the prelaunch page.
Each track's guide contains its full rules.

## Problems

Start with [AC problems](problems/ac.json) or
[Stable AC problems](problems/stable_ac.json). Each file is a JSON array
of 10,115 entries containing only `challenge_id` and `description`.
The two files describe the AC and Stable AC versions of the same
**10,115 initial presentations**.

## Run a successful Discovery example

Each solution contains only a challenge ID and a list of moves. The
[examples guide](examples/README.md) includes a successful training submission
for both AC and Stable AC, the expected receipt, and a separate rejection example.
From the repository or unpacked public package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

Expected: exit code 0, `accepted: true`, and both `results[].ok: true`.
The [AC training file](examples/training_424.json) and
[Stable AC training file](examples/stable_training_424.json) contain the
**same 424 separate presentations**, all outside the official 10,115.
These examples are unscored; use IDs from the problem files for competition
submissions. Local verification does not register a submission on SAIR.

## Data and reference tools

| Directory | Contents |
|---|---|
| [problems/ac.json](problems/ac.json), [problems/stable_ac.json](problems/stable_ac.json) | Official problem statements: each entry contains `challenge_id` and `description` |
| [examples/](examples/README.md) | Both versions of the 424 training presentations, successful and unsuccessful submissions, and expected results |
| [tools/verifier/](tools/verifier/README.md) | Python reference verifier for Discovery, using only the standard library |
| [tools/verifier/data/](tools/verifier/data/README.md) | Replay manifest, move specifications, golden vectors, and MS-1190 reference metadata |
| [tools/lean/](tools/lean/README.md) | Official Proof Track definitions in `AC.lean`; using Lean and `Check.lean` is optional |

To check a scored submission, pass
`competition/tools/verifier/data/manifest.json` to the verifier's `--manifest`
option, as shown in the [verifier guide](tools/verifier/README.md).
Discovery verification uses Python and does not depend on Lean.

Release packages include generated `competition.yaml` metadata for track
routes and dates. This file is not tracked in Git and is not needed to run
the verifier or submit solutions.
SAIR handles registration, teams, submissions, leaderboards, and public Proof
versions and comments. This package supplies the data, rules, and reference
mathematical checks. The release metadata remains `prelaunch` until the
submission launch and data-freeze requirements are complete; it does not
indicate whether registration is open.
