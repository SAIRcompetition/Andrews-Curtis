# Andrews–Curtis Conjecture Challenge — Evaluation and Rules

**Prelaunch preview.** This document specifies verification, scoring,
and confidentiality for the planned competition. Local verification
is available now; registration, online submissions, and official
scoring are not open. The competition service is planned to use the
reference verifier sources in `tools/verifier/`; its server-side
verdicts will be the authority for Discovery results once submissions open.

ACC is one competition with **Discovery Track** and **Proof Track**. Each
contains **AC** and **Stable AC** problems. Sections 1–8 specify Discovery;
§9 specifies Proof, which accepts proofs and disproofs of either
[mathematical statement](statement.md). Proof submissions and versions are
public from receipt, with comments for community review. Discovery move
sequences remain private during competition and are released afterwards (§7).

Announced calendar dates are September 8, 2026 for registration, September
11 for Discovery Track, September 20 for Proof Track, and
November 30 for the submission deadline. Exact UTC opening and deadline
times, certificate release, and official freeze remain to be set. Their
timestamp fields remain `null`; status remains `prelaunch` until the
release requirements are met.
`submissions_open` is Discovery's UTC opening; `prove_submissions_open` is
Proof's. Each track's `opens_at` uses its corresponding timestamp.

For each track, eligibility uses the time the server receives the complete
submission: at or after that track's published UTC opening time and before
`submission_deadline`. Verification or review may finish after the deadline.
A late Discovery submission earns no points; Proof corrections after the
deadline are addressed in §9.6. A calendar date alone does not open an endpoint.

For a complete local success case and expected receipt, see the
[training example](../examples/README.md). It uses an unscored example
manifest and does not count as a competition submission.

## 1. Encoding and frozen objects

The challenge determines the move specification: `ac-v1-` IDs use
`ac-r2-v1`; `sac-v1-` IDs use `sac-r8-v1`. Corresponding IDs contain the
same initial presentation. The manifest has 20,230 challenge records for
10,115 presentations, scored separately for the AC and Stable AC problems.

### 1.1 AC problem

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

All 257 rows are in `challenges/stable_move_spec.json`; its `moves` array
is hashed as in §1.1. A move may name only existing relators and generators.
Stabilization requires $k<8$. Destabilization requires the selected relator
to be exactly a single positive generator $g$, absent from every other
relator. It deletes that relator and generator, then renumbers generators
above $g$ down by one, preserving the order of the remaining relators.

The rank cap is frozen in `sac-r8-v1`. It restricts this search benchmark,
not the stable conjecture of §9. From a signed permutation of the $k$
generators, invert negative relators and then destabilize from the highest
relator index down; the shortest finish has $k$ plus the number of negative
relators moves. From either `(x,y)` or `(y,x)`, the suffix is `[16,15]`.

An AC solution followed by `[16,15]` reaches the stable target. It is
accepted for the Stable AC problem only if the extended path also satisfies
its limits: the suffix adds two moves and one unit of work. Submit it
under the corresponding `sac-v1-` ID; points do not transfer between problems.

## 2. Verifier semantics

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
is applicable at rank 2; Stable AC additionally checks the conditions in §1.2.

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
id → applicability → relator length → work budget → target. The first triggered check
is the one reported.

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
| `max_path_length` | 100 000 |
| `max_total_relator_length` | 10 000 |
| `max_work` = Σ per-step total relator length | 5 000 000 |

Path limits come from the manifest; structural limits have published
defaults in the reference parser and are supplied by the platform's
frozen configuration. A structurally accepted upload counts once toward
the daily quota, even if all its solutions fail verification. Structural
rejections do not count. Local self-checks do not consume platform quota.

The work
budget exists because path length × relator length alone admits ~10⁹
character operations; the 424 AC training certificates have work ≤ 2 161
and their stable extensions have work ≤ 2 162, so
5 000 000 leaves three orders of magnitude of headroom while bounding
verification cost.

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
from §5, `manifest_hash`, and verifier version; the accepted event history
must be retained so that the result can be reproduced.

**First Solver** is the team with the earliest `(received_at, submission_id)`
among verified solutions of a challenge, regardless of path length. A later
submission cannot take this honor by finding a shorter path. A provisional
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

## 7. Discovery disclosure and collaboration

Public per challenge during the competition: `status`,
`current_best_length`, `current_best_solver`, `first_solver`,
`first_solved_at`, `k_teams`, `base_score`, `certificate_hash`,
`peak_total_relator_length` (non-scoring), verified bridges (length,
team, time, hash). **Not public: move sequences, intermediate states,
or path statistics other than the explicitly listed length and peak.**
Teams may download only their own Discovery submissions during the
competition. The platform must enforce this with a public-field whitelist
and tests; this repository does not yet supply that production API.
All valid Discovery certificates are published at the announced
post-competition `certificate_release` time. This embargo does not apply
to Proof submissions, which are public under §9.

### Team Participation and Anti-Cheating Policy

- Each individual or organization can participate in only one team.
- Teams must register members and sponsors in advance.
- If coordinated cheating is detected (including sockpuppet teams), all related teams will be disqualified.

### Collaboration and attribution

Sharing a specific Discovery certificate across teams is joint work and
must not be resubmitted as independent results by multiple teams.
Discussion, public Proof review, and properly attributed use of ideas
are allowed; they do not create an exception for copying Discovery
certificates into additional independently scoring teams.

The public dataset omits internal per-instance difficulty labels and
provenance mappings. This is not a guarantee of anonymity: contestants
may recognize presentations or match them to public mathematical sources.

## 8. Bridge certificates

The planned Discovery bridge submission accepts
`{from_challenge_id, to_challenge_id, moves}`. The server determines
the move-spec version from the official challenges. Both endpoints must
use the same specification; a mixed pair is rejected with `E_SPEC_MISMATCH`.
Verified exactly as §2 with the target replaced by
`to_challenge.initial_relators` (exact ordered). A verified bridge is
listed on both challenges with its length, team, time, and hash;
its moves follow the same disclosure rules as other Discovery certificates.

The bridge itself scores nothing. A complete solution derived using a
bridge may be submitted in the ordinary `{challenge_id, moves}` format
and is verified and scored normally for that challenge, subject to §7's
collaboration rules. For example, a 10-move path from B to A plus a
40-move solution of A gives a 50-move solution of B; if it is B's first
accepted solution, it earns B's full base score. Shortest-path scoring
does not prevent this. A bridge does not merge challenges in v1.

## 9. Proof Track

### 9.1 What is claimed

Select `ac` or `stable_ac`. A **proof** establishes that conjecture for
all positive finite ranks. A **disproof** establishes its negation. In
classical logic this is equivalent to proving the existence of a balanced
presentation of the trivial group that cannot reach its
standard presentation under the relevant full, unbounded relation.
For ordinary AC the rank stays fixed; Stable AC permits adding and removing
trivial generator–relator pairs with no rank cap. See [statement.md](statement.md).

A disproof may exhibit a concrete counterexample or prove that one exists
nonconstructively. If a submission gives a concrete counterexample, identify
its rank and exact presentation; name the challenge if it is a pool instance.
A counterexample may lie outside the Discovery pool. A nonconstructive
disproof need not identify a particular rank, presentation, or challenge ID.

An AC proof also proves Stable AC; a Stable AC disproof also disproves AC.
An AC disproof alone does not settle Stable AC, and a Stable AC proof alone
does not settle AC. Failure to find a path, or a proof excluding only paths
within a length, word-size, rank, or move restriction, does not by itself
disprove the full conjecture. Solving the finite pool is not a proof of either.

### 9.2 Submission materials

The Proof submission page will collect the following when submissions open:

| Field | Requirement |
|---|---|
| `conjecture` | `ac` or `stable_ac`, selecting the problem within Proof Track |
| `claim_type` | `proof` or `disproof` |
| `description` | State the claim, its scope, the argument or its outline, and the authors' contribution |
| Supporting materials | Paper/PDF, GitHub link for a Lean formalization, arXiv link, or a combination, as needed to supply the complete argument |
| Attribution | Identify prior work, submissions, versions, or comments used and explain their contribution; include this in the description or argument |

The description may contain the full argument itself. Otherwise the
supporting materials must supply it. PDF and Lean are both optional;
an uploaded PDF must be ≤ 25 MB. A title, claim announcement, or search
log without a complete argument cannot earn acceptance or priority.
The submitted materials and cited public references must give reviewers
access to the argument and all assumptions on which it depends.

GitHub materials must identify a fixed commit and the theorem and build
instructions to check. arXiv materials must identify a specific version
such as `v2`. The platform records the actual submitted content under §9.4;
changing an external link's target later does not revise that record.
The team and authors are associated with the submission by the platform.
The platform assigns version identifiers and timestamps; contestants do
not add a version selector to the official mathematical statement.

### 9.3 Official statement and Lean verification

The [official statements](statement.md) cover every positive finite rank.
Both are defined in `tools/lean/AC.lean`, using free groups and
`Subsingleton (PresentedGroup (Set.range R))` for presented-group triviality.

| Problem | Proof target | Disproof target | Equivalent existence statement |
|---|---|---|---|
| AC | `AC.Conjecture` | `¬ AC.Conjecture` | `AC.Counterexample` |
| Stable AC | `AC.StableConjecture` | `¬ AC.StableConjecture` | `AC.StableCounterexample` |

Ordinary reachability fixes the rank. Stable reachability permits finite
sequences of rank changes without any bound on rank or intermediate word
size. Discovery's 14/257 move encodings and resource limits do not restrict
these targets. If a claim uses a pool presentation, it must map its words
accurately to the mathematical tuple. No contestant-supplied version field
selects or changes a statement.

Descriptions, papers, and formalizations address the same selected target.
Lean is a means of verification, not an exemption from review. A
successful build does not automatically accept a mathematical claim:
reviewers must examine the exact theorem, its scope, dependencies,
axioms, and trust boundary.

The local project pins Lean `4.29.1` and Mathlib commit
`5e932f97dd25535344f80f9dd8da3aab83df0fe6`. Its
`statement-lock.json` records source and dependency SHA-256 snapshots.
Follow the [project guide](../tools/lean/README.md) to acquire the
pinned cache and run `lake build`, which builds only `AC`. A
formalization imports `AC`; the release process separately checks the
source snapshot.

`lake build Check` optionally runs semantic examples, the compiler-hash
check, and an axiom audit against `propext`, `Classical.choice`, and
`Quot.sound`. This auxiliary target is not a submission requirement.
Online submissions remain closed during prelaunch.

### 9.4 Public versions and comments

Every Proof submission is public from receipt. A submission page contains
the description, materials, author and team attribution, version history,
comments, and review decisions. Other participants may comment, question
an argument, suggest corrections, and learn from it. Comments and author
responses identify the version they discuss and carry server timestamps;
substantive edits retain an accessible history.

The server assigns each complete submitted version an immutable,
globally unique, monotonically increasing version ID and a UTC
`received_at`; the ID breaks equal-time ties. It preserves that version's
description, authors, supplied files,
and the submitted content of linked arguments, together with content
hashes and fixed external revision identifiers. A replacement PDF or
changed argument is a new version linked to its predecessor. Older
versions, comments, and decisions remain accessible. Withdrawal marks
the record as withdrawn rather than erasing it.

Submission publication and a receipt timestamp are records of a claim;
they do not certify its correctness.

### 9.5 Review and decisions

Review is carried out by the organizers and reviewers they designate,
informed by public comments and the authors' responses. Community
discussion is open; acceptance is an organizer decision, not a vote
count or a successful Lean build. No turnaround is guaranteed.

| State | Meaning for the identified version |
|---|---|
| `received` | The version has been recorded and published |
| `screening` | Organizers check scope and substantive mathematical content |
| `under_review` | The argument is being assessed |
| `accepted` | The stated proof or disproof has been accepted, with a public review explanation |
| `rejected` | The claim has been declined, with a reason |
| `revision_requested` | Reviewers request changes; a submitted revision creates a new version at `received` |
| `withdrawn` | The authors have withdrawn this version from review and competition recognition; its history and contribution record remain visible |
| `retracted` | Organizers have withdrawn a prior acceptance, with a public explanation |

Decisions identify the exact version, the reviewers or responsible
organizers, the decision time, and the reasons. A newer version does
not inherit acceptance automatically or delete the assessment of an
older version. Organizers may correct a decision when a substantive
error is established; the previous decision, explanation, and correction
remain part of the record. A substantive objection to an accepted
version is displayed while it is reviewed, and any recognition based
on a withdrawn or retracted version is updated accordingly. Withdrawal
does not itself establish that an argument was mathematically incorrect.

### 9.6 Priority and contribution credit

Priority belongs to the **earliest submitted version that review confirms
already contains a complete, correct argument** for the stated result.
Order qualifying versions by server `(received_at, version ID)`,
not by the time review finishes or by an external publication date.
Publication dates remain relevant scholarly attribution, but they do not
replace the competition's receipt record. Only versions received within
the announced competition submission window qualify for competition
priority; review may continue after the deadline. Later corrections may
be published and reviewed as non-competitive versions, but cannot create
or backdate an eligible version. Withdrawn or retracted versions do not
hold competition priority; their recorded historical contributions remain
attributable.

An incomplete announcement cannot reserve priority. If a later version
supplies a missing essential argument, that later version's receipt time
applies. If an earlier version was already complete and correct, later
wording or exposition changes do not erase its established priority.
The review explanation identifies the earliest qualifying version and
why it qualifies. Recognition may be corrected if subsequent review
validates an earlier version or retracts a previously accepted one.

Priority and contribution credit are recorded separately. Authors must
cite the particular submissions, versions, papers, code, and comments
they used and explain their contribution. For example, if a public
comment supplies a key lemma used in a revision, that contribution
must be acknowledged even when the original authors submit the completed
argument. Reviewers consider these records when recognizing contributions
or resolving attribution disputes. The platform does not automatically
assign contribution percentages or turn a comment into coauthorship.
`Independent Confirmation` is reserved for later accepted work whose
independence has been established; a disclosed extension or correction
of another submission is credited as such.

### 9.7 Recognition and the tracks

For each conjecture, the first qualifying proof **or** disproof is recognized as the
**Highest Mathematical Achievement of the Competition**, with its
qualifying version, receipt time, contributors, and review explanation.
Other accepted work and substantive contributions receive attribution
appropriate to their role. Proof recognition does not convert into
Discovery points.

A qualifying AC proof is recognized for both conjectures, as is a qualifying
Stable AC disproof. The same submitted version and receipt time support
both recognitions once reviewers confirm the implication; no second upload
or later review time resets its priority. Shared authorship and contributions
remain attached to that version.

An accepted proof or disproof does not automatically close Discovery,
change its scoring rule, or invalidate correct finite move certificates.
A purported counterexample conflicts with a verified path under the same
relation; a Stable AC counterexample conflicts with either kind of path.
An ordinary AC counterexample can coexist with a stable trivialization.
Reviewers must check the exact presentation, claimed relation, and verifier
before recording a contradiction. Any correction must be explained publicly;
incompatible conclusions cannot both remain endorsed.

The planned platform flow is a public submission page with version
history, comments, and organizer decisions. The local repository supplies
the mathematical statement and reference tools; the SAIR integration,
version storage, comments, and review workflow still require implementation
and end-to-end acceptance checks before launch.
