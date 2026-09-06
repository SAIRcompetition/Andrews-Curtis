# Andrews–Curtis Conjecture Challenge (ACC) — Internal Design Guide

ACC is one competition on the SAIR competition platform, with a **Discovery
Track** and a **Prove Track**. Discovery rewards verified short trivialization
paths for specific presentations. Prove accepts arguments for or against the
full Andrews–Curtis conjecture. A Prove result neither automatically ends
Discovery nor converts into Discovery points.

The competition is **prelaunch**. Local data and mathematical checks are
available; online submission, official scoring, and public Prove review are
not yet implemented by this repository. SAIR is the decided host platform.
The remaining platform work is its ACC adapter and integration.

The contestant-facing contract is [evaluation.md](../competition/rules/evaluation.md),
with [overview.md](../competition/rules/overview.md) as its introduction and
[statement.md](../competition/rules/statement.md) as the mathematical target.
This guide records implementation responsibilities and gaps, not a second
set of competition rules. Earlier designs remain available in Git history.

## 1. Mathematical definitions and move specification

### 1.1 Discovery encoding

A Discovery state is an ordered pair of freely reduced words over
`1 = x`, `-1 = x^-1`, `2 = y`, and `-2 = y^-1`. No other letters occur in
this rank-two encoding. Free reduction scans left to right and cancels
adjacent inverse letters using a stack.

### 1.2 Exact target

The target is exactly `[[1], [2]]`. Swapped or inverted basis tuples require
final moves. The published canonicalization table supplies shortest suffixes
for the eight signed basis tuples; the largest suffix has five moves.
Those moves count toward length and all resource limits.

### 1.3 Atomic moves

The authoritative table is [move_spec.json](../competition/challenges/move_spec.json).
Its 14 move IDs describe inversion, right multiplication by the other relator
or its inverse, and conjugation by one generator letter or its inverse.
Every move has an inverse in the table. The Python implementation is
[core.py](../competition/tools/verifier/acms_verify/core.py).

`ac-r2-v1` is organizer-maintained metadata, not a field contestants select
or send with a solution. Published move IDs must not be silently reassigned.

### 1.4 Relation to the full conjecture

[AC.lean](../competition/tools/lean/AC.lean) defines the full Prove target for
every positive finite rank, using an ambient free group, genuine
presented-group triviality, and unbounded finite sequences of non-stable AC
moves. Discovery's rank and operational limits do not restrict this target.

The general target is defined directly; a formal bridge to the Python
14-move encoding is not an admission requirement. An argument about a pool
instance must identify it and accurately translate its words into the
mathematical presentation.

## 2. Challenge and training data

The current [manifest](../competition/challenges/manifest.json) has **10,115
scored challenges**, `ac-v1-00001` through `ac-v1-10115`, each with
`base_score = 1`. [training_424.json](../competition/challenges/training_424.json)
contains **424 separate, unscored instances** with replayable paths. The two
sets have no common initial presentation. Training IDs are absent from the
official scored manifest.

`build/data/SOURCES.json` tracks the source release. `build/sync_dataset.py`
and `build/build_manifest_v2.py` regenerate the pool. Internal classifications
and the private ID map are excluded from the public package. This does not
promise that provenance cannot be inferred from public mathematical material.

An unresolved label records knowledge at the relevant cutoff, not a proof
of non-reachability. A successful replay certifies a path, not optimality.

A bridge between two presentations receives no direct points. A full
trivialization derived by composing that bridge with another solution is an
ordinary Discovery submission and can score for its own challenge. Comparing
its length to a solution of a different challenge does not prevent this.

## 3. Manifest, hashes, and reproducibility

### 3.1 Manifest responsibilities

The manifest supplies IDs, generators, relators, targets, move metadata,
instance hashes, scoring flags, base scores, replay limits, and lifecycle
metadata. Organizer data checks establish valid letters, reduced words,
unique IDs, consistent targets, and valid hashes before publication.

### 3.2 Instance and certificate identity

[canon.py](../competition/tools/verifier/acms_verify/canon.py) implements the
public byte templates. An instance hash covers its ID, generators, relators,
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

A JSON document contains a nonempty `solutions` array. Each entry has
exactly `challenge_id` and `moves`; optional `method` and `notes` belong to
the outer document. Contestants supply no version or claimed result fields.
Duplicate challenge IDs within one document are rejected. The public
contract and [submission.py](../competition/tools/verifier/acms_verify/submission.py)
define structural errors and their precedence.

### 4.2 Verifier and receipts

The service uses the same verifier sources as the public CLI: look up the
official challenge, replay each path, enforce limits, check the exact target,
and compute length, peak, work, and certificate hash. Outer `accepted` means
structural acceptance of the document; only per-solution `ok: true` is a
verified solution eligible for scoring. A failed path does not invalidate
other paths in a structurally valid batch.

The server assigns a UTC receipt time and a unique, monotonically increasing
submission ID to each complete submission. Verification completion time does not determine
priority. Persist inputs and results so retries and delayed verification
refer to the same recorded event.

Competition eligibility uses the complete server receipt in the UTC window
`[submissions_open, submission_deadline)`. Verification may finish after
the deadline without changing the original receipt or eligibility.

### 4.3 Limits

Current limits are 100 submissions per team per UTC day, 500 solutions per
submission, a 4 MiB (4,194,304-byte) body, 100,000 moves per path, 10,000 letters in the
reduced pair, and cumulative work of 5,000,000. Work includes the initial
length and each reduced state after a move. Structural rejection does not
consume quota. A structurally accepted document counts once even if every
path fails verification. The public contract governs accounting and error
precedence; the service must enforce quotas in addition to local replay limits.

These are Discovery acceptance limits. Exceeding them does not prove that a
presentation has no AC trivialization.

### 4.4 Bridge certificates

A bridge names two official challenge IDs and a move list. Replay uses the
second challenge's initial relators as the exact target. Record a verified
bridge against both problems, without direct points. A derived full solution
is scored normally (§2). No automatic merging of challenge scores is implied.

### 4.5 Runnable examples

[examples/README.md](../competition/examples/README.md) supplies a complete
training input, its manifest, a runnable command, a successful receipt, and
a separate scored-instance rejection example. Local verification does not
register a submission on SAIR.

## 5. Discovery scoring

### 5.1 Formula

For challenge `i`, `V_i` is its base score, `L[t,i]` is a team's shortest
accepted path, `L_best[i]` is the minimum across teams, and `k[i]` counts
teams attaining that minimum. Such a team receives `V_i * 2^(1-k[i])`;
other teams receive zero for that challenge. Totals sum across scored
challenges; unsolved challenges contribute zero. The formula is unchanged.

### 5.2 Ordered replay and publication

Replay accepted events in server `(received_at, submission_id)` order,
never verification completion order. Within a submission, process solutions
in their original array order and publish the final batch leaderboard
atomically. Duplicate delivery of an event must not create extra results,
quota charges, or priority records.

Rank by exact total descending, then time-of-current-total ascending. That
time changes when ordered replay changes a team's total, including changes
caused by other teams. If both tie, use immutable team ID, not display name.
Delayed results require rebuilding the affected derived history.

**Implementation gaps:** `server/scoring/engine.py` currently updates these
clocks according to ingestion order, so the same events can produce different
tie rankings. An earlier receipt arriving later with an equal best length
also fails to update the best-length timestamp. Fix both before launch.

### 5.3 First Solver and counters

First Solver is the minimum `(received_at, submission_id)` among accepted
solutions for a challenge. A later-received shorter path cannot take away
that honor. An earlier pending submission that later verifies can correct
a provisional display; first completion is not first submission.

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

Retain the public worked scoring example. Add replay-order invariance,
equal-length earlier receipts, duplicate delivery, atomic batch publication,
permanent solved counts, and complete configuration replay to the existing
tests. A passing formula example alone does not verify event semantics.

## 6. Confidentiality, teams, and reuse

Discovery moves and intermediate states remain private during competition.
Publish only the evaluation contract's allowed fields: lengths, solver
records, approved non-scoring statistics, and bridge summaries. Teams can
inspect their own submissions. Publish valid certificates at the announced
post-competition release point.

Prove submissions, versions, supporting materials, decisions, and comments
are public on submission, with no private/public toggle. This does not
change Discovery path confidentiality.

The same team identity applies across both tracks. Apply the public rules
on membership, no multiple-team participation, and no merging after a team
has submitted. Learning from public work is allowed. Identify borrowed
arguments, code, certificates, and comments; shared work must not be
represented as independent discovery. A certificate hash cannot establish
independence: provenance review remains an organizer responsibility.

## 7. Prove submissions, review, and credit

### 7.1 Common target

A proof establishes the full arbitrary-positive-rank non-stable conjecture.
A disproof establishes its negation: some balanced presentation of the
trivial group has no finite standard AC path to its standard tuple. It can
lie outside the Discovery pool. The Lean targets are `AC.Conjecture` and
`¬ AC.Conjecture`; `AC.Counterexample` is the equivalent witness form.

### 7.2 Materials

Identify proof or disproof, authors/team, a description, and a complete
argument. The description, paper/PDF, GitHub repository containing Lean
work, arXiv paper, or a combination can carry that argument. Neither PDF
nor Lean is mandatory; an uploaded PDF must be at most 25 MB, as specified
in the public rules. Linked formal code identifies a fixed commit;
arXiv material identifies a specific version. A mutable link alone cannot
establish the contents of a past submission.

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

The interaction is simple: publish a submission and let participants
comment underneath it. No separate peer-review portal or elaborate
assignment workflow is required.

### 7.4 Decisions

`accepted`, `rejected`, `revision_requested`, and `retracted` decisions bind
to a specific version with a public reason. Revisions do not erase earlier
records. Correct or retract an accepted claim when a substantive flaw is
established, preserving the prior decision and reason. Community comments
inform organizer decisions; votes and builds do not decide correctness.

### 7.5 Lean verification

The public project pins the statement, Lean toolchain, and Mathlib revision.
`lake build` builds the official statement. `lake build Check` optionally
runs semantic examples, a compiler check, and an axiom audit. Neither that
auxiliary command nor Lean itself is required for submission. Formal work
still needs review of its actual theorem, definitions, scope, dependencies,
and axioms. A restricted or different proposition is not the official target.

### 7.6 Priority and contributions

Competition priority belongs to the earliest eligible, non-withdrawn and
non-retracted version confirmed to contain a complete correct argument.
Eligibility uses its complete server receipt in the UTC window
`[submissions_open, submission_deadline)`; review may finish after the
deadline. An early placeholder or the time review finishes does not confer
priority. A material gap repaired in a later eligible version gives
that completed argument the later version's priority. Cosmetic revisions
do not erase an earlier complete and correct version's priority.

Authors identify borrowed submission versions, comments, papers, and code,
and describe their contribution. Credit may recognize original ideas,
essential completions, and substantive reviewer contributions. Organizers
resolve disagreements using public history and evidence, without automatic
percentage allocations. Competition receipts do not replace scientific
priority established by earlier public work; an external publication date
does not replace the server receipt used for competition priority.
Withdrawn or retracted versions no longer occupy competition priority or
honors, but their historical contributions remain visible.

### 7.7 Relationship to Discovery

Recognize Prove achievements separately from Discovery points, within the
same competition. A proof need not supply short paths; a disproof does not
invalidate verified paths for other presentations. Neither automatically
stops Discovery. However, a valid path and a valid non-reachability claim
for the same presentation cannot both hold; nor can a full proof and a
full disproof. Review must check these conflicts and record corrections.

## 8. SAIR platform integration

The ACC adapter connects SAIR authentication, team IDs, receipts, storage,
and public pages to the mathematical verifier and scoring rules. It is
not yet implemented here. Existing SAIR capabilities are not working ACC
endpoints until integrated and tested.

| Area | Required behavior |
|---|---|
| Discovery submissions | Durable receipts, quotas, batch verification, and per-solution results |
| Discovery records | Team-private submissions and approved public challenge/leaderboard summaries |
| Bridges | Verified records without direct points |
| Prove submissions | Public immutable versions and their exact supporting materials |
| Prove discussion | Attributed, version-linked comments and edit history |
| Prove decisions | Public version-specific reasons, priority, and contribution records |
| Replay | Rebuild scoring from immutable events and complete identified configuration |

Route mapping, database design, and authentication plumbing belong to the
adapter. Distinguish planned contracts from live endpoints. Discovery needs
an explicit public-field allowlist; publishing Prove material must not expose
unrelated private Discovery payloads.

## 9. Public release package

### 9.1 Public and internal sources

The IGP24-aligned public tree is `competition/`: rules, challenge data,
examples, reference verifier, Lean statement, and metadata. Internal scoring,
integration, private maps, and this guide are not in the export.

### 9.2 Lifecycle

`build/release.py --preview` writes an explicitly marked preview to
`dist/ACMS-public`. The default release command requires a complete approved
schedule and verified Git data freeze. Maintain release state in
`build/competition_state.json` and synchronize generated metadata. During
prelaunch, unannounced dates and `freeze_commit` remain `null`.

### 9.3 Export checks

Release checks cover dataset hashes, examples and golden vectors, and the
Lean source/configuration snapshot. Exclude private maps, dependency caches,
and build products. This is not an end-to-end platform launch test or
certification of a contestant's argument. Rebuild the preview after public
sources change; do not distribute an older package as current rules.

## 10. Implementation status

| Component | Current status |
|---|---|
| 10,115 scored instances and 424 disjoint training instances | Published locally with data checks |
| Python verifier and successful training example | Implemented and runnable |
| Full conjecture statement in Lean | Implemented; optional checks available |
| Preview/export and metadata gates | Implemented |
| Score formula and exact arithmetic | Implemented in an in-memory reference engine |
| Ordered replay, best-length receipt handling, solved count | Known gaps requiring correction before launch |
| Complete immutable scoring configuration record | Missing from the current engine |
| SAIR adapter, durable receipts, quotas, authorization | Integration outstanding |
| Bridge service and public/private serialization | Integration outstanding |
| Public Prove versions, materials, comments, decisions, priority | Platform implementation outstanding |

Local tests establish only the behavior they exercise. They do not show
that missing platform operations already exist.

## 11. Launch acceptance

In addition to existing mathematical and data checks, launch requires:

1. The 10,115-instance manifest and separate 424-instance training material
   reproduce expected hashes; examples run correctly from the public export.
2. Actual SAIR authentication and team identity lead to durable receipts,
   quota enforcement, per-solution verification, and leaderboard publication.
3. Accepted-event replay is independent of completion order; earlier
   same-length receipts, same-time IDs, duplicates, and batches obey the rules.
4. Solved counts survive shorter competing solutions. Current-best counts
   and First Solver remain separate and correctly computed.
5. Historical scoring reproduces from stored events and complete frozen
   configuration, including scoring flags and base scores.
6. Public Discovery responses exclude private moves and intermediate states;
   authorized teams can retrieve their own records.
7. Bridges use exact destination presentations and score zero themselves;
   derived full solutions receive ordinary Discovery scoring.
8. Prove preserves public versions, fixed materials, comments, decisions,
   reasons, and revisions. Priority distinguishes cosmetic edits from repairs
   of substantive gaps.
9. Review checks the full target, prior work, borrowed contributions, and
   conflicts with accepted results, including same-presentation Discovery paths.
10. Approved schedule, freeze, public rules, generated metadata, exported
    package, and actual enabled platform operations agree.

Official registration and scoring remain closed until these requirements
and the announced release process have been satisfied.
