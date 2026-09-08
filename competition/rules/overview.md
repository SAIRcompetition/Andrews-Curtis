# Andrews–Curtis Conjecture Challenge (ACC) — Overview

**Prelaunch preview — registration and submissions are not open.** You
can inspect the current rules and data and try the Python verifier
locally. Registration is announced for September 8, 2026, Discovery for
September 11, and Proof for September 21. The submission deadline is
November 30, 2026; its exact UTC time, opening times, and the official
data freeze remain pending.

ACC is one competition with **two tracks**, each containing **AC** and
**Stable AC** problems:

| Track | Task |
|---|---|
| **Discovery Track** | Find short verified move sequences, with separate AC and Stable AC leaderboards |
| **Proof Track** | Prove or disprove either full conjecture |

The tracks share team identities and attribution rules. A Proof result
does not automatically end Discovery.

## The mathematics

The **Andrews–Curtis conjecture** (1965) asserts that every balanced
presentation of the trivial group can be transformed into the trivial
presentation at the same rank by a sequence of elementary moves — relator inversion,
relator multiplication, and conjugation. It has been open for sixty
years; most experts expect it to be false, but no counterexample has
ever been verified.

The **stable conjecture** additionally allows adding a fresh generator
and a relator equal to it, or removing such a pair when the generator
occurs in no other relator. There is no bound on how many auxiliary
generators may be used. Ordinary AC implies Stable AC; a stable
counterexample is also an ordinary counterexample.

The [official statements](statement.md) and [Lean project](../tools/lean/README.md)
cover every positive finite rank. Discovery is a separate bounded search
benchmark on rank-two inputs.

The AC and Stable AC problems in Discovery use the same **10,115 balanced
presentations of the trivial group**. `ac-v1-00001` … `ac-v1-10115` are AC challenges; the matching
`sac-v1-` IDs have exactly the same initial relators. This gives 20,230
challenge records, with one leaderboard per move specification. The
publication freeze is pending. The pool draws on an extended Miller–Schupp
family, automorphic disguises of hard classes, and presentations solvable
by construction. It includes **all 550 Miller–Schupp instances with no
publicly known trivialization** in the MS-1190 dataset (Shehper et al. 2025;
status per Fagan et al., *The Two-Hump Problem*, ICML 2026), and excludes
instances with public replayable certificates.

The Miller–Schupp family itself is the most studied source of potential
counterexamples:

$$MS(n,w)=\langle x,y \mid x^{-1}y^n x y^{-(n+1)},\ x\,w^{-1}\rangle,
\qquad n\ge 1,\ \sigma_x(w)=0.$$

Every $MS(n,w)$ presents the trivial group; the question is whether it
is **AC-trivializable**.

**Internal per-instance difficulty, provenance, and status labels and
maps are not published.** Participants may still identify instances by
matching them against public mathematical sources. Working out which
instances are within reach is part of the task; a first trivialization
of an open instance is a new mathematical result.

> **"Unresolved" is not a verdict.** An unresolved instance is one for
> which, as of the data freeze date, no publicly available valid
> trivialization certificate is known. It does **not** mean the instance
> is a counterexample, and it does **not** mean the instance is
> unsolvable.

## Discovery Track

### AC problem

A challenge gives you an ordered pair of freely reduced words
`initial_relators = [r0, r1]` over letters `1 = x, -1 = x^-1, 2 = y,
-2 = y^-1`. Transform it into the **exact ordered target**
$T = (x, y) =$ `[[1],[2]]` using the 14 numbered operations of
`move_spec_version = "ac-r2-v1"`:

| id | Effect | Inverse | id | Effect | Inverse |
|---:|---|---:|---:|---|---:|
| 0 | $r_0 \leftarrow r_0^{-1}$ | 0 | 7 | $r_0 \leftarrow x^{-1} r_0 x$ | 6 |
| 1 | $r_1 \leftarrow r_1^{-1}$ | 1 | 8 | $r_0 \leftarrow y r_0 y^{-1}$ | 9 |
| 2 | $r_0 \leftarrow r_0 r_1$ | 3 | 9 | $r_0 \leftarrow y^{-1} r_0 y$ | 8 |
| 3 | $r_0 \leftarrow r_0 r_1^{-1}$ | 2 | 10 | $r_1 \leftarrow x r_1 x^{-1}$ | 11 |
| 4 | $r_1 \leftarrow r_1 r_0$ | 5 | 11 | $r_1 \leftarrow x^{-1} r_1 x$ | 10 |
| 5 | $r_1 \leftarrow r_1 r_0^{-1}$ | 4 | 12 | $r_1 \leftarrow y r_1 y^{-1}$ | 13 |
| 6 | $r_0 \leftarrow x r_0 x^{-1}$ | 7 | 13 | $r_1 \leftarrow y^{-1} r_1 y$ | 12 |

These IDs encode 2 inversions, 4 right multiplications by the other relator
or its inverse, and 8 conjugations by a generator letter or its inverse.
They instantiate the three ordinary AC operation types at rank 2.

Words are freely reduced after every move. The move set is closed under
inversion, so reachability is symmetric.

**The endpoint must be exactly `[[1],[2]]`, in order.** Ending at
$(y,x)$ or $(x^{-1},y)$ does not count — but this costs at most **5**
extra moves from any "loose trivial" state. The exhaustively verified
shortest suffixes (also machine-readable in `challenges/move_spec.json`,
`canonicalization_table`) are:

| Final state | Moves to $T$ | One shortest path (move ids) |
|---|---:|---|
| $(x,y)$ | 0 | — |
| $(x,y^{-1})$ | 1 | `[1]` |
| $(x^{-1},y)$ | 1 | `[0]` |
| $(x^{-1},y^{-1})$ | 2 | `[0,1]` |
| $(y^{-1},x)$ | 4 | `[2,5,2,8]` |
| $(y,x^{-1})$ | 4 | `[3,4,3,10]` |
| $(y^{-1},x^{-1})$ | 4 | `[2,0,4,3]` |
| $(y,x)$ | 5 | `[0,2,5,2,8]` |

No extra theory is needed — append the matching suffix and you are done.

### Stable AC problem

The matching `sac-v1-` challenge starts at the same rank-two presentation.
Its target is the **empty presentation** `[]`. States have $0\le k\le8$
generators and the same number of relators. The `sac-r8-v1` encoding has
257 operation IDs covering ranks up to 8, listed in
`challenges/stable_move_spec.json`:

| IDs | Operation |
|---|---|
| 0–13 | The original AC block, unchanged |
| 14 | Add a fresh generator and its singleton relator |
| 15–22 | Delete the selected singleton positive relator and its generator, if absent elsewhere; renumber the remaining generators |
| 23–28 | Inversion on the remaining relator indices |
| 29–136 | Remaining right multiplications by another relator or its inverse |
| 137–256 | Remaining conjugations by generator letters or their inverses |

The table contains 8 inversion, 112 multiplication, 128 conjugation,
1 stabilization, and 8 destabilization entries. The 257 IDs are not all
applicable at every state: moves must name existing relators and generators.
Stabilization at rank 8 and invalid deletions fail with
`E_MOVE_NOT_APPLICABLE`; nothing is skipped.
The rank cap restricts the benchmark, not the mathematical stable conjecture.
See [evaluation.md](evaluation.md) §1.2 for exact semantics.

From either `(x,y)` or `(y,x)`, `[16,15]` reaches `[]`. In general, invert
the negative entries of a signed basis tuple, then destabilize from the
highest relator index down. Appending `[16,15]` to an AC solution gives a
stable path; acceptance requires room for two more moves and one more work
unit under the same limits. Submit it under the `sac-v1-` ID to earn stable
points; points are never transferred automatically.

### Warm-up data

`challenges/training_424.json` contains 424 solved AC presentations and
`stable_training_424.json` contains the same instances with certificates
extended by `[16,15]`. These 424 presentations are **outside both scored
problem sets**. The runnable example exercises both specifications.

### Submitting

The format below is the successful **training example**, which uses
`examples/training_manifest.json` rather than the scored competition
manifest:

```json
{
  "solutions": [
    { "challenge_id": "ms-train-0160", "moves": [6, 4, 2, 9, 1, 4, 1] },
    { "challenge_id": "sac-train-0160", "moves": [6, 4, 2, 9, 1, 4, 1, 16, 15] }
  ]
}
```

Run it from the repository or exported package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

This example earns no competition points and is not valid against the
scored manifest. The [examples guide](../examples/README.md) provides
the complete expected receipt and a separate rejection example. For
the competition, use the `challenge_id` of a scored pool instance and
the moves that solve it; online submission will open on the announced
date.

Each solution contains only `challenge_id` and `moves`. Its challenge
selects the specification; a batch may contain solutions to both problems. You may also
include optional top-level `method` (a method name) and `notes` (free
text, at most 2000 characters). The verifier reads the move-spec version
from the supplied challenge, verifies deterministically, and computes
length itself; any client-asserted result field (`length`,
`score`, `final_state`, …) rejects the whole submission. Limits (path
length 100 000, total relator length 10 000, work budget 5 000 000) and
the full error-code contract are in [evaluation.md](evaluation.md). A
downloadable reference verifier lets you self-check now; the planned
competition service will use the same Python sources.

### Scoring

Discovery has **separate AC and Stable AC scores and rankings**, with no
combined leaderboard. Upload quotas cover both problems together.

Each challenge $i$ has a base score $V_i$ (v1: all $V_i = 1$). Let
$L^\star_i$ be the shortest accepted path across all teams and $k_i$
the number of teams currently at $L^\star_i$. Teams at the optimum
share $P_{t,i} = V_i\,2^{1-k_i}$; everyone else scores 0 on that
challenge.

Worked example ($V_i = 1$):

| Stage | A | B | C | D | $L^\star$ | $k$ | Points |
|---|---:|---:|---:|---:|---:|---:|---|
| A first solves in 40 | 40 | – | – | – | 40 | 1 | A=1 |
| B matches 40 | 40 | 40 | – | – | 40 | 2 | A=B=1/2 |
| C matches 40 | 40 | 40 | 40 | – | 40 | 3 | each 1/4 |
| D finds **38** | 40 | 40 | 40 | 38 | 38 | 1 | **D=1, A/B/C drop to 0** |
| A matches 38 | 38 | 40 | 40 | 38 | 38 | 2 | A=D=1/2 |

The rule is hard by design: a new strictly-shorter path zeroes everyone
else instantly, maximizing the incentive to keep optimizing.

> **The leaderboard length is a record, not a theorem.** The current
> best-known atomic path is the shortest path among valid competition
> submissions to date. This is **not** a mathematically proven shortest
> path.

**First Solver** is the accepted solution with the earliest server
receipt, with submission ID breaking ties. A later, shorter solution
does not take this honor away. Delayed validation of an earlier receipt
may correct a provisional display; the honor does not guarantee points.
First Solver is recorded separately for each problem.
See [evaluation.md](evaluation.md) §6.

During Discovery Track, path length, peak relator length, certificate
hash, and the result fields listed in [evaluation.md](evaluation.md) §7
are public; move sequences remain private. Your `certificate_hash`
lets you claim a result publicly (e.g.
in a preprint) without revealing the path; all valid certificates are
published openly after the competition, forming a new public benchmark.

**Bridge certificates**: a verified path from one challenge's initial
state to another's is a real, machine-checked mathematical fact. It is
registered and displayed (length, team, hash) but scores no points.
Both endpoints must use the same move specification.
If a bridge is composed into a valid submitted trivialization, that
full solution is scored normally for the challenge it solves, using
its full move length.

## Proof Track

The AC and Stable AC problems each accept **proofs and disproofs** of their
[official statement](statement.md).
A proof must cover all positive finite ranks. A disproof must establish the
selected conjecture's negation. It may exhibit a concrete counterexample or
prove that one exists without explicitly identifying it. Such a presentation
must define the trivial group and admit no path under the full unbounded
relation of that conjecture. Ordinary AC keeps the rank fixed; Stable AC
allows stabilization and destabilization with no rank cap. A counterexample
may lie outside the Discovery pool.

An AC proof also settles Stable AC. A Stable AC disproof also settles AC.
The reverse implications are not assumed: an ordinary counterexample may
still have a stable trivialization.

**Planned submission after opening.** Select `conjecture: ac` or
`stable_ac`, set `claim_type` to `proof` or `disproof`, and
provide a description stating the claim and summarizing the argument.
The complete argument may be in the description, a paper/PDF, Lean
material at a fixed GitHub commit, an identified arXiv version, or a
combination of these. A PDF is optional. Without supporting material,
the description itself must contain the complete substantive argument.

**Public versions and discussion.** The planned platform will publish
all Proof submission versions and comments by default. Each version
will receive a server timestamp and a monotonically increasing ID;
revisions will create new versions rather than overwrite old ones.
Supporting links will identify the fixed commit or document version
being submitted. Comments and review decisions will identify the
submission version they address.

Community peer review drives discussion and progress. Participants are
encouraged to examine arguments, identify gaps, suggest corrections, and
build on one another's work. Organizers may assess selected claims for
competition recognition; submission does not create an obligation for
organizers or designated reviewers to assess every claim. Any recognition
decision identifies a specific version and preserves the public reasoning
and history. Lean formalizations are also open to peer review of the claim,
its scope, and its trust boundary.
Formal targets are `AC.Conjecture` or `AC.StableConjecture` for a proof,
and their negations for a disproof (equivalently `AC.Counterexample` or
`AC.StableCounterexample`). The
[Lean guide](../tools/lean/README.md) builds `AC`; `lake build Check`
is optional and is not a submission requirement.

**Priority and credit.** Priority belongs to the earliest version that
review confirms contains a complete, correct argument, ordered by
server timestamp and then ID. Closing a substantive gap uses the new
valid version's time; editorial revisions do not erase an already
valid version's priority. Cite any submission, version, or comment you
build on, and explain the contribution. Only later work confirmed to
be independent is called `Independent Confirmation`; contribution
percentages are not assigned automatically.

> **Not finding a path is not a disproof.** Failure to find a
> trivialization — under any compute budget, length bound, peak bound,
> or restricted move set — does **not** establish a counterexample.

For each conjecture, the first accepted proof or disproof under this
priority rule receives the **Highest Mathematical Achievement of the Competition** honor.
Proof results do not earn Discovery points and do not automatically
end Discovery Track. A qualifying AC proof or Stable AC disproof
is recognized for both conjectures using the same version and receipt time.
Submission fields, community review, public records,
and the full priority and credit rules are in
[evaluation.md](evaluation.md) §9. Both tracks remain closed during
prelaunch.

## Team Participation and Anti-Cheating Policy

- Each individual or organization can participate in only one team.
- Teams must register members and sponsors in advance.
- If coordinated cheating is detected (including sockpuppet teams), all related teams will be disqualified.

## Collaboration and attribution

Public learning and cross-team discussion with stated contributions are
welcome. Sharing a specific Discovery certificate across teams is joint
work and must not be resubmitted for independent credit or scoring.
The organizers may request provenance for any submission.

## Community feedback

Questions about the rules, scoring, or evaluation are welcome. Join the
[SAIR Foundation Zulip community](https://zulip.sair.foundation/) for
discussion and collaboration.

## Co-organizers

ACC is co-organized by (in alphabetical order by surname):

* Lucas Fagan
* Sergei Gukov
* Terence Tao

ACC is run by the [SAIR Foundation](https://sair.foundation/) in
collaboration with [Caltech](https://www.caltech.edu/).

<!-- logo URLs: re-host under /competition-assets/acms/ at site onboarding -->
[<img src="https://competition.sair.foundation/competition-assets/lean-kernel-challenge/sair-foundation-logo.png" alt="SAIR Foundation logo" width="200">](https://sair.foundation/)
[<img src="https://www.caltech.edu/static/core/img/caltech-new-logo.png" alt="Caltech logo" width="200">](https://www.caltech.edu/)

## Timeline

* Registration and team formation: September 8, 2026.
* Discovery Track: September 11, 2026.
* Proof Track: September 21, 2026.
* Submission deadline: November 30, 2026; exact UTC time to be announced.
* Certificate release: to be announced.

These calendar dates are recorded in `competition.yaml` under
`announced_dates`. Exact UTC opening times, deadline time, release time,
`freeze_date`, and `freeze_commit` remain `null`; status is `prelaunch`.
`submissions_open` records Discovery's UTC start and `prove_submissions_open`
Proof's; each track's `opens_at` uses the relevant field.
The official schedule and verified freeze must be complete before formal
release and online submissions open.
