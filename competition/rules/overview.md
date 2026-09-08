# ACC: The Andrews–Curtis Conjecture Competition — Overview

## The mathematics

The **Andrews–Curtis conjecture** (1965) asserts that every balanced
presentation of the trivial group can be transformed into the trivial
presentation by a sequence of elementary moves — relator inversion,
relator multiplication, and conjugation. It has been open for sixty
years; most experts expect it to be false, but no counterexample has
ever been verified.

The **stable Andrews–Curtis conjecture** asserts the same, for the
larger move set that additionally allows adding a new generator
together with a relator equal to it, and removing such a pair. It is
the weaker of the two statements — a proof of the Andrews–Curtis
conjecture proves it — and it is connected to open questions in
four-dimensional topology.

The competition runs on a **frozen pool of 10,115 balanced
presentations of the trivial group**, spanning warm-up exercises to the
research frontier. The pool draws on an extended Miller–Schupp family,
on automorphic disguises of known hard classes, and on presentations
that are solvable by construction. It includes **all 550 Miller–Schupp
instances with no publicly known trivialization** — the MS-1190 dataset
(Shehper et al. 2025; status per Fagan et al., *The Two-Hump Problem*,
ICML 2026) — and excludes from scoring every instance whose
trivialization is already publicly known.

**The same 10,115 presentations are used in both trivialization
tracks**: `ac-v1-00001` … `ac-v1-10115` are the Andrews–Curtis
challenges, `sac-v1-00001` … `sac-v1-10115` the stable ones, and
`sac-v1-N` is the same presentation as `ac-v1-N`.

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

There are four tracks: two trivialization tracks, scored on
leaderboards, and two proof-or-disproof tracks, reviewed by experts.
The trivialization tracks share the pool and the verifier and differ
only in the move specification and the terminal state; the challenge id
prefix selects the track.

### Track 1 — AC trivialization (`ac-r2-v1`)

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

### Track 2 — stable AC trivialization (`sac-r8-v1`)

Challenge `sac-v1-N` is **the same presentation** as `ac-v1-N`: the
same two initial relators, byte for byte. What changes is the move set
and the destination.

A state is an ordered list of $k$ freely reduced relators over the
generators $1,\dots,k$ (letters $\pm 1,\dots,\pm k$; $x = 1$, $y = 2$,
and the extra generators are written $g_3,\dots,g_8$), with
$0 \le k \le 8$. Every challenge starts at $k = 2$. The **target is the
empty presentation** $\langle\ \mid\ \rangle =$ `[]`: destabilize
everything away.

The 257 frozen moves of `move_spec_version = "sac-r8-v1"` are numbered
`0`–`256`. A move's meaning does not depend on the current rank; its
applicability is checked at replay time.

| ids | Category | Count | Effect |
|---|---|---:|---|
| 0–13 | the `ac-r2-v1` block | 14 | exactly the 14 moves of the table above — same ids, same rows, same inverses |
| 14 | stabilize | 1 | $k \to k+1$: append the generator $k+1$ and the relator `[k+1]`. Not applicable at $k = 8$ |
| 15–22 | destabilize relator $i$ ($i = 0,\dots,7$) | 8 | applicable **iff** relator $i$ is exactly the single positive letter $g$ and $g$ occurs in no other relator; deletes relator $i$ and generator $g$, renumbering every generator above $g$ down by one. $k \to k-1$ |
| 23–28 | inversion of relator $i$ ($i = 2,\dots,7$) | 6 | $r_i \leftarrow r_i^{-1}$ (the two rank-2 cases are ids 0–1) |
| 29–136 | multiplication $r_i \leftarrow r_i r_j^{\pm 1}$, $i \ne j < 8$ | 108 | the four rank-2 cases are ids 2–5 |
| 137–256 | conjugation $r_i \leftarrow c\,r_i\,c^{-1}$, $c = g^{\pm 1}$, $i < 8$, $g \le 8$ | 120 | the eight rank-2 cases are ids 6–13 |

So id 14 stabilizes, id 15 destabilizes relator 0, id 16 destabilizes
relator 1, id 23 inverts relator 2. The **full 257-row table, with a
description of every id, is machine-readable in
`challenges/stable_move_spec.json`** (`max_rank: 8`;
`move_spec_hash` covers the `moves` array). Do not guess ids from the
categories above — read them from that file.

A move whose relator index or generator is beyond the current rank, a
stabilization at $k = 8$, or a destabilization whose precondition fails
is rejected with `E_MOVE_NOT_APPLICABLE` at that move index; nothing is
"skipped". Words are freely reduced after every move. Inversion,
multiplication and conjugation are closed under inversion exactly as in
track 1; stabilization and destabilization undo each other only up to
renumbering, so neither carries a fixed inverse id — but reachability
is again symmetric.

**Finishing is cheap and symmetric.** From any state whose $k$ relators
are the $k$ generators as single letters, each occurring once and
possibly inverted, the shortest finish is
$k + (\text{number of inverted letters})$ moves: invert the inverted
ones, then destabilize from the highest relator index down to 0. The
rank-2 rows (exhaustively verified, and machine-readable in
`challenges/stable_move_spec.json`, `canonicalization_table`) are:

| Final state | Moves to `[]` | One shortest path (move ids) |
|---|---:|---|
| $(x,y)$ | 2 | `[16,15]` |
| $(y,x)$ | 2 | `[16,15]` |
| $(x,y^{-1})$ | 3 | `[1,16,15]` |
| $(x^{-1},y)$ | 3 | `[0,16,15]` |
| $(y^{-1},x)$ | 3 | `[0,16,15]` |
| $(y,x^{-1})$ | 3 | `[1,16,15]` |
| $(x^{-1},y^{-1})$ | 4 | `[0,1,16,15]` |
| $(y^{-1},x^{-1})$ | 4 | `[0,1,16,15]` |

There is no ordering asymmetry: $(x,y)$ and $(y,x)$ cost the same. That
is the reason the terminal state of this track is the empty
presentation rather than a fixed ordered tuple — the exact-order rule
of track 1 has no natural analogue once the rank can change.

In particular, **any `ac-r2-v1` certificate followed by the two moves
`[16, 15]` is a valid `sac-r8-v1` certificate** for the corresponding
`sac-v1-` challenge. It is not credited automatically: you must submit
it to track 2 yourself, under the `sac-v1-` id.

### Warm-up data

`challenges/training_424.json` publishes 424 solved Miller–Schupp
instances with full atomic-move certificates in the `ac-r2-v1`
encoding, and `challenges/stable_training_424.json` the same 424
instances in the `sac-r8-v1` encoding, each certificate extended by
`[16, 15]` so that it lands on the empty presentation. Both are
training material: replay them to validate a pipeline, or mine them for
search heuristics. Those instances are **not** in the scored pool.

## Submitting

The `challenge_id` prefix selects the track — `ac-v1-` is track 1,
`sac-v1-` is track 2 — and `move_spec_version` must be the one that
challenge carries. One submission file may mix solutions to both
tracks:

```json
{
  "method": "optional method name",
  "notes": "optional free text, <= 2000 chars",
  "solutions": [
    { "challenge_id": "ac-v1-00001",  "move_spec_version": "ac-r2-v1",
      "moves": [0, 4, 8, 3] },
    { "challenge_id": "sac-v1-00001", "move_spec_version": "sac-r8-v1",
      "moves": [0, 4, 8, 3, 16, 15] }
  ]
}
```

The two ids are different challenges, so mixing them never trips the
duplicate-challenge rule.

Submit only the moves. The server verifies deterministically and
computes length itself; any client-asserted result field (`length`,
`score`, `final_state`, …) rejects the whole submission. Limits (path
length 100 000, total relator length 10 000, work budget 5 000 000) are
the same in both tracks, and the full error-code contract is in
[evaluation.md](evaluation.md). A downloadable reference verifier — the
same Python sources the server runs — lets you check everything before
submitting.

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

**Tracks 1 and 2 are scored independently.** The same formula runs on
each, over that track's 10,115 challenges, and produces **two separate
leaderboards**; the totals are not summed and there is no combined
ranking. **First Solver** is a permanent honor recorded the moment a
challenge is first solved, per track — a challenge has an AC First
Solver and a stable-AC First Solver, and they need not be the same
team. It never changes afterwards, and does not guarantee continued
points.

> **The leaderboard length is a record, not a theorem.** The current
> best-known atomic path is the shortest path among valid competition
> submissions to date. This is **not** a mathematically proven shortest
> path.

During the competition, only path **lengths** are public — never the
moves. Your `certificate_hash` lets you claim a result publicly (e.g.
in a preprint) without revealing the path; all valid certificates are
published openly after the competition, forming a new public benchmark.

**Bridge certificates**: a verified path from one challenge's initial
state to another's is a real, machine-checked mathematical fact. It is
registered and displayed (length, team, hash) but scores no points, and
a bridge-derived solution is necessarily longer than a direct one — the
shortest-path rule keeps bridges honor, not arbitrage. A bridge is
within one move specification: both endpoints carry the same prefix.

## Tracks 3 and 4 — proof or disproof (open Sept 20)

Track 3 is the **Andrews–Curtis conjecture**, track 4 the **stable
Andrews–Curtis conjecture**. Each accepts a settlement of its
conjecture in either direction: a disproof, or a proof.

A disproof is not a search log. It is a **self-contained mathematical
argument** that some balanced presentation of the trivial group is
**not** related to the trivial presentation by the relation of that
conjecture: for track 3, the full, unbounded, non-stable Andrews–Curtis
relation; for track 4, the stable relation, which additionally allows
adding and removing a generator together with a relator equal to it.

The two conjectures are related, and the tracks honor that:

| Statement | Consequence |
|---|---|
| A proof of AC | proves stable AC as well — it settles both tracks |
| A disproof of stable AC | is also a disproof of AC — honored on both boards |
| A disproof of AC | is **not** a disproof of stable AC; the stable question stays open |

**Official channel: PDF plus expert review.** Upload the argument as a
single self-contained PDF through the competition site, naming the
conjecture it settles. A claim moves through *received* → *screening* →
*under expert review* → *accepted*, *rejected*, or *revision
requested*; review is carried out by the organizer panel together with
reviewers they designate. There is no guaranteed turnaround. The
organizers may summarily decline submissions that carry no substantive
new mathematical content, and a team may have **at most one active
claim per conjecture** — a new upload replaces that team's pending
claim on the same conjecture, and leaves a claim on the other one
untouched.

**Lean 4 fast track (optional).** A claim accompanied by, or later
formalized as, a machine-checked Lean 4 proof that builds in the
competition's frozen offline environment is fast-tracked and, on
passing verification, settles the claim. The competition Lean library
is in development for both conjectures: when published it will provide
frozen definitions of the AC and stable AC relations together with
compatibility theorems tying the competition move sets to them. Until
the library is published there is nothing to build against, so the PDF
channel is the only route open.

> **Not finding a path is not a disproof.** Failure to find a
> trivialization — in either trivialization track, under any compute
> budget, length bound, peak bound, or restricted move set — is **not**
> a disproof of either conjecture.

Explicitly **not** a counterexample to the **Andrews–Curtis
conjecture** (track 3):

* no path found within a fixed compute budget;
* nonexistence of paths of length $\le N$;
* nonexistence of paths of peak total relator length $\le B$;
* unreachability in the substitution graph or any restricted move set;
* unreachability under *stable* AC — that is not a counterexample to AC
  in the sense of this track's definition, which is about the
  non-stable relation. Note that such a result would in fact be
  *stronger*, and belongs to track 4.

Explicitly **not** a counterexample to the **stable Andrews–Curtis
conjecture** (track 4):

* no stable path found within a fixed compute budget;
* nonexistence of stable paths of length $\le N$;
* nonexistence of stable paths of peak total relator length $\le B$;
* unreachability under a bounded rank, a restricted move set, or the
  substitution graph;
* unreachability under *non-stable* AC — under any bound and any move
  set, including an exhaustive result about the 14 moves of
  `ac-r2-v1`. Stabilization is exactly what the stable conjecture adds.

The first accepted disproof of each conjecture is honored as the
**Highest Mathematical Achievement of the Competition** for that
conjecture, displayed above the leaderboards; it does not convert into
leaderboard points. A disproof of stable AC is displayed as a disproof
of both. The submission mechanics, review states, and Lean requirements
are in [evaluation.md](evaluation.md) §9; the full submission mechanics
for tracks 3 and 4 will be published before they open on September 20,
2026.

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

* Registration and team formation open: **September 8, 2026**
* Trivialization tracks (1 and 2) open: **September 11, 2026**
* Proof-or-disproof tracks (3 and 4) open: **September 20, 2026**
* Submission deadline: —
* Certificate release (post-competition): —

The submission deadline and the post-competition certificate release
date will be announced. The frozen data carries the freeze date in
`challenges/manifest.json`, `challenges/README.md` and
`competition.yaml`.
