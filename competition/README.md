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

[Prelaunch](rules/prelaunch.md) contains the same overview for the prelaunch page.
Each track's guide contains its full rules.

## Discovery Track resources

Follow the [Discovery Track guide](rules/discovery.md) for moves, submission
instructions, local verification, and scoring.

| Resource | Contents |
|---|---|
| [AC problems](problems/ac.jsonl) | 10,115 problem IDs and descriptions |
| [Stable AC problems](problems/stable_ac.jsonl) | The matching 10,115 Stable AC problem IDs and initial presentations |
| [Training data and examples](examples/README.md) | 424 separate, unscored presentations, runnable submissions, and expected receipts |
| [Python verifier](tools/verifier/README.md) | Local verification instructions |
| [Verifier data](tools/verifier/data/README.md) | Manifest, move specifications, and conformance vectors |

Both problem files use JSON Lines, with one object per line containing
only `challenge_id` and `description` of the initial presentation.

## Proof Track resources

Follow the [Proof Track guide](rules/proof.md) for the full conjecture
statements, submission materials, public versions, and community peer review.

| Resource | Contents |
|---|---|
| [AC.lean](tools/lean/AC.lean) | Official definitions of AC and Stable AC |
| [Lean guide](tools/lean/README.md) | Instructions for working with the formal definitions; using Lean is optional |
| [Check.lean](tools/lean/Check.lean) | Optional checks and semantic examples |

Release packages include generated `competition.yaml` metadata for track
routes and dates. This file is not tracked in Git and is not needed to run
the verifier or submit solutions.
SAIR handles registration, teams, submissions, leaderboards, and public Proof
versions and comments. This package supplies the data, rules, and reference
mathematical checks. The release metadata remains `prelaunch` until the
submission launch and data-freeze requirements are complete; it does not
indicate whether registration is open.
