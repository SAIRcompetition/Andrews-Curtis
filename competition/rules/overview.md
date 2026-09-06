# Andrews–Curtis Conjecture Challenge (ACC) — Overview

**Prelaunch preview — registration and submissions are not open.** You
can inspect the current rules and data and try the Python verifier
locally. The official data freeze and competition dates have not yet
been announced.

ACC is one competition with two tracks: **Discovery Track** rewards
short verified trivializations of the published instances; **Prove
Track** accepts proofs or disproofs of the full conjecture.

## The mathematics

The **Andrews–Curtis conjecture** (1965) asserts that every balanced
presentation of the trivial group can be transformed into the trivial
presentation by a sequence of elementary moves — relator inversion,
relator multiplication, and conjugation. It has been open for sixty
years; most experts expect it to be false, but no counterexample has
ever been verified.

The [official statement](statement.md) fixes the full conjecture for
every positive finite rank and maps it to the
[Lean project](../tools/lean/README.md). A proof must cover that full
statement; a disproof must establish its negation. An explicit
counterexample must present the trivial group and rule out reachability
under the full, unbounded, non-stable relation. The finite rank-two pool
below is a separate search task.

Discovery Track uses a **pool of 10,115 balanced
presentations of the trivial group**, `ac-v1-00001` … `ac-v1-10115`,
spanning warm-up exercises to the research frontier. Its official
publication freeze is still pending. The pool draws on
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

### Submitting

The format below is the successful **training example**, which uses
`examples/training_manifest.json` rather than the scored competition
manifest:

```json
{
  "solutions": [
    { "challenge_id": "ms-train-0160", "moves": [6, 4, 2, 9, 1, 4, 1] }
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

Each solution contains only `challenge_id` and `moves`. You may also
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
If a bridge is composed into a valid submitted trivialization, that
full solution is scored normally for the challenge it solves, using
its full move length.

## Prove Track

Prove Track accepts **proofs and disproofs** of the
[official statement](statement.md). A proof must cover every positive
finite rank; a disproof must establish the negation of that statement.
An explicit counterexample must be a balanced presentation of the
trivial group that cannot reach the standard presentation under the
full, unbounded, non-stable Andrews–Curtis relation. It may lie outside
the Discovery pool; if it uses a pool instance, identify its challenge.

**Planned submission after opening.** Set `claim_type` to `proof` or `disproof` and
provide a description stating the claim and summarizing the argument.
The complete argument may be in the description, a paper/PDF, Lean
material at a fixed GitHub commit, an identified arXiv version, or a
combination of these. A PDF is optional. Without supporting material,
the description itself must contain the complete substantive argument.

**Public versions and discussion.** The planned platform will publish
all Prove submission versions and comments by default. Each version
will receive a server timestamp and a monotonically increasing ID;
revisions will create new versions rather than overwrite old ones.
Supporting links will identify the fixed commit or document version
being submitted. Comments and review decisions will identify the
submission version they address.

The organizers and their designated reviewers will consider public
comments and issue a reasoned `accepted`, `rejected`, or
`revision_requested` decision for a specific version. They may correct
a decision publicly while preserving its history. Lean compilation
does not replace review of the claim, its scope, and its trust boundary.
A formal proof targets `AC.Conjecture`; a formal disproof targets
`¬ AC.Conjecture`, equivalently `AC.Counterexample`. The
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
> or restricted move set — is **not** a counterexample.

The first accepted proof or disproof under this priority rule receives
the **Highest Mathematical Achievement of the Competition** honor.
Prove results do not earn Discovery points and do not automatically
end Discovery Track. Submission fields, review states, public records,
and the full priority and credit rules are in
[evaluation.md](evaluation.md) §9. Both tracks remain closed during
prelaunch.

## Teams and integrity

One person, one team; team size unlimited; members may join during the
competition with organizer approval. **Teams may not merge after either
has submitted.** Public learning and cross-team discussion with stated
contributions are welcome. Sharing a specific Discovery certificate
across teams is joint work and must not be resubmitted for independent
credit or scoring. Coordinated cheating (including sockpuppets)
disqualifies all involved teams. The organizers may request provenance
for any submission.

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

* Registration opens: to be announced.
* Submissions open: to be announced.
* Submission deadline: to be announced.
* Discovery certificate release (post-competition): to be announced.

Current status is `prelaunch`. In `competition.yaml`, `freeze_date`,
`freeze_commit`, `registration_opens`, `submissions_open`,
`submission_deadline`, and `certificate_release` are all `null` until
announced. The manifest's `freeze_date` is also `null`; the official
freeze commit will be published before the formal release.
