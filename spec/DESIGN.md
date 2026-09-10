# The Andrews–Curtis Conjecture (ACC) Challenge — Internal Design Guide

The ACC Challenge is one competition on SAIR with **Discovery Track** (`discovery`)
and **Proof Track** (`proof`). Each has two problems: **AC** (`ac`) and
**Stable AC** (`stable_ac`). Discovery rewards short verified paths with
separate problem leaderboards. Proof accepts proofs or disproofs of either
full conjecture. Public versions and voluntary community peer review are
the main Proof workflow.

Registration is open on [SAIR](https://competition.sair.foundation/competitions/acc).
Discovery launches September 11, 2026 at 16:00 UTC; Proof launches September 20.
The local release status remains **prelaunch** until submission-release
requirements are met. Platform services are hosted by SAIR and require
separate integration checks; the local tools do not establish their readiness.

The contestant-facing entry point is [overview.md](../competition/rules/overview.md),
identical to the prelaunch page. [discovery.md](../competition/rules/discovery.md)
contains the Discovery task and evaluation contract;
[proof.md](../competition/rules/proof.md) contains the Proof task, full mathematical
statements, and public review and version rules.
This guide records implementation responsibilities and gaps, not a second
set of competition rules. Earlier designs remain available in Git history.

## 1. Mathematical definitions and move specification

### 1.1 Discovery encoding

The AC problem in Discovery uses an ordered pair of freely reduced words over
`1 = x`, `-1 = x^-1`, `2 = y`, and `-2 = y^-1`. No other letters occur in
this rank-two encoding. Free reduction scans left to right and cancels
adjacent inverse letters using a stack.

### 1.2 AC target

The target is exactly `[[1], [2]]`. Swapped or inverted basis tuples require
final moves. The published canonicalization table supplies shortest suffixes
for the eight signed basis tuples; the largest suffix has five moves.
Those moves count toward length and all resource limits.

### 1.3 AC moves

The authoritative table is [move_spec.json](../competition/tools/verifier/data/move_spec.json).
Its 14 move IDs describe inversion, right multiplication by the other relator
or its inverse, and conjugation by one generator letter or its inverse.
Every move has an inverse in the table. The Python implementation is
[core.py](../competition/tools/verifier/acms_verify/core.py).

`ac-r2-v1` is organizer-maintained metadata, not a field contestants select
or send with a solution. Published move IDs must not be silently reassigned.

### 1.4 Stable AC problem in Discovery

[stable_move_spec.json](../competition/tools/verifier/data/stable_move_spec.json)
defines `sac-r8-v1`: 257 operation IDs covering ranks
0–8. The count is 8 inversions + 112 right multiplications + 128
generator-letter conjugations + 1 stabilization + 8 destabilizations;
only IDs applicable to the current state may be used.
The first 14 IDs retain AC meanings. Stabilization adds a fresh generator
and its singleton relator; deletion requires an isolated positive singleton,
removes its generator, and renumbers the remaining generators. The target
is empty. `stable_core.py` implements replay; `specs.py` dispatches from
the challenge's specification. Out-of-rank moves fail applicability checks.

An AC path extended by `[16,15]` reaches empty, but it must still meet the
stable limits and be submitted under the stable challenge ID. No automatic
credit transfers between problems. The suffix adds two moves and one work unit.

### 1.5 Full conjectures

[AC.lean](../competition/tools/lean/AC.lean) defines `AC.Conjecture` and
`AC.StableConjecture` for every positive finite rank. The former fixes rank;
the latter permits finite sequences of stabilization and deletion without
any rank bound. Both use genuine presented-group triviality. Discovery's
rank and operational limits do not restrict these targets.

A formal bridge to Python's finite encoding is not an admission requirement.
A pool claim must identify its challenge and accurately map its words to
the mathematical presentation.

## 2. Problem statements, verifier data, and training

The public problem entry points are [ac.jsonl](../competition/problems/ac.jsonl)
and [stable_ac.jsonl](../competition/problems/stable_ac.jsonl). Each is a
JSON Lines file with **10,115** objects, one per line, containing only
`challenge_id` and `description` of the initial presentation.
They present the two problems over the same initial presentations.

The supporting [manifest](../competition/tools/verifier/data/manifest.json)
has **20,230 scored
challenges** over **10,115 presentations**, with `base_score = 1` each.
`ac-N` and `sac-N` share initial relators, with distinct targets,
specifications, and hashes. Renaming scored challenge IDs changes the
instance hashes, manifest hash, and any certificate hash tied to an older ID.
Hash algorithms, move tables, and presentation words are unchanged.
[training_424.json](../competition/examples/training_424.json) and
[stable_training_424.json](../competition/examples/stable_training_424.json)
contain the same **424
separate, unscored presentations**, certified under each specification.
These presentations and their training IDs are absent from both scored problem sets.
Readable training problem files are [examples/ac.jsonl](../competition/examples/ac.jsonl)
and [examples/stable_ac.jsonl](../competition/examples/stable_ac.jsonl), each with
424 records in the same format as the official problems. Their separate
[training manifest](../competition/examples/training_manifest.json) contains all
848 unscored challenges. The frozen training files retain their original IDs
and certificates; the manifest gives each Stable AC version a `sac-train-` ID.

`competition/tools/verifier/data/` also contains both move specifications,
`golden_vectors.json`, and `ms1190_metadata.csv`. These support replay and
reference checks; the CLI's `--manifest` option reads the manifest there.

`python3 build/build_problems.py` regenerates both problem files from the
committed verifier manifest, without private source data; `--check` rejects
missing or stale problem files. `build/build_manifest_v2.py` also generates
them when rebuilding the pool. Training JSONL files, the training manifest,
successful examples, and expected receipts are generated separately by
`build/build_examples.py` in `competition/examples/`.

`build/data/SOURCES.json` tracks the source release. `build/sync_dataset.py`
and `build/build_manifest_v2.py` regenerate the pool. Internal classifications
and the private ID map are excluded from the public package. This does not
promise that provenance cannot be inferred from public mathematical material.

An unresolved label records knowledge at the relevant cutoff, not a proof
of non-reachability. A successful replay certifies a path, not optimality.

## 3. Manifest, hashes, and reproducibility

### 3.1 Manifest responsibilities

The manifest supplies IDs, generators, relators, targets, move metadata,
instance hashes, scoring flags, base scores, replay limits, and lifecycle
metadata. Organizer data checks establish valid letters, reduced words,
unique IDs, consistent targets, and valid hashes before publication.

### 3.2 Instance and certificate identity

[canon.py](../competition/tools/verifier/acms_verify/canon.py) implements the
[public byte templates](../competition/tools/verifier/data/README.md#hash-specification).
An instance hash covers its ID, generators, relators,
target, and move metadata. A certificate hash covers its challenge ID,
official move version, and moves. It identifies a path, not authorship,
receipt time, independent discovery, or competition score.

### 3.3 Configuration identity

`move_spec_hash` covers the move table. `manifest_hash` covers the sorted
instance hashes; it does not cover every manifest field. Scoring flags,
base scores, limits, dates, and other policy metadata need a separate record.
Policy changes need not invalidate mathematical certificates, but cannot
silently change the configuration used to reproduce a leaderboard.

An official scoring run must identify an immutable complete configuration
snapshot or a verified freeze commit containing it, together with the
verifier version and ordered input events. This must preserve the dataset,
scoring policy, flags and base scores, and replay/submission limits.
**Implementation gap:** the in-memory engine currently records only
`manifest_hash`, verifier version, and an event key, not this complete record.

## 4. Discovery submissions and verification

### 4.1 Submission format

A submission is a UTF-8 `submission.txt` file. Each solution occupies one
line in the form `challenge_id: [move_id, ...]`. The ID is an ASCII letter
or digit followed by letters, digits, underscores, or hyphens. Spaces
around the ID, colon, and list entries are allowed. The move list uses
JSON array syntax; move values are checked by the selected verifier.

Following IGP24's comment convention, the first `#` on a line starts a
comment. Ignore everything from there to the end of that line, along with
blank lines and full-line comments. Notes may describe methods, sources,
links, or expected results, but never supply trusted result fields.
Comments do not affect replay, hashes, or points. The former JSON wrapper
and its `method`/`notes` fields are no longer accepted.

At least one solution line is required. Challenge IDs may repeat within
one file; matching AC and stable IDs are distinct and may be included
together. Non-comment text must parse as a solution; do not silently skip
a malformed line, even after an earlier success for its ID. Preserve file order after removing
comments. The public contract and
[submission.py](../competition/tools/verifier/acms_verify/submission.py)
define structural errors and their precedence: byte limit, UTF-8 decoding,
all line parsing, solution count, then per-record selection and verification.
Malformed-line errors include a one-based `line_number`.

### 4.2 Verifier and receipts

The service uses the same verifier sources as the public CLI: look up the
official challenge, replay each path, enforce limits, check the exact target,
and return length, work, and certificate hash. Outer `accepted` means
structural acceptance of the document; only per-solution `ok: true` is a
verified solution eligible for scoring. A failed path does not invalidate
other paths in a structurally valid batch.

After the entire file passes structural checks, process records in file
order. For each challenge ID, the first path returning `ok: true` is selected
for scoring from that upload. Earlier path failures do not block later
attempts. Once selected, later records for that ID are skipped without
replay, even if shorter. Return one result per record in file order; a skipped
row is `{challenge_id, ok: false, skipped: true, reason: "already_verified"}`.
Only `ok: true` results enter scoring. Skipped rows do not count as CLI
failures, but an actual failed attempt still yields exit code 1 even if a
later attempt succeeds. Selection resets for each upload; the existing
best-record scoring across uploads is unchanged.

The server assigns a UTC receipt time and a unique, monotonically increasing
submission ID to each complete submission. Verification completion time does not determine
priority. Persist inputs and results so retries and delayed verification
refer to the same recorded event.

Competition eligibility uses the complete server receipt in the selected
track's UTC window `[track_open, submission_deadline)`. Verification may finish after
the deadline without changing the original receipt or eligibility.

### 4.3 Limits

Current limits cover both problems together within Discovery Track: 40
submissions per team per UTC day, 500 solutions per submission, and a 10 MB
(10,000,000-byte) TXT file including comments. Verification limits are
100,000 moves per path, 10,000 letters in the reduced relator tuple, and
cumulative work of 5,000,000. Work includes the initial
length and each reduced state after a move. Structural rejection does not
consume quota. A structurally accepted document counts once even if every
path fails verification. The public contract governs accounting and error
precedence; the service must enforce quotas in addition to local replay limits.
Comments count toward the file byte limit but not the solution count, and
there is no separate comment-length limit. Every solution record counts
toward the 500-record cap, including repeated IDs and skipped records.
Path verification limits apply to records that are replayed.

These are Discovery acceptance limits. Exceeding them does not prove that a
presentation has no AC trivialization.

### 4.4 Runnable examples

[examples/README.md](../competition/examples/README.md) supplies a complete
training input, its manifest, a runnable command, a successful receipt, and
a separate scored-instance rejection example. Local verification does not
register a submission on SAIR.

## 5. Discovery scoring

### 5.1 Formula

Every scored challenge has a fixed base score of 1. If `k` distinct teams
share its shortest accepted path length, each receives `2^(1-k)` points;
other teams receive zero for that challenge. Multiple submissions from
the same team count only once. Totals sum only across scored
challenges for the selected problem; there is no combined ranking. Unsolved
challenges contribute zero. `ScoringEngine` takes a `move_spec_version`
selector and rejects an unselected mixed-spec manifest. Run one engine per
Discovery problem; it rejects challenges belonging to the other specification.

### 5.2 Ordered replay and publication

Use the UTC `received_at` and unique, monotonically increasing
`submission_id` assigned to each complete submission (§4.2).
Replay accepted events in server `(received_at, submission_id)` order,
never verification completion order. Within a submission, process only its
selected `ok: true` results, in file order, and publish the final batch
leaderboard atomically. Duplicate delivery of an event must not create extra results,
quota charges, or priority records.

Recompute the affected leaderboard in full after every accepted solution.
Rank by exact total descending, then time-of-current-total ascending.
Reset that timestamp whenever ordered replay changes a team's total,
including changes caused by other teams. If both tie, use
immutable team ID, not display name. Delayed results require rebuilding the
affected derived history before publishing the corrected leaderboard.

Each `scoring_run` records its input event, the immutable configuration
reference defined in §3.3, `manifest_hash`, and verifier version. Retain the
accepted-event history so every result can be reproduced.

**Implementation gaps:** `server/scoring/engine.py` currently updates these
clocks according to ingestion order, so the same events can produce different
tie rankings. An earlier receipt arriving later with an equal best length
also fails to update the best-length timestamp. Complete configuration
references remain missing (§3.3). Fix these before launch.

### 5.3 First Solver and counters

First Solver is the minimum `(received_at, submission_id)` among accepted
solutions for a challenge. A later-received shorter path cannot take away
that honor. An earlier pending submission that later verifies can correct
a provisional display; first completion is not first submission.

`current_best_solver` is the team with the earliest `(received_at, submission_id)`
among accepted solutions at the current shortest length.
Equal-length submissions verified late must also correct this choice.

`solved` counts distinct challenges for which a team has any accepted
solution. Being overtaken never removes a solved challenge. A separate
`current_best_count` records challenges on which the team attains `L_best`.
The earliest receipt for a team's current best length must survive
same-length retries and delayed processing.

**Implementation gap:** the engine derives `solved` from current points,
so being overtaken incorrectly removes a solved challenge.

### 5.4 No optimality claim

`L_best` is the best accepted competition record, not a certified globally
shortest path. Resource limits restrict which paths can enter that record.

### 5.5 Exact arithmetic

Use exact rational scores. Round half-even to four decimal places only for
display, never ranking. The engine already uses `fractions.Fraction` and
exact integer display rounding.

### 5.6 Regression scenarios

Use this worked example as a scoring regression case:

| Stage | A | B | C | D | Best length | $k$ | Points |
|---|---:|---:|---:|---:|---:|---:|---|
| A first solves in 40 | 40 | – | – | – | 40 | 1 | A=1 |
| B matches 40 | 40 | 40 | – | – | 40 | 2 | A=B=1/2 |
| C matches 40 | 40 | 40 | 40 | – | 40 | 3 | each 1/4 |
| D finds **38** | 40 | 40 | 40 | 38 | 38 | 1 | **D=1, A/B/C drop to 0** |
| A matches 38 | 38 | 40 | 40 | 38 | 38 | 2 | A=D=1/2 |

Add replay-order invariance, equal-length earlier receipts, duplicate
delivery, atomic batch publication,
permanent solved counts, and complete configuration replay to the existing
tests. A passing formula example alone does not verify event semantics.

## 6. Confidentiality, teams, and reuse

Discovery moves and intermediate states remain private during competition.
The platform's public challenge fields are `status`, `current_best_length`,
`current_best_solver`, `first_solver`, `first_solved_at`, `k_teams`,
`base_score`, and `certificate_hash`.
Enforce this allowlist in public API responses; authorize teams to retrieve
their own submissions. Publish valid move sequences after the competition.

Proof submissions, versions, and supporting materials are public on
submission, with no private/public toggle. Comments and any recognition
decisions are public when recorded. This does not change Discovery path
confidentiality.

The same team identity applies across both tracks and all their problems.
Each individual or organization may participate in only one team; teams
must register members and sponsors in advance. Detected coordinated
cheating, including sockpuppet teams, disqualifies all related teams.

Learning from public work is allowed. Identify borrowed arguments, code,
certificates, and comments; shared work must not be represented as
independent discovery. A certificate hash cannot establish independence:
provenance review remains an organizer responsibility.

## 7. Proof submissions, review, and credit

### 7.1 Targets

Select `ac` or `stable_ac`. Proof targets are `AC.Conjecture` and
`AC.StableConjecture`; disproof targets are their negations, equivalently
`AC.Counterexample` and `AC.StableCounterexample`. All quantify over positive
finite ranks, with no word/path bound. Stable rank may vary without a cap;
ordinary rank stays fixed. A counterexample may lie outside the pool.
Nonconstructive disproofs are eligible: these counterexample targets assert
existence and do not require an explicit witness.

### 7.2 Materials

Identify the conjecture, proof or disproof, authors/team, a description, and a complete
argument. The description, paper/PDF, GitHub repository containing Lean
work, arXiv paper, or a combination can carry that argument. Neither PDF
nor Lean is mandatory; an uploaded PDF must be at most 25 MB, as specified
in the public rules. Linked formal code identifies a fixed commit;
arXiv material identifies a specific version. A mutable link alone cannot
establish the contents of a past submission.

Require a rank and exact presentation only when a submission exhibits a
concrete counterexample, with a challenge ID if it is a pool instance.
The submission form must not require these fields for every disproof.

### 7.3 Public versions and comments

Assign every complete version an immutable server UTC receipt time and a
globally unique monotonic version ID. Order versions by `(received_at,
version ID)` without a separate sequence field. Preserve its
description, authors, change note, attachments, and the exact submitted
content of linked materials with hashes and fixed external revision IDs.
Never replace an earlier version with an updated PDF or branch. Comments
have an author, server timestamp, and identified submission version; retain
visible edit history when comments can change. Withdrawal marks a record
as withdrawn without deleting its history or asserting that its argument
is false. Post-deadline revisions may be published as noncompetitive
versions; they cannot backfill an earlier version's argument or priority.

The interaction is simple: publish a submission and invite voluntary
community peer review through comments underneath it. Participants may
examine arguments, raise objections, suggest improvements, and develop
new versions together. Publication does not assign an organizer reviewer
or place every submission in a screening or review queue.

### 7.4 Selective recognition and decisions

Organizers may select claims for assessment when considering competition
recognition, using community discussion as evidence. They do not undertake
to review every submission. A published version may remain without a formal
assessment.

For selected claims, `accepted`, `rejected`, `revision_requested`, and
`retracted` decisions bind to a specific version with a public reason.
Revisions do not erase earlier records. Correct or retract an accepted claim
when a substantive flaw is established, preserving its decision history.
Community discussion helps mathematical progress; comment counts, votes,
and successful Lean builds do not automatically confer acceptance.

### 7.5 Lean verification

The public project pins the statement, Lean toolchain, and Mathlib revision.
`lake build` builds the official statement. `lake build Check` optionally
runs semantic examples, a compiler check, and an axiom audit. Neither that
auxiliary command nor Lean itself is required for submission. Community
reviewers can inspect the actual theorem, definitions, scope, dependencies,
and axioms. A claim selected for recognition needs this scrutiny even when
it builds successfully. A restricted or different proposition is not the
official target.

### 7.6 Priority and contributions

When competition recognition is assessed, priority belongs to the earliest
eligible, non-withdrawn and non-retracted version confirmed to contain a
complete correct argument. Publication alone does not establish priority or
promise that a formal assessment will occur.
Eligibility uses its complete server receipt in the UTC window
`[track_open, submission_deadline)`; review may finish after the
deadline. An early placeholder or the time review finishes does not confer
priority. A material gap repaired in a later eligible version gives
that completed argument the later version's priority. Cosmetic revisions
do not erase an earlier complete and correct version's priority.

Authors identify borrowed submission versions, comments, papers, and code,
and describe their contribution. Credit may recognize original ideas,
essential completions, and substantive reviewer contributions. When assessing
recognition, organizers resolve disagreements using public history and evidence, without automatic
percentage allocations. Competition receipts do not replace scientific
priority established by earlier public work; an external publication date
does not replace the server receipt used for competition priority.
Withdrawn or retracted versions no longer hold competition priority,
but their historical contributions remain visible.

## 8. SAIR platform integration

The ACC adapter connects SAIR authentication, team IDs, receipts, storage,
and public pages to the mathematical verifier and scoring rules. It is
not yet implemented here. Existing SAIR capabilities are not working ACC
endpoints until integrated and tested.

| Area | Required behavior |
|---|---|
| Discovery submissions | Durable receipts, quotas, batch verification, and per-solution results |
| Discovery records | Team-private submissions and approved public challenge/leaderboard summaries |
| Proof submissions | Public immutable versions and their exact supporting materials |
| Proof discussion | Voluntary community peer review through attributed, version-linked comments and edit history |
| Proof recognition | Optional assessment of selected claims, with public version-specific reasons, priority, and contribution records |
| Replay | Rebuild scoring from immutable events and complete identified configuration |

Route mapping, database design, and authentication plumbing belong to the
adapter. Distinguish planned contracts from live endpoints. Discovery needs
an explicit public-field allowlist; publishing Proof material must not expose
unrelated private Discovery payloads.

## 9. Public release package

### 9.1 Public and internal sources

The IGP24-aligned public tree is `competition/`: `rules/`, two problem
statement files in `problems/`, training data and submissions in `examples/`,
the reference verifier with its supporting `data/`, and the Lean statements.
`competition.yaml` is
generated from the tracked manifest and `build/competition_state.json`; it
is ignored in the checkout and regenerated directly into every export.
A missing or stale local YAML file cannot block or alter an export. Internal scoring,
integration, private maps, and this guide are not in the export.

### 9.2 Lifecycle

`build/release.py --preview` writes an explicitly marked preview to
`dist/ACMS-public`. The default release command requires approved registration, Discovery opening,
and deadline timestamps and a verified Git data freeze. The Proof opening
timestamp may remain unset for the Discovery release; set it before enabling
Proof submissions. A finished release requires the Proof opening timestamp too. Maintain release state in
`build/competition_state.json` and synchronize generated metadata. During
prelaunch, `submissions_open` is `2026-09-11T16:00:00Z` and the exclusive
`submission_deadline` is `2026-12-01T12:00:00Z`, the end of November 30,
2026 AoE (UTC−12). `freeze_date`, `freeze_commit`, `registration_opens`,
and `prove_submissions_open` remain `null`. Calendar plans are separately
recorded in `announced_dates`: registration September 8, Discovery
September 11, Proof September 20, and the deadline November 30, 2026.
Exact track opening
uses track-level `opens_at`, supplied by `submissions_open` for Discovery and
`prove_submissions_open` for Proof. The internal date keys retain their
existing spelling; public track IDs are `discovery` and `proof`, with
nested `problems` entries `ac` and `stable_ac`.

### 9.3 Export checks

Release checks cover the common overview and track-guide routes, generated
problem statements, dataset hashes, examples and golden vectors, and the
Lean source/configuration snapshot. Exclude private maps, dependency caches,
and build products. This is not an end-to-end platform launch test or
certification of a contestant's argument. Rebuild the preview after public
sources change; do not distribute an older package as current rules.

## 10. Implementation status

| Component | Current status |
|---|---|
| 10,115 presentations in two Discovery problems and 424 disjoint training presentations | Published locally with data checks |
| Python verifier and successful training example | Implemented and runnable |
| Full ordinary and stable conjecture statements in Lean | Implemented; optional checks available |
| Preview/export and metadata gates | Implemented |
| Score formula and exact arithmetic | Implemented in an in-memory reference engine |
| Ordered replay, best-length receipt handling, solved count | Known gaps requiring correction before launch |
| Complete immutable scoring configuration record | Missing from the current engine |
| SAIR adapter, durable receipts, quotas, authorization | Integration outstanding |
| Public Proof versions, community comments, and selective recognition records | Platform implementation outstanding |

Local tests establish only the behavior they exercise. They do not show
that missing platform operations already exist.

## 11. Launch acceptance

Registration is already open. Validate each submission track before its own
launch; the September 11 Discovery launch does not require the September 20
Proof workflow to be ready. The published rules, generated metadata, export,
and enabled platform operations must agree for the track being opened.

### 11.1 Discovery — September 11, 2026 at 16:00 UTC

1. Both 10,115-challenge problem sets and their separate 424-instance training
   material reproduce expected hashes; examples run from the public export.
2. Actual SAIR authentication and team identity lead to durable receipts,
   shared quota enforcement, per-solution verification, and separate Discovery
   leaderboards. Mixed batches must not combine AC and Stable AC scores.
3. Accepted-event replay is independent of completion order; earlier
   same-length receipts, same-time IDs, event retries, and batches obey the rules.
   Repeated challenge IDs select only the first verified path in each file.
4. Solved counts survive shorter competing solutions. Current-best counts
   and First Solver remain separate and correctly computed.
5. Historical scoring reproduces from stored events and complete frozen
   configuration, including scoring flags and base scores.
6. Public Discovery responses exclude private moves and intermediate states;
   authorized teams can retrieve their own records.
7. Approved Discovery timing, deadline, and data freeze match the public
   rules and metadata. A future Proof opening date does not enable its endpoint.

### 11.2 Proof — September 20, 2026

1. Publish versions and fixed materials for voluntary community review, with
   comments and revisions; do not automatically queue every submission for
   organizer assessment.
2. Where selected recognition assessments are recorded, they identify the
   exact version, reasons, full target, prior work, and contributions.
   Priority distinguishes cosmetic edits from repairs of substantive gaps.
3. Set the approved Proof UTC opening time in `prove_submissions_open` and
   its track-level `opens_at` before enabling submissions; preserve the
   existing Discovery schedule and data freeze.
