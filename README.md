# The Andrews–Curtis Conjecture (ACC) Challenge

The **Discovery Track is live** on
[SAIR](https://competition.sair.foundation/competitions/acc).
**Proof Track opens before September 20, 2026**. The
submission deadline is November 30, 2026 AoE.

The ACC Challenge is co-organized by Caltech and the SAIR Foundation, with
Lucas Fagan, Sergei Gukov, and Terence Tao. It has **two tracks**, each
covering **AC** and **Stable AC**:

| Guide | Contents |
|---|---|
| [Overview](competition/rules/overview.md) | Background, tracks, dates, registration, and common rules |
| [Discovery Track](competition/rules/discovery.md) | Problems, moves, TXT submissions, local tests, and separate AC/Stable AC scoring |
| [Proof Track](competition/rules/proof.md) | Research directions, submissions, optional materials, and sharing with credit |

Discovery works with explicit finite move sequences. Proof welcomes ideas,
partial results, and full proofs or disproofs. Choose AC or Stable AC and a
proof or disproof direction, then describe your work. Participation is
voluntary; submitting requires agreeing to share. Every Proof submission is
automatically published in the SAIR Contributor Network for others to use
and build on with credit.

SAIR hosts registration, teams, submissions, and leaderboards. This
repository provides the competition rules, problems, examples,
Discovery verifier, and optional Lean definitions for Proof Track.

## Discovery Track resources

The two problem files contain the AC and Stable AC versions of the **same
10,115 initial presentations**. Each uses JSON Lines: one JSON object per
line, containing only `challenge_id` and `description` of the initial presentation.

| File or guide | Contents |
|---|---|
| [AC problems](competition/problems/ac.jsonl) | 10,115 AC problem statements |
| [Stable AC problems](competition/problems/stable_ac.jsonl) | 10,115 Stable AC problem statements |
| [Examples](competition/examples/README.md) | 424 unscored training presentations in JSONL, known move sequences, runnable submissions, and receipts |
| [Discovery verifier](competition/tools/verifier/README.md) | [Discovery Track](competition/rules/discovery.md) replay commands and supporting [data](competition/tools/verifier/data/README.md) |

The 424 training presentations are outside the scored pool. The verifier
reads `competition/tools/verifier/data/manifest.json` to check submissions.

## Proof Track resources

The [Proof Track guide](competition/rules/proof.md) describes the conjectures,
submissions, optional supporting links, and sharing and credit. The
[Lean guide](competition/tools/lean/README.md) explains how to use the official
[AC.lean definitions](competition/tools/lean/AC.lean); using Lean is optional.

## Quick test

Run the successful, unscored training submission from the repository root:

```sh
PYTHONPATH=competition/tools python3 -m verifier \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.txt --pretty
```

Both paths should return `ok: true`. See the
[examples guide](competition/examples/README.md) for the expected receipt
and the [verifier guide](competition/tools/verifier/README.md) for checking
official submissions.

## License

Copyright 2026 sairmath.

Licensed under [Apache 2.0](LICENSE).

MS-1190 presentation set: Shehper et al. 2025; instance status per
Fagan et al., "The Two-Hump Problem", ICML 2026.
