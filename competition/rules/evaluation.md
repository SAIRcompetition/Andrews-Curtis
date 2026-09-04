# ACC Evaluation — Technical Specification

This document is normative for verification, scoring, and
confidentiality. The reference verifier in `tools/verifier/` runs the
same sources as the competition system; **the server-side verifier is
the sole authority for official results**.

## 1. Encoding and frozen objects

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

## 2. Verifier semantics

Deterministic, pure integer arithmetic. For a solution
`{challenge_id, move_spec_version, moves}` verified against limits
`{max_path_length, max_total_relator_length, max_work}`:

```
assert move_spec_version == challenge.move_spec_version   else E_SPEC_MISMATCH
assert len(moves) <= max_path_length                      else E_PATH_TOO_LONG
s    = challenge.initial_relators          # freely reduced, from the manifest
work = peak = |s0| + |s1|                  # the initial state counts toward work
for k, m in enumerate(moves):
    assert m is an integer in 0..13        else E_BAD_MOVE_ID(move_index=k)
    s = free_reduce(apply(s, m))
    tot = |s0| + |s1|
    assert tot <= max_total_relator_length else E_LENGTH_LIMIT(move_index=k)
    peak = max(peak, tot); work += tot
    assert work <= max_work                else E_WORK_BUDGET(move_index=k)
assert s == challenge.target_relators      else E_NOT_TARGET(final_shape=(|s0|,|s1|))
return { ok, length = len(moves), peak_total_relator_length = peak, work,
         certificate_hash }
```

JSON type strictness: `1.0` is a float and is **not** a valid move id;
`true`/`false` are booleans, not integers; `"3"` is a string. All are
rejected with `E_BAD_MOVE_ID` at their index.

## 3. Error codes

Whole-submission rejections (structural; do **not** count against the
daily quota):

| Code | Trigger |
|---|---|
| `E_MALFORMED` | body too large, broken/truncated JSON, wrong types, unknown keys, missing solution keys, `moves` not an array, empty/oversized `solutions`, oversized `notes` (`detail` field disambiguates) |
| `E_DUPLICATE_CHALLENGE` | same `challenge_id` twice in one submission |
| `E_CLIENT_ASSERTED_RESULT` | any of the forbidden result keys anywhere in the submission: `length`, `score`, `final_state`, `peak`, `peak_total_relator_length`, `work`, `ok`, `verdict`, `verified`, `accepted`, `result` |

Per-solution rejections (other solutions in the same submission are
processed normally):

| Code | Trigger |
|---|---|
| `E_UNKNOWN_CHALLENGE` | `challenge_id` not in the manifest |
| `E_SPEC_MISMATCH` | `move_spec_version` differs from the frozen value |
| `E_PATH_TOO_LONG` | more than `max_path_length` moves |
| `E_BAD_MOVE_ID` | non-integer or out-of-range move (carries `move_index`) |
| `E_LENGTH_LIMIT` | intermediate total relator length exceeds the limit (carries `move_index`) |
| `E_WORK_BUDGET` | cumulative work exceeds `max_work` (carries `move_index`) |
| `E_NOT_TARGET` | every move legal but endpoint ≠ `[[1],[2]]` (carries `final_shape`) |

**Check priority (frozen):** body byte limit → JSON parse →
client-asserted-result scan → structural shape → solutions count →
duplicates → then per solution: spec version → path length → per-move
id → relator length → work budget → target. The first triggered check
is the one reported.

## 4. Limits

| Limit | v1 value |
|---|---:|
| Submissions per team per day (site + API combined) | 100 |
| `solutions` per submission | 500 |
| Raw body size | 4 MB |
| `max_path_length` | 100 000 |
| `max_total_relator_length` | 10 000 |
| `max_work` = Σ per-step total relator length | 5 000 000 |

All values live in the manifest/configuration, not in code. The work
budget exists because path length × relator length alone admits ~10⁹
character operations; the 424 published training certificates have
work ≤ 2 161, so
5 000 000 leaves three orders of magnitude of headroom while bounding
verification cost.

## 5. Hashes

Explicit byte templates — fixed key order, no whitespace, ASCII only,
shortest-decimal integers (`-1` never `-01`, `-0` forbidden):

```
instance_canon    = {"challenge_id":"<id>","generators":["x","y"],
                     "initial_relators":[[...],[...]],
                     "target_relators":[[1],[2]],
                     "move_spec_version":"<ver>","move_spec_hash":"<sha256:...>"}
certificate_canon = {"challenge_id":"<id>","move_spec_version":"<ver>",
                     "moves":[m0,m1,...]}
hash              = "sha256:" + lowercase_hex(SHA256(utf8(canon)))
```

(Line breaks above are illustrative only; the canonical byte strings
contain none.)

`manifest_hash` = SHA-256 of the canonical JSON of the sorted list of
all `instance_hash` values. `instance_hash` deliberately excludes
`base_score`, `status_at_freeze`, `source`, and `freeze_date`: policy
edits never invalidate certificates. Any change to the manifest or the
move spec changes at least one published hash, and submissions carrying
a stale `move_spec_version` are rejected with `E_SPEC_MISMATCH`.

## 6. Scoring

Per challenge $i$: $V_i$ from the manifest;
$L_{t,i}$ = team $t$'s minimal accepted length;
$L^\star_i = \min_t L_{t,i}$;
$k_i = \#\{t : L_{t,i} = L^\star_i\}$;
$P_{t,i} = V_i\,2^{1-k_i}$ if $L_{t,i}=L^\star_i$, else 0;
$P_t = \sum_i P_{t,i}$.

The leaderboard is recomputed **in full** from the best-length table
after every accepted solution; every recomputation writes a
`scoring_run` (with `manifest_hash`, verifier version, event time) so
any historical leaderboard is reproducible. Scores are exact rationals
end to end — floats are forbidden — and displayed round-half-even to 4
decimal places. Ranking: total descending, then earliest
time-of-current-total. **First Solver** = argmin over accepted
solutions of `(received_at, submission_id)`; `submission_id` is
monotonically increasing and breaks same-millisecond ties; the record
is immutable.

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
`to_challenge.initial_relators` (exact ordered). Registered on both
challenges and in `/discoveries`; scores nothing in v1; any future
merging of challenges happens only at announced scoring-epoch
boundaries, by the organizers, with verified bridges as the only
admissible evidence.

## 9. Counterexample track

### 9.1 What is claimed

A counterexample claim asserts, for a specific balanced presentation
$P$, that $P$ presents the trivial group and that $P$ is **not** related
to the trivial presentation by the full, unbounded, non-stable
Andrews–Curtis relation (inversion, multiplication, and conjugation by
an **arbitrary** word). The claim must name the presentation
explicitly; if it is a pool instance, it must name the `challenge_id`.

### 9.2 Official channel: PDF plus expert review

`POST /counterexample-submissions`, content type `application/pdf`,
one file, **≤ 25 MB**. The argument must be self-contained: a reader
must be able to check it from the PDF alone, without running code and
without consulting unpublished material. Supplementary data may be
referenced but never substitutes for the argument.

States:

| State | Meaning |
|---|---|
| `received` | upload accepted and timestamped |
| `screening` | organizer triage for substantive mathematical content |
| `under_review` | with the review panel |
| `accepted` | the disproof is accepted |
| `rejected` | declined, with a reason |
| `revision_requested` | returned to the team; a revised upload restarts at `received` |

Review is carried out by the organizer panel together with reviewers
they designate. **No turnaround is guaranteed.** The organizers may
summarily decline a submission that carries no substantive new
mathematical content. A team may hold **at most one active claim**
(`received`, `screening`, `under_review`) at a time; a new upload
replaces the pending one, and the receipt time of the replacement is
the one that counts. `GET /counterexample-submissions/me` returns a
team's own claims and their states.

"First" is by server receipt time of the submission that is ultimately
accepted; later independent disproofs are marked `Independent
Confirmation`.

### 9.3 Optional fast track: machine-checked Lean 4

A claim accompanied by — or later formalized as — a Lean 4 package that
builds offline (`lake build` in the frozen container, no network) and
proves

```lean
theorem candidate_matches_manifest : P = Competition.instance challenge_id
theorem candidate_presents_trivial_group : P.PresentsTrivialGroup
theorem candidate_not_ac_reachable :
    ¬ StandardAC.Reachable P StandardAC.trivialPresentation
```

against the competition Lean library is fast-tracked: machine checking
replaces mathematical refereeing of the argument, and passing
verification settles the claim.

**The competition Lean library is in development and is not yet
available.** When published it will provide frozen definitions of the
full, unbounded, non-stable AC relation (`StandardAC.Step`) together
with a compatibility theorem tying the 14-move closure of `ac-r2-v1` to
the standard AC moves; the exact statement, the pinned toolchain, and a
template project will be published in `tools/lean/` at that point.
Until then the PDF channel of §9.2 is the official and only route, and
the requirements below are stated in advance so that a formalization
effort can target them.

Frozen and published by hash: Lean version, `lean-toolchain`, Mathlib
commit, competition formalization commit, `lake-manifest.json`,
container image digest.

Automatic CI gates (all fail-closed):

1. clean offline container `lake build`;
2. `#print axioms` on all three theorems — whitelist exactly
   `propext`, `Classical.choice`, `Quot.sound`;
3. source scan for `sorry|admit|sorryAx|unsafe|native_decide|@[implemented_by]`;
4. SHA-256 comparison of the frozen definition files — any edit rejects;
5. steps 1–2 repeated on an independent machine.

Passing all five gates yields a **Provisional Counterexample**; it
becomes **Verified** after review of the trust boundary and
confirmation that the formal statement matches the standard AC
conjecture, plus public source release for community scrutiny.

### 9.4 What is not a counterexample

Explicitly **not** a counterexample: failure to find a path under any
compute budget; nonexistence of paths of length ≤ N or peak ≤ B;
unreachability in a restricted move set or substitution graph;
unreachability under stable AC.

### 9.5 Honor

The first accepted disproof is displayed above the leaderboard as the
**Highest Mathematical Achievement of the Competition**. It awards no
leaderboard points and does not enter any team's score.
