# Discovery Track

**Discovery Track opens on September 11, 2026 at 16:00 UTC**
(`2026-09-11T16:00:00Z`). Find short verified move sequences for two
problems, **AC** and **Stable AC**, using the same pool of **10,115
balanced presentations of the trivial group**. Each problem has its own
leaderboard. The **424 training presentations are outside both scored
problem sets** and earn no points.

Each submitted solution contains only `challenge_id` and `moves`.
Start with the [successful training example](#21-submission-format-and-local-example),
then use this document for the exact moves, verifier contract, scoring,
and disclosure rules. General participation, team, experimental-status,
and competition-wide rules are in the [competition overview](overview.md).

The announced deadline is **November 30, 2026**; its exact UTC time remains
to be announced. Eligibility uses the time the server receives the complete
submission: at or after the opening above and before `submission_deadline`.
Verification may finish after the deadline; a late submission earns no
points. See [competition.yaml](../competition.yaml) for the maintained
schedule and publication state. Local self-checks are available before
launch and do not register competition submissions; once submissions open,
the competition service's verifier determines official Discovery results.

## 1. Problems and move specifications

[manifest.json](../challenges/manifest.json) contains 20,230 challenge
records: one for each problem on each of the 10,115 initial presentations.
Matching ID suffixes select identical initial relators:

| Problem | Challenge IDs | Move specification | Target |
|---|---|---|---|
| AC | `ac-v1-00001` through `ac-v1-10115` | `ac-r2-v1`, 14 moves | Exact ordered pair `[[1],[2]]`, at rank 2 |
| Stable AC | `sac-v1-00001` through `sac-v1-10115` | `sac-r8-v1`, 257 moves | Empty presentation `[]`, with current rank at most 8 |

The challenge supplies its move specification. The numbered move tables
are frozen: IDs retain their published meanings. Every scored challenge
has `base_score: 1`. The official publication freeze is recorded separately
in the metadata; an unset freeze date does not change the instance hashes.

### 1.1 AC problem

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

Words are freely reduced after every move by a single left-fold: scan
left to right, canceling a letter against the top of the output stack
when they are inverse. The move set is closed under inversion, so
reachability is symmetric.

**The endpoint must be exactly `[[1],[2]]`, in order.** Ending at
$(y,x)$ or $(x^{-1},y)$ does not count — but this costs at most **5**
extra moves from any "loose trivial" state. The exhaustively verified
shortest suffixes are also published as `canonicalization_table` in
[move_spec.json](../challenges/move_spec.json):

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

Append the matching suffix and verify the complete path against the
[limits](#4-limits); the suffix counts toward path length and work.

### 1.2 Stable AC problem

A state is an ordered list of $k$ freely reduced relators over letters
$\pm1,\ldots,\pm k$, where $0\le k\le8$. Each challenge starts at
rank 2; the target is the **empty presentation** `[]`.

| Move IDs | Operation |
|---|---|
| 0–13 | The original AC block, with unchanged meanings |
| 14 | Stabilize: append generator $k+1$ and relator `[k+1]` |
| 15–22 | Destabilize relator $i=0,\ldots,7$ |
| 23–28 | Invert relator $i=2,\ldots,7$ |
| 29–136 | Remaining right multiplications by another relator or its inverse |
| 137–256 | Remaining conjugations by a generator letter or its inverse |

All 257 rows are in [stable_move_spec.json](../challenges/stable_move_spec.json);
its `moves` array is hashed as specified in [§5](#5-hashes). The operation
IDs cover ranks up to 8: 8 inversions, 112 right multiplications, 128 generator-letter
conjugations, 1 stabilization, and 8 destabilizations. Applicability depends
on the current state. A move may name only existing relators and generators.
Stabilization requires $k<8$. Destabilization requires the selected relator
to be exactly a single positive generator $g$, absent from every other
relator. It deletes that relator and generator, then renumbers generators
above $g$ down by one, preserving the order of the remaining relators.

The rank cap is frozen in `sac-r8-v1`. It restricts this search benchmark
and does not change the full stable conjecture. From a signed permutation
of the $k$ generators, invert negative relators and then destabilize from
the highest relator index down; the shortest finish has $k$ plus the number of negative
relators moves. From either `(x,y)` or `(y,x)`, the suffix is `[16,15]`.

An AC solution followed by `[16,15]` reaches the stable target. It is
accepted for the Stable AC problem only if the extended path also satisfies
its limits: the suffix adds two moves and one unit of work. Submit it
under the corresponding `sac-v1-` ID; points do not transfer between problems.

### 1.3 Data and training

The scored pool draws on the extended Miller–Schupp family, automorphic
disguises of hard classes, and presentations solvable by construction.
It includes all **550 MS-1190 instances with no publicly known
trivialization**, as classified in the published dataset, and excludes
instances with public replayable certificates. The Miller–Schupp encoding is

$$MS(n,w)=\langle x,y\mid x^{-1}y^n x y^{-(n+1)},\ xw^{-1}\rangle,
\qquad n\ge1,\quad \sigma_x(w)=0.$$

These are presentations of the trivial group. The data's unresolved status
means no public valid trivialization is known at the recorded snapshot;
it is not a verifier rejection or a claim that the instance is unsolvable.

Internal per-instance difficulty labels and direct provenance mappings
are omitted. Participants may still recognize presentations by comparison
with public mathematical sources; the omission is not an anonymity guarantee.
See the [challenge data guide](../challenges/README.md) for the manifest
schema, pool construction, and full MS-1190 reference metadata.

[training_424.json](../challenges/training_424.json) contains 424 solved AC
presentations. [stable_training_424.json](../challenges/stable_training_424.json)
contains the same presentations with paths extended by `[16,15]`.
They are outside both scored problem sets. The example below exercises
both specifications using a separate, unscored manifest.

## 2. Submissions and verification

### 2.1 Submission format and local example

A submission document has a nonempty `solutions` array. Each solution
contains exactly `challenge_id` and `moves`; do not add a move-spec version
or verifier result. A batch may contain both `ac-v1-` and `sac-v1-` IDs.
Optional top-level `method` is a string naming the method; optional `notes`
is a string of at most 2,000 characters.

This is the complete successful **training submission**:

```json
{
  "solutions": [
    { "challenge_id": "ms-train-0160", "moves": [6, 4, 2, 9, 1, 4, 1] },
    { "challenge_id": "sac-train-0160", "moves": [6, 4, 2, 9, 1, 4, 1, 16, 15] }
  ]
}
```

From the development repository or exported public package root, run:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

Expected: exit status **0**, top-level `accepted: true`, and `ok: true`
for both results. The [examples guide](../examples/README.md) contains the
complete [expected receipt](../examples/sample_verdict.json) and a separate
rejection example. Training IDs do not occur in the scored manifest:
checking this sample against it returns `E_UNKNOWN_CHALLENGE` and exit
status 1. For scored submissions, use IDs from the official manifest and
your own move sequences. To check `mine.json` locally:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/challenges/manifest.json \
  --submission mine.json --pretty
```

The [reference verifier](../tools/verifier/README.md) uses only the Python
standard library. Its command-line exit codes are:

| Code | Meaning |
|---:|---|
| 0 | All solutions verified successfully |
| 1 | Structurally accepted document with at least one rejected solution |
| 2 | Whole-submission rejection or failing golden vectors |
| 3 | Usage or input/output error |

Run the published conformance vectors and check the manifest's hashes:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --golden competition/challenges/golden_vectors.json
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/challenges/manifest.json --check-hashes
```

### 2.2 Verifier semantics

Deterministic, pure integer arithmetic. For a solution
`{challenge_id, moves}` verified against limits
`{max_path_length, max_total_relator_length, max_work}`, the server
looks up the official challenge by id and uses its `move_spec_version`
for replay and certificate hashing. Each solution must contain exactly
`challenge_id` and `moves`; optional `method` and `notes` belong to the
top-level submission document.

```
assert len(moves) <= max_path_length       else E_PATH_TOO_LONG
s    = challenge.initial_relators          # freely reduced, from the manifest
work = peak = sum(len(r) for r in s)       # the initial state counts toward work
for k, m in enumerate(moves):
    assert m is an integer in the spec     else E_BAD_MOVE_ID(move_index=k)
    assert m is applicable to s            else E_MOVE_NOT_APPLICABLE(move_index=k)
    s = free_reduce(apply(s, m))
    tot = sum(len(r) for r in s)
    assert tot <= max_total_relator_length else E_LENGTH_LIMIT(move_index=k)
    peak = max(peak, tot); work += tot
    assert work <= max_work                else E_WORK_BUDGET(move_index=k)
assert s == challenge.target_relators      else E_NOT_TARGET(final_shape=[len(r) for r in s])
return { ok, length = len(moves), peak_total_relator_length = peak, work,
         certificate_hash }
```

The move-ID range is 0–13 for AC and 0–256 for Stable AC. Every AC move
is applicable at rank 2; Stable AC additionally checks the conditions in
[§1.2](#12-stable-ac-problem).

JSON type strictness: `1.0` is a float and is **not** a valid move id;
`true`/`false` are booleans, not integers; `"3"` is a string. All are
rejected with `E_BAD_MOVE_ID` at their index.

The submission receipt's top-level `accepted` means that the document
passed structural checks. It does **not** mean that any challenge was
solved. Only a solution with `results[i].ok: true` is verified and may
enter scoring. A mixed submission keeps its successful solutions even
when others fail; a structurally accepted document can contain no
successful solutions.

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
| `E_PATH_TOO_LONG` | more than `max_path_length` moves |
| `E_BAD_MOVE_ID` | non-integer or move outside the challenge specification (carries `move_index`) |
| `E_MOVE_NOT_APPLICABLE` | Stable AC: unavailable relator/generator, stabilization at rank 8, or failed destabilization condition (carries `move_index`, `move`, and `reason`) |
| `E_LENGTH_LIMIT` | intermediate total relator length exceeds the limit (carries `move_index`) |
| `E_WORK_BUDGET` | cumulative work exceeds `max_work` (carries `move_index`) |
| `E_NOT_TARGET` | every move legal but endpoint differs from the challenge target: `[[1],[2]]` for AC or `[]` for Stable AC (carries `final_shape`) |

**Check priority (frozen):** body byte limit → JSON parse →
client-asserted-result scan → structural shape → solutions count →
duplicates → then per solution: challenge lookup → path length → per-move
id → applicability → relator length → work budget → target. The first
triggered check is the one reported.

`E_MOVE_NOT_APPLICABLE.reason` is `relator_out_of_rank`,
`generator_out_of_rank`, `max_rank_exceeded`, or `destabilize_precondition`.

## 4. Limits

The same path limits apply to both Discovery problems. Upload quotas and
batch/body limits are shared per team across the entire Discovery Track.
A batch may mix `ac-v1-` and `sac-v1-` IDs; they are distinct challenges.

| Limit | v1 value |
|---|---:|
| Discovery submissions per team per UTC day (site + API combined) | 100 |
| `solutions` per submission | 500 |
| Raw body size | 4 MiB (4,194,304 bytes) |
| Optional top-level `notes` | 2,000 characters |
| `max_path_length` | 100 000 |
| `max_total_relator_length` | 10 000 |
| `max_work` = Σ per-step total relator length | 5 000 000 |

Path limits come from the manifest; structural limits have published
defaults in the reference parser and are supplied by the platform's
frozen configuration. A structurally accepted upload counts once toward
the daily quota, even if all its solutions fail verification. Structural
rejections do not count. Local self-checks do not consume platform quota.

The work budget exists because path length × relator length alone admits
~10⁹ character operations; the 424 AC training certificates have work ≤ 2 161
and their stable extensions have work ≤ 2 162, so
5 000 000 leaves three orders of magnitude of headroom while bounding
verification cost.

## 5. Hashes

The `move_spec_hash` is the SHA-256 of canonical JSON (sorted keys,
no whitespace, ASCII) for the `moves` array in the corresponding move
specification file. It covers the move table, not its explanatory notes.

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

`<target>` is `[[1],[2]]` for AC or `[]` for Stable AC. The two records
for a presentation have distinct IDs, targets, and instance hashes. Original
AC instance hashes are unchanged. The manifest hash covers all 20,230 records.

The `<ver>` in both templates is the official challenge's
`move_spec_version`. It remains part of the certificate hash but is
not a contestant-supplied submission field.

`manifest_hash` = SHA-256 of the canonical JSON of the sorted list of
all `instance_hash` values. `instance_hash` deliberately excludes
`base_score`, `status_at_freeze`, `source`, and `freeze_date`.
The manifest hash therefore identifies the encoded instances, not the
complete scoring policy or resource limits. Changing an excluded field
does not change this hash. Changing a challenge's encoded mathematical
data or the hashed move table changes the relevant hashes.

Official scoring must retain the complete frozen configuration, including
base scores, eligibility, limits, and scoring rules, identified by an
immutable release commit or an archived configuration snapshot. Each
scoring run must identify that configuration as well as the manifest and
verifier version. These are organizer records, not extra contestant fields.
The v1 base scores are all 1; any future policy change must be announced
and separately recorded, never silently substituted into old results.
Submissions are replayed against the official frozen challenges.

## 6. Scoring

Per challenge $i$: $V_i$ from the manifest;
$L_{t,i}$ = team $t$'s minimal accepted length;
$L^\star_i = \min_t L_{t,i}$;
$k_i = \#\{t : L_{t,i} = L^\star_i\}$;
$P_{t,i} = V_i\,2^{1-k_i}$ if $L_{t,i}=L^\star_i$, else 0;
$P_t = \sum_i P_{t,i}$.

Scores, totals, ranks, First Solver, and solved counters are computed
**separately for the AC and Stable AC problems**. There is no combined ranking.
Submission IDs and quota accounting remain shared; an event affects only
the leaderboard selected by its challenge.

Worked example ($V_i=1$):

| Stage | A | B | C | D | $L^\star$ | $k$ | Points |
|---|---:|---:|---:|---:|---:|---:|---|
| A first solves in 40 | 40 | – | – | – | 40 | 1 | A=1 |
| B matches 40 | 40 | 40 | – | – | 40 | 2 | A=B=1/2 |
| C matches 40 | 40 | 40 | 40 | – | 40 | 3 | each 1/4 |
| D finds **38** | 40 | 40 | 40 | 38 | 38 | 1 | **D=1, A/B/C drop to 0** |
| A matches 38 | 38 | 40 | 40 | 38 | 38 | 2 | A=D=1/2 |

A shorter verified path changes the current optimum and removes the
previous holders' points unless they match it. The leaderboard reports the
shortest path among accepted submissions; it is not a proof of mathematical
minimality.

The server timestamps each complete submission and assigns a monotonically
increasing `submission_id`. Accepted solutions are processed in the total
order `(received_at, submission_id)`, preserving array order within a
submission. Verification completion time does not decide priority.
If an earlier submission finishes verification later, replay the affected
history in this order before publishing the corrected leaderboard.

The leaderboard is recomputed **in full** after every accepted solution.
Scores are exact rationals end to end and displayed round-half-even to
4 decimal places. Rank by total descending, then by the earliest event
at which the current total was reached, then by immutable team ID for
an exact tie. The time-of-current-total resets whenever that team's
total changes in the ordered history, including changes caused by other
teams. Each `scoring_run` records the input event, configuration reference
from [§5](#5-hashes), `manifest_hash`, and verifier version; the accepted
event history must be retained so that the result can be reproduced.

**First Solver** is the team with the earliest `(received_at, submission_id)`
among verified solutions of a challenge, regardless of path length. A later
submission cannot take this record by finding a shorter path. A provisional
display may be corrected when an earlier submission is subsequently verified.
`current_best_solver` is the earliest submitter of the current minimum length;
this also uses receipt order, including equal-length submissions verified late.

`solved` counts the distinct scored challenges for which a team has any
verified solution. `current_best_count` counts those on which it currently
shares the shortest accepted length. Losing points to a shorter solution
does not erase a solved challenge or its First Solver record.

**Implementation status.** These are the official scoring requirements.
The development scoring engine still needs the ordered-replay fixes,
the separate solved/current-best counts, and complete configuration
references. Production integration must pass these checks before launch;
the local engine is not yet an end-to-end implementation of this section.

## 7. Disclosure and collaboration

Public per challenge during the competition: `status`,
`current_best_length`, `current_best_solver`, `first_solver`,
`first_solved_at`, `k_teams`, `base_score`, `certificate_hash`,
`peak_total_relator_length` (non-scoring), verified bridges (length,
team, time, hash). **Not public: move sequences, intermediate states,
or path statistics other than the explicitly listed length and peak.**
Teams may download only their own Discovery submissions during the
competition. The platform must enforce this with a public-field whitelist
and tests; this repository does not yet supply that production API.
All valid Discovery move sequences are published after the competition,
forming a reproducible public benchmark. A `certificate_hash` lets a team
identify a verified result publicly, for example in a preprint, while its move sequence remains private.

Sharing a specific Discovery certificate across teams is joint work and
must not be resubmitted as independent results by multiple teams. Discussion
and properly attributed use of ideas are allowed; they do not permit
copying a certificate into additional independently scoring teams. The
[competition overview](overview.md) contains the shared team, anti-cheating,
rules.

## 8. Bridge certificates

The planned Discovery bridge submission accepts
`{from_challenge_id, to_challenge_id, moves}`. The server determines
the move-spec version from the official challenges. Both endpoints must
use the same specification; a mixed pair is rejected with `E_SPEC_MISMATCH`.
Verified exactly as [§2](#22-verifier-semantics) with the target replaced by
`to_challenge.initial_relators` (exact ordered). A verified bridge is
listed on both challenges with its length, team, time, and hash;
its moves follow the same disclosure rules as other Discovery certificates.

The bridge itself scores nothing. A complete solution derived using a
bridge may be submitted in the ordinary `{challenge_id, moves}` format
and is verified and scored normally for that challenge, subject to the
[disclosure and collaboration rules](#7-disclosure-and-collaboration).
For example, a 10-move path from B to A plus a 40-move solution of A
gives a 50-move solution of B; if it is B's first
accepted solution, it earns B's full base score. Shortest-path scoring
does not prevent this. A bridge does not merge challenges in v1.
