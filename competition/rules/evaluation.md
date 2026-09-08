# ACC Evaluation — Technical Specification

This document is normative for verification, scoring, and
confidentiality. The reference verifier in `tools/verifier/` runs the
same sources as the competition system; **the server-side verifier is
the sole authority for official results**.

## 1. Encoding and frozen objects

There are two frozen move specifications, one per trivialization track.
The challenge record names the one that governs it, and the
`challenge_id` prefix identifies it: `ac-v1-` → `ac-r2-v1`,
`sac-v1-` → `sac-r8-v1`. Everything else — replay, limits, hashes,
scoring, confidentiality — is shared.

### 1.1 `ac-r2-v1` (track 1, challenge ids `ac-v1-00001` … `ac-v1-10115`)

Letters: `1 = x, -1 = x^-1, 2 = y, -2 = y^-1`. A word is an array of
nonzero integers; a presentation state is the ordered pair
`[r0, r1]`, both words kept freely reduced. Free reduction is a single
left-fold: scan left to right, cancel a letter against the top of the
output stack when they are inverse. Target: the exact ordered pair
`[[1],[2]]`.

The 14 moves of `ac-r2-v1` and the canonicalization table are published
machine-readably in `challenges/move_spec.json`; ids are frozen
forever. `move_spec_hash` is the SHA-256 of the canonical JSON (sorted
keys, no whitespace, ASCII) of the `moves` array of that file.

### 1.2 `sac-r8-v1` (track 2, challenge ids `sac-v1-00001` … `sac-v1-10115`)

`sac-v1-N` carries the same `initial_relators` as `ac-v1-N`.

A state is an **ordered list of $k$ freely reduced relators** over the
generators $1,\dots,k$ — letters $\pm 1,\dots,\pm k$, with `1 = x`,
`2 = y` and $g_3,\dots,g_8$ the extra generators — where
$0 \le k \le 8$. Every challenge starts at $k = 2$. Free reduction is
the same left-fold. Target: the **empty presentation** `[]`.

The 257 moves are integer ids `0`–`256`. A move's meaning is
independent of the current rank; its applicability is a runtime check:

| ids | Category | Count | Effect |
|---|---|---:|---|
| 0–13 | the `ac-r2-v1` block | 14 | identical to §1.1: same rows, same ids, same inverses |
| 14 | stabilize | 1 | $k \to k+1$: append the generator $k+1$ and the relator `[k+1]` |
| 15–22 | destabilize relator $i$ ($i = 0,\dots,7$) | 8 | delete relator $i$ and the generator $g$ it names, renumbering every generator above $g$ down by one; $k \to k-1$ |
| 23–28 | inversion of relator $i$ ($i = 2,\dots,7$) | 6 | $r_i \leftarrow r_i^{-1}$ |
| 29–136 | multiplication $r_i \leftarrow r_i r_j^{\pm 1}$, $i \ne j < 8$ | 108 | the four rank-2 cases are ids 2–5 |
| 137–256 | conjugation $r_i \leftarrow c\,r_i\,c^{-1}$, $c = g^{\pm 1}$, $i < 8$, $g \le 8$ | 120 | the eight rank-2 cases are ids 6–13 |

Applicability, checked before the move is applied:

| Move | Applicable iff | `reason` on failure |
|---|---|---|
| any move naming relator $i$ | $i < k$ | `relator_out_of_rank` |
| any conjugation by $g^{\pm 1}$ | $g \le k$ | `generator_out_of_rank` |
| 14 (stabilize) | $k < 8$ | `max_rank_exceeded` |
| 15–22 (destabilize $i$) | relator $i$ is **exactly** the single positive letter $g$, and $g$ occurs in no other relator | `destabilize_precondition` |

`max_rank = 8` is part of the specification, not a limit: it is frozen
in `challenges/stable_move_spec.json` and does not move.

The full 257-row table, with a description of every id, the letter
encoding, `max_rank`, and the rank-2 canonicalization table, is
published machine-readably in `challenges/stable_move_spec.json`; ids
are frozen forever. Its `move_spec_hash` is computed exactly as in
§1.1, over that file's `moves` array.

**Canonical finish.** From any state whose $k$ relators are the $k$
generators as single letters, each occurring once and possibly
inverted, the shortest finish is $k$ + (number of inverted letters)
moves: invert the inverted ones, then destabilize from the highest
relator index down to 0. In rank 2 that is `[16,15]` from both $(x,y)$
and $(y,x)$ — 2 moves either way, 3 with one inverted letter, 4 with
two; the rows are in `stable_move_spec.json`,
`canonicalization_table`. Consequently any accepted `ac-r2-v1`
certificate, followed by `[16, 15]`, is a valid `sac-r8-v1` certificate
for the corresponding `sac-v1-` challenge — but it must be submitted
under that id to count (§6). Public warm-up data for this
specification is `challenges/stable_training_424.json`: the 424
`training_424.json` certificates, each extended by `[16, 15]`.

## 2. Verifier semantics

Deterministic, pure integer arithmetic, and identical in both tracks
except where the specification is consulted. Write $\mathrm{tot}(s) =
\sum_i |r_i|$ for the total relator length of a state. For a solution
`{challenge_id, move_spec_version, moves}` verified against limits
`{max_path_length, max_total_relator_length, max_work}`:

```
spec = challenge.move_spec_version   # ac-r2-v1 | sac-r8-v1, per the id prefix
assert move_spec_version == spec              else E_SPEC_MISMATCH
assert len(moves) <= max_path_length          else E_PATH_TOO_LONG
s    = challenge.initial_relators    # freely reduced, from the manifest
work = peak = tot(s)                 # the initial state counts toward work
for k, m in enumerate(moves):
    assert m is an integer in spec's range    else E_BAD_MOVE_ID(k)
    assert m is applicable to s               else E_MOVE_NOT_APPLICABLE(k, m, reason)
    s = free_reduce(apply(s, m))     # spec's move table; freely reduced
    assert tot(s) <= max_total_relator_length else E_LENGTH_LIMIT(k)
    peak = max(peak, tot(s)); work += tot(s)
    assert work <= max_work                   else E_WORK_BUDGET(k)
assert s == challenge.target_relators         else E_NOT_TARGET(final_shape)
return { ok, length = len(moves), peak_total_relator_length = peak, work,
         certificate_hash }
```

Every per-move rejection carries the failing `move_index` $k$;
`E_MOVE_NOT_APPLICABLE` also carries the move and a `reason` (§1.2),
and `E_NOT_TARGET` a `final_shape`, the list of relator lengths at the
end. The final comparison is **exact equality with the challenge's
`target_relators`** — the ordered pair `[[1],[2]]` under `ac-r2-v1`,
the empty list `[]` under `sac-r8-v1`. The applicability check is a
`sac-r8-v1` check only: under `ac-r2-v1` every id in `0..13` is
applicable in every state, so it never fires.

JSON type strictness: `1.0` is a float and is **not** a valid move id;
`true`/`false` are booleans, not integers; `"3"` is a string. All are
rejected with `E_BAD_MOVE_ID` at their index.

## 3. Error codes

Whole-submission rejections (structural; do **not** count against the
daily quota):

| Code | Trigger |
|---|---|
| `E_MALFORMED` | body too large, broken/truncated JSON, wrong types, unknown keys, missing solution keys, `moves` not an array, empty/oversized `solutions`, oversized `notes` (`detail` field disambiguates) |
| `E_DUPLICATE_CHALLENGE` | same `challenge_id` twice in one submission (`ac-v1-00001` and `sac-v1-00001` are different ids, so a submission may carry both) |
| `E_CLIENT_ASSERTED_RESULT` | any of the forbidden result keys anywhere in the submission: `length`, `score`, `final_state`, `peak`, `peak_total_relator_length`, `work`, `ok`, `verdict`, `verified`, `accepted`, `result` |

Per-solution rejections (other solutions in the same submission are
processed normally):

| Code | Trigger |
|---|---|
| `E_UNKNOWN_CHALLENGE` | `challenge_id` not in the manifest |
| `E_SPEC_MISMATCH` | `move_spec_version` differs from the challenge's frozen `move_spec_version` — this is what keeps the two tracks apart: an `ac-r2-v1` solution submitted against a `sac-v1-` id is rejected here, and vice versa |
| `E_PATH_TOO_LONG` | more than `max_path_length` moves |
| `E_BAD_MOVE_ID` | non-integer, or an integer outside the specification's range: `0..13` under `ac-r2-v1`, `0..256` under `sac-r8-v1` (carries `move_index`) |
| `E_MOVE_NOT_APPLICABLE` | `sac-r8-v1` only: the move id is valid but not applicable in the current state (carries `move_index`, `move`, and `reason` ∈ `relator_out_of_rank`, `generator_out_of_rank`, `max_rank_exceeded`, `destabilize_precondition`) |
| `E_LENGTH_LIMIT` | intermediate total relator length exceeds the limit (carries `move_index`) |
| `E_WORK_BUDGET` | cumulative work exceeds `max_work` (carries `move_index`) |
| `E_NOT_TARGET` | every move legal but the endpoint is not the challenge's target — `[[1],[2]]` under `ac-r2-v1`, `[]` under `sac-r8-v1` (carries `final_shape`, the list of relator lengths at the end, possibly empty) |

**Check priority (frozen):** body byte limit → JSON parse →
client-asserted-result scan → structural shape → solutions count →
duplicates → then per solution: spec version → path length → per-move
id → per-move applicability → relator length → work budget → target.
The first triggered check is the one reported.

## 4. Limits

| Limit | v1 value |
|---|---:|
| Submissions per team per day (site + API combined) | 100 |
| `solutions` per submission | 500 |
| Raw body size | 4 MB |
| `max_path_length` | 100 000 |
| `max_total_relator_length` | 10 000 |
| `max_work` = Σ per-step total relator length | 5 000 000 |

The limits are identical in both trivialization tracks, and the
submission quotas (100 per day, 500 solutions per submission) are **per
team across both tracks**, not per track, unless the competition
platform announces otherwise. `max_rank = 8` is not a limit: it lives
in `sac-r8-v1` (§1.2), and exceeding it is `E_MOVE_NOT_APPLICABLE`, not
a budget error.

All values live in the manifest/configuration, not in code. The work
budget exists because path length × relator length alone admits ~10⁹
character operations; the 424 published `ac-r2-v1` training
certificates have work ≤ 2 161, and their `sac-r8-v1` extensions add
one to that, so 5 000 000 leaves three orders of magnitude of headroom
while bounding verification cost.

## 5. Hashes

Explicit byte templates — fixed key order, no whitespace, ASCII only,
shortest-decimal integers (`-1` never `-01`, `-0` forbidden):

```
instance_canon    = {"challenge_id":"<id>","generators":["x","y"],
                     "initial_relators":[[...],[...]],
                     "target_relators":<target>,
                     "move_spec_version":"<ver>","move_spec_hash":"<sha256:...>"}
certificate_canon = {"challenge_id":"<id>","move_spec_version":"<ver>",
                     "moves":[m0,m1,...]}
hash              = "sha256:" + lowercase_hex(SHA256(utf8(canon)))
```

(Line breaks above are illustrative only; the canonical byte strings
contain none.)

The template is the same in both tracks; the two tracks differ only in
the values substituted into it. `<target>` is `[[1],[2]]` for an
`ac-v1-` challenge and `[]` for a `sac-v1-` one, and
`move_spec_version` / `move_spec_hash` are that challenge's. So
`ac-v1-N` and `sac-v1-N` share `initial_relators` but have different
`instance_hash` values, and every `ac-v1-` hash is unchanged from the
single-track manifest.

`manifest_hash` = SHA-256 of the canonical JSON of the sorted list of
all `instance_hash` values, over all 20,230 challenge records.
`instance_hash` deliberately excludes `base_score`, `status_at_freeze`,
`source`, and `freeze_date`: policy edits never invalidate
certificates. The two `move_spec_hash` values — one per specification —
are published in `competition.yaml` and in the manifest's `move_specs`
list, alongside the file each covers. Any change to the manifest or to
either move spec changes at least one published hash, and submissions
carrying a `move_spec_version` that is not the challenge's are rejected
with `E_SPEC_MISMATCH`.

## 6. Scoring

Per challenge $i$: $V_i$ from the manifest;
$L_{t,i}$ = team $t$'s minimal accepted length;
$L^\star_i = \min_t L_{t,i}$;
$k_i = \#\{t : L_{t,i} = L^\star_i\}$;
$P_{t,i} = V_i\,2^{1-k_i}$ if $L_{t,i}=L^\star_i$, else 0;
$P_t = \sum_i P_{t,i}$.

**The formula runs once per track, over that track's challenges only.**
Tracks 1 and 2 have separate leaderboards and separate totals; the two
are never summed and there is no combined ranking. A solution is
credited to exactly the track its `challenge_id` names: an `ac-r2-v1`
certificate extended by `[16, 15]` (§1.2) earns track-2 points only if
it is submitted under the `sac-v1-` id, and it is never credited
automatically.

The leaderboard is recomputed **in full** from the best-length table
after every accepted solution; every recomputation writes a
`scoring_run` (with `manifest_hash`, verifier version, event time) so
any historical leaderboard is reproducible. Scores are exact rationals
end to end — floats are forbidden — and displayed round-half-even to 4
decimal places. Ranking: total descending, then earliest
time-of-current-total. **First Solver** = argmin over accepted
solutions of `(received_at, submission_id)`, computed per challenge and
therefore per track; `submission_id` is monotonically increasing and
breaks same-millisecond ties; the record is immutable.

## 7. Confidentiality

Public per challenge during the competition: `status`,
`current_best_length`, `current_best_solver`, `first_solver`,
`first_solved_at`, `k_teams`, `base_score`, `certificate_hash`,
`peak_total_relator_length` (non-scoring), verified bridges (length,
team, time, hash). **Not public: any move sequence, any intermediate
state, any path statistic beyond length.** Teams see only their own
submissions (`GET /submissions/me`). The public API serializer uses an
explicit whitelist, with a regression test asserting no `moves` array
ever appears in any public response. All valid certificates are
published after the competition.

## 8. Bridge certificates

`POST /bridge-submissions` with
`{from_challenge_id, to_challenge_id, move_spec_version, moves}`.
Verified exactly as §2 with the target replaced by
`to_challenge.initial_relators` (exact ordered). **Both challenges must
carry the same `move_spec_version`** — a bridge lives inside one
specification, and a mixed pair is rejected with `E_SPEC_MISMATCH`.
Registered on both challenges and in `/discoveries`; scores nothing in
v1; any future merging of challenges happens only at announced
scoring-epoch boundaries, by the organizers, with verified bridges as
the only admissible evidence.

## 9. Proof-or-disproof tracks

Track 3 settles the Andrews–Curtis conjecture; track 4 settles the
stable Andrews–Curtis conjecture. They open on September 20, 2026. Both
run on the mechanics below, independently of each other and of the
trivialization leaderboards.

### 9.1 What is claimed

A **track 3** disproof asserts, for a specific balanced presentation
$P$, that $P$ presents the trivial group and that $P$ is **not** related
to the trivial presentation $\langle x,y \mid x,y\rangle$ by the full,
unbounded, non-stable Andrews–Curtis relation (inversion,
multiplication, and conjugation by an **arbitrary** word).

A **track 4** disproof asserts, for a specific balanced presentation
$P$, that $P$ presents the trivial group and that $P$ is **not** related
to the empty presentation — equivalently, to
$\langle x,y \mid x,y\rangle$ — by the **stable** Andrews–Curtis
relation: the relation above, extended by adding a new generator
together with a relator equal to it, and by removing such a pair. No
rank bound of any kind is part of this claim; the bound `max_rank = 8`
belongs to the `sac-r8-v1` competition metric of §1.2 and to nothing
else.

Either track also accepts a **proof** of its conjecture, on the same
mechanics. The logical relations are honored as stated: a proof of AC
proves stable AC; a disproof of stable AC is a disproof of AC and is
recognized on both tracks; a disproof of AC is not a disproof of stable
AC.

The claim must name the presentation explicitly; if it is a pool
instance, it must name the `challenge_id`.

### 9.2 Official channel: PDF plus expert review

`POST /counterexample-submissions`, content type `application/pdf`,
one file, **≤ 25 MB**, with a `conjecture` selector — `ac` for track 3,
`stable_ac` for track 4 — naming the statement the argument settles.
The argument must be self-contained: a reader must be able to check it
from the PDF alone, without running code and without consulting
unpublished material. Supplementary data may be referenced but never
substitutes for the argument.

States:

| State | Meaning |
|---|---|
| `received` | upload accepted and timestamped |
| `screening` | organizer triage for substantive mathematical content |
| `under_review` | with the review panel |
| `accepted` | the claim is accepted |
| `rejected` | declined, with a reason |
| `revision_requested` | returned to the team; a revised upload restarts at `received` |

Review is carried out by the organizer panel together with reviewers
they designate. **No turnaround is guaranteed.** The organizers may
summarily decline a submission that carries no substantive new
mathematical content. A team may hold **at most one active claim per
conjecture** (`received`, `screening`, `under_review`): a new upload
replaces that team's pending claim on the *same* conjecture — the
receipt time of the replacement is the one that counts — and leaves a
claim on the other conjecture untouched. `GET
/counterexample-submissions/me` returns a team's own claims, their
conjecture, and their states.

"First" is by server receipt time of the submission that is ultimately
accepted, per conjecture; later independent settlements of the same
conjecture are marked `Independent Confirmation`.

### 9.3 Optional fast track: machine-checked Lean 4

A claim accompanied by — or later formalized as — a Lean 4 package that
builds offline (`lake build` in the frozen container, no network) and
proves, against the competition Lean library, that the named
presentation presents the trivial group and is not related to the
trivial presentation under the relation of the conjecture it targets,
is fast-tracked: machine checking replaces mathematical refereeing of
the argument, and passing verification settles the claim.

**The competition Lean library is in development for both conjectures
and is not yet available; nothing is available to build against.** When
published it will carry frozen definitions of the AC and stable AC
relations, the exact theorem statements a contestant must prove, the
pinned toolchain, and a template project, in `tools/lean/`. Until then
the PDF channel of §9.2 is the official and only route, and the
requirements below are stated in advance so that a formalization effort
can target them.

Frozen and published by hash: Lean version, `lean-toolchain`, Mathlib
commit, competition formalization commit, `lake-manifest.json`,
container image digest.

Automatic CI gates (all fail-closed):

1. clean offline container `lake build`;
2. `#print axioms` on every theorem the claim rests on — whitelist
   exactly `propext`, `Classical.choice`, `Quot.sound`;
3. source scan for `sorry|admit|sorryAx|unsafe|native_decide|@[implemented_by]`;
4. SHA-256 comparison of the frozen definition files — any edit rejects;
5. steps 1–2 repeated on an independent machine.

Passing all five gates yields a **Provisional Counterexample**; it
becomes **Verified** after review of the trust boundary and
confirmation that the formal statement matches the conjecture as stated
in §9.1, plus public source release for community scrutiny.

### 9.4 What is not a counterexample

Not a counterexample to the **Andrews–Curtis conjecture** (track 3):
failure to find a path under any compute budget; nonexistence of paths
of length ≤ N or peak ≤ B; unreachability in a restricted move set or
substitution graph; unreachability under *stable* AC — which is not a
counterexample to AC in the sense of §9.1, whose relation is the
non-stable one. A result of that last kind is *stronger* than an AC
counterexample and belongs to track 4.

Not a counterexample to the **stable Andrews–Curtis conjecture**
(track 4): failure to find a stable path under any compute budget;
nonexistence of stable paths of length ≤ N or peak ≤ B; unreachability
under a bounded rank (including `max_rank = 8`), a restricted move set,
or the substitution graph; unreachability under *non-stable* AC, under
any bound and any move set — including an exhaustive result about the
14 moves of `ac-r2-v1`.

### 9.5 Honor

The first accepted disproof of each conjecture is displayed above the
leaderboards as the **Highest Mathematical Achievement of the
Competition** for that conjecture. An accepted disproof of stable AC is
displayed as a disproof of both conjectures. Neither award converts
into leaderboard points, and neither enters any team's score in either
trivialization track.
