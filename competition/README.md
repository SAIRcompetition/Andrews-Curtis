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
These training examples are unscored; use official challenge IDs for competition
submissions. Local verification does not register a submission on SAIR.

## Data and reference tools

| Directory | Contents |
|---|---|
| [challenges/](challenges/README.md) | 10,115 presentations for each Discovery problem, separate AC and Stable AC challenge records, and 424 unscored training presentations |
| [examples/](examples/README.md) | Successful and unsuccessful submissions with expected results |
| [tools/verifier/](tools/verifier/README.md) | Python reference verifier for Discovery, using only the standard library |
| [tools/lean/](tools/lean/README.md) | The full AC and Stable AC conjectures in `AC.lean`; `Check.lean` is optional |

Release packages include generated `competition.yaml` metadata for track
routes and dates. This file is not tracked in Git and is not needed to run
the verifier or submit solutions.
SAIR handles registration, teams, submissions, leaderboards, and public Proof
versions and comments. This package supplies the data, rules, and reference
mathematical checks. The release metadata remains `prelaunch` until the
submission launch and data-freeze requirements are complete; it does not
indicate whether registration is open.
