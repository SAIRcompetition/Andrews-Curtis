# ACC: The Andrews–Curtis Conjecture Competition — Overview

## The mathematics

The **Andrews–Curtis conjecture** (1965) asserts that every balanced
presentation of the trivial group can be transformed into the trivial
presentation by a sequence of elementary moves — relator inversion,
relator multiplication, and conjugation. It has been open for sixty
years; most experts expect it to be false, but no counterexample has
ever been verified.

The competition runs on a **frozen pool of 10,115 balanced
presentations of the trivial group**, `ac-v1-00001` … `ac-v1-10115`,
spanning warm-up exercises to the research frontier. The pool draws on
an extended Miller–Schupp family, on automorphic disguises of known
hard classes, and on presentations that are solvable by construction.
It includes **all 550 Miller–Schupp instances with no publicly known
trivialization** — the MS-1190 dataset (Shehper et al. 2025; status per
Fagan et al., *The Two-Hump Problem*, ICML 2026) — and excludes from
scoring every instance whose trivialization is already publicly known.

The Miller–Schupp family itself is the most studied source of potential
counterexamples:

$$MS(n,w)=\langle x,y \mid x^{-1}y^n x y^{-(n+1)},\ x\,w^{-1}\rangle,
\qquad n\ge 1,\ \sigma_x(w)=0.$$

Every $MS(n,w)$ presents the trivial group; the question is whether it
is **AC-trivializable**.

**Per-instance difficulty, provenance, and status are deliberately
withheld.** Working out which instances are within reach is part of the
game. Many of them are open problems: for those, a first trivialization
is a new mathematical result — which ones they are is not disclosed.

> **"Unresolved" is not a verdict.** An unresolved instance is one for
> which, as of the data freeze date, no publicly available valid
> trivialization certificate is known. It does **not** mean the instance
> is a counterexample, and it does **not** mean the instance is
> unsolvable.

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

**Warm-up data.** `challenges/training_424.json` publishes 424 solved
Miller–Schupp instances with full atomic-move certificates, in exactly
the frozen encoding. It is training material: replay it to validate a
pipeline, or mine it for search heuristics. Those instances are **not**
in the scored pool.

## Submitting

```json
{
  "method": "optional method name",
  "notes": "optional free text, <= 2000 chars",
  "solutions": [
    { "challenge_id": "ac-v1-00001", "move_spec_version": "ac-r2-v1",
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

> **The leaderboard length is a record, not a theorem.** The current
> best-known atomic path is the shortest path among valid competition
> submissions to date. This is **not** a mathematically proven shortest
> path.

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

A disproof of the Andrews–Curtis conjecture is not a search log. It is
a **self-contained mathematical argument** that some balanced
presentation of the trivial group is **not** related to the trivial
presentation by the full, unbounded, non-stable Andrews–Curtis
relation.

**Official channel: PDF plus expert review.** Upload the argument as a
single self-contained PDF through the competition site. A claim moves
through *received* → *screening* → *under expert review* → *accepted*,
*rejected*, or *revision requested*; review is carried out by the
organizer panel together with reviewers they designate. There is no
guaranteed turnaround. The organizers may summarily decline
submissions that carry no substantive new mathematical content, and a
team may have **at most one active claim at a time** — a new upload
replaces the pending one.

**Lean 4 fast track (optional).** A claim accompanied by, or later
formalized as, a machine-checked Lean 4 proof that builds in the
competition's frozen offline environment is fast-tracked and, on
passing verification, settles the claim. The competition Lean library
is in development: when published it will provide frozen definitions of
the full, unbounded, non-stable AC relation together with a
compatibility theorem tying the 14-move closure to the standard AC
moves. Until the library is published there is nothing to build
against, so the PDF channel is the only route open.

> **Not finding a path is not a disproof.** Failure to find a
> trivialization — under any compute budget, length bound, peak bound,
> or restricted move set — is **not** a counterexample.

Explicitly **not** a counterexample:

* no path found within a fixed compute budget;
* nonexistence of paths of length $\le N$;
* nonexistence of paths of peak total relator length $\le B$;
* unreachability in the substitution graph or any restricted move set;
* unreachability under *stable* AC (which allows adding and removing
  trivial relators).

The first accepted disproof is honored as the **Highest Mathematical
Achievement of the Competition**, displayed above the leaderboard; it
does not convert into leaderboard points. The submission mechanics,
review states, and Lean requirements are in
[evaluation.md](evaluation.md) §9.

## Teams and integrity

One person, one team; team size unlimited; members may join during the
competition with organizer approval. **Teams may not merge after either
has submitted.** Sharing a specific certificate across teams is joint
work and must not be resubmitted as independent; coordinated cheating
(including sockpuppets) disqualifies all involved teams. The organizers
may request provenance for any submission.

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

* Registration opens: —
* Submissions open: —
* Submission deadline: —
* Certificate release (post-competition): —

The freeze date, competition window, and post-competition certificate
release date will be announced. The frozen data carries the freeze date
in `challenges/manifest.json`, `challenges/README.md` and
`competition.yaml`.
