# ACMS: Andrews–Curtis, Miller–Schupp Phase — Overview

## The mathematics

The **Andrews–Curtis conjecture** (1965) asserts that every balanced
presentation of the trivial group can be transformed into the trivial
presentation by a sequence of elementary moves — relator inversion,
relator multiplication, and conjugation. It is open; most experts
expect it to be false, but no counterexample has ever been verified.

This competition works on the **Miller–Schupp family**, the most
studied source of potential counterexamples:

$$MS(n,w)=\langle x,y \mid x^{-1}y^n x y^{-(n+1)},\ x\,w^{-1} \rangle,
\qquad n\ge 1,\ \sigma_x(w)=0.$$

Every $MS(n,w)$ presents the trivial group. The question is whether it
is **AC-trivializable**. From the MS-1190 dataset (Shehper et al. 2025;
status per Fagan et al., *The Two-Hump Problem*, ICML 2026), the
challenge pool consists of the **550 instances with no publicly known
replayable trivialization** as of the freeze date. Solving any one of
them is a new mathematical result.

1. > "Unresolved" means only: as of the data freeze date, no publicly available
   > valid trivialization certificate is known. It does **not** mean the instance
   > is a counterexample, and it does **not** mean the instance is unsolvable.

## The task

A challenge gives you an ordered pair of freely reduced words
`initial_relators = [r0, r1]` over letters `1 = x, -1 = x^-1, 2 = y,
-2 = y^-1`. Transform it into the **exact ordered target**
$T = (x, y) =$ `[[1],[2]]` using the 14 frozen atomic moves of
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

Words are freely reduced after every move. The move set is closed under
inversion, so reachability is symmetric.

**The endpoint must be exactly `[[1],[2]]`, in order.** Ending at
$(y,x)$ or $(x^{-1},y)$ does not count — but this costs at most **5**
extra moves from any "loose trivial" state. The exhaustively verified
shortest suffixes (also machine-readable in `move_spec.json`,
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

## Submitting

```json
{
  "method": "optional method name",
  "notes": "optional free text, <= 2000 chars",
  "solutions": [
    { "challenge_id": "ms-v1-0001", "move_spec_version": "ac-r2-v1",
      "moves": [0, 4, 8, 3] }
  ]
}
```

Submit only the moves. The server verifies deterministically and
computes length itself; any client-asserted result field (`length`,
`score`, `final_state`, …) rejects the whole submission. Limits (path
length 100 000, total relator length 10 000, work budget 5 000 000) and
the full error-code contract are in [evaluation.md](evaluation.md). A
downloadable reference verifier — the same Python sources the server
runs — lets you check everything before submitting.

## Scoring

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

2. > Current best-known atomic path — the shortest path among valid competition
   > submissions to date. This is **not** a mathematically proven shortest path.

**First Solver** is a permanent honor recorded the moment a challenge
is first solved; it never changes afterwards, and does not guarantee
continued points.

During the competition, only path **lengths** are public — never the
moves. Your `certificate_hash` lets you claim a result publicly (e.g.
in a preprint) without revealing the path; all valid certificates are
published openly after the competition, forming a new public benchmark.

**Bridge certificates**: a verified path from one challenge's initial
state to another's is a real, machine-checked mathematical fact. It is
registered and displayed (length, team, hash) but scores no points, and
a bridge-derived solution is necessarily longer than a direct one — the
shortest-path rule keeps bridges honor, not arbitrage.

## The counterexample track

Prove in Lean 4 — in a frozen, offline-buildable environment — that
some pool challenge presents the trivial group but is **not** reachable
from the trivial presentation under the full, unbounded, non-stable AC
relation. The competition library provides the frozen definitions and
the compatibility theorem `ac_iff_atomic` tying the 14-move closure to
standard AC moves.

3. > A verified counterexample is a Lean proof, checked in the frozen environment
   > with an audited axiom set, that the presentation presents the trivial group
   > and is **not** related to the trivial presentation by the full, unbounded,
   > non-stable Andrews–Curtis relation. Failure to find a path — under any
   > budget, length bound, peak bound, or restricted move set — is not a counterexample.

The first submission passing full verification is honored as the
**Highest Mathematical Achievement of the Competition**, displayed
above the leaderboard; it does not convert into leaderboard points.
Technical requirements (allowed axioms, CI gates, review process) are
in [evaluation.md](evaluation.md).

## Teams and integrity

One person, one team; team size unlimited; members may join during the
competition with organizer approval. **Teams may not merge after either
has submitted.** Sharing a specific certificate across teams is joint
work and must not be resubmitted as independent; coordinated cheating
(including sockpuppets) disqualifies all involved teams. The organizers
may request provenance for any submission.

## Timeline

The freeze date, competition window, and post-competition certificate
release date will be announced (decision D-9, pending). The frozen
data carries the freeze date in `manifest.json`, `challenges/README.md`
and `competition.yaml`.
