# The Andrews–Curtis Conjecture (ACC) Challenge

Co-organized by Caltech and the SAIR Foundation, with Lucas Fagan, Sergei
Gukov, and Terence Tao.

The **Discovery Track is live** on
[SAIR](https://competition.sair.foundation/competitions/acc).
**Proof Track opens before September 20, 2026**. Both tracks cover
**AC** and **Stable AC**; the submission deadline is November 30, 2026 AoE.

## Competition guides

| Guide | Contents |
|---|---|
| [Overview](rules/overview.md) | Background, both tracks, dates, registration, and common competition rules |
| [Discovery Track](rules/discovery.md) | Problems, moves, TXT submissions, local tests, and scoring |
| [Proof Track](rules/proof.md) | Research directions, submissions, optional materials, and sharing with credit |

Start with the guide for your track.

## Discovery Track resources

Follow the [Discovery Track guide](rules/discovery.md) for moves, submission
instructions, local verification, and scoring.

| Resource | Contents |
|---|---|
| [AC problems](problems/ac.jsonl) | 10,115 problem IDs and descriptions |
| [Stable AC problems](problems/stable_ac.jsonl) | The matching 10,115 Stable AC problem IDs and initial presentations |
| [Training data and examples](examples/README.md) | 424 unscored presentations in JSONL, known move sequences, runnable submissions, and expected receipts |
| [Python verifier](tools/verifier/README.md) | Local verification instructions |
| [Verifier data](tools/verifier/data/README.md) | Manifest, move specifications, and conformance vectors |

Both problem files use JSON Lines, with one object per line containing
only `challenge_id` and `description` of the initial presentation.
Submit solutions as a [TXT file](rules/discovery.md#submit),
one `challenge_id: [moves]` line per solution, with optional `#` comments.

## Proof Track resources

Proof Track welcomes ideas, partial results, and full proofs or disproofs.
Choose AC or Stable AC and a proof or disproof direction, and provide a
description. A public GitHub repository containing Lean 4 formalization and
arXiv or paper links are optional. See the [Proof Track guide](rules/proof.md).

Participation is voluntary. You must check the box agreeing to share before
submitting. Every Proof submission is automatically published in the SAIR
Contributor Network, where others can use and build on it with credit.

| Resource | Contents |
|---|---|
| [AC.lean](tools/lean/AC.lean) | Official definitions of AC and Stable AC |
| [Lean guide](tools/lean/README.md) | Instructions for working with the formal definitions; using Lean is optional |
| [Check.lean](tools/lean/Check.lean) | Optional checks and semantic examples |

SAIR handles registration, teams, submissions, leaderboards, and published
Proof contributions. This repository supplies the data, rules, and reference
mathematical checks.
