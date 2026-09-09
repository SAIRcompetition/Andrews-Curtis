# Proof Track

Submit a proof or disproof of the full **AC** or **Stable AC** conjecture.
Proof Track opens on **September 20, 2026**; the submission deadline is
**November 30, 2026**. See the [competition overview](overview.md) for the
official schedule, registration, teams, and common participation rules.

## Claims

Select `ac` or `stable_ac`. A proof establishes the selected conjecture
for every positive finite rank. A disproof establishes its negation; it
may exhibit a counterexample or prove that one exists nonconstructively.
An explicit rank, presentation, or challenge ID is not required for a
nonconstructive disproof.

For either route, a counterexample must present the trivial group and
admit no finite path to the standard presentation under the selected
conjecture's full relation.
Failure to find a path, or a proof excluding only paths within a length,
word-size, rank, or move restriction, does not by itself establish this.
Solving a finite collection of presentations does not prove either conjecture.

The mathematical statements below apply equally to descriptions, papers,
PDFs, and Lean arguments. The shared formal definitions are in
[AC.lean](../tools/lean/AC.lean), under namespace `AC`.

## Ordinary AC

Let $n\ge1$ be any finite positive rank and
$F_n=\langle x_0,\ldots,x_{n-1}\rangle$ the free group on $n$ generators.
An ordered relator tuple $R=(r_0,\ldots,r_{n-1})\in F_n^n$ defines

$$P_R=\langle x_0,\ldots,x_{n-1}\mid r_0,\ldots,r_{n-1}\rangle
      =F_n/\langle\!\langle r_0,\ldots,r_{n-1}\rangle\!\rangle.$$

The standard tuple is $X=(x_0,\ldots,x_{n-1})$. Each elementary move
changes one relator, leaving all others fixed:

- **Inversion:** $r_i\leftarrow r_i^{-1}$.
- **Right multiplication:** $r_i\leftarrow r_i r_j$, for $i\ne j$.
- **Conjugation:** $r_i\leftarrow w r_i w^{-1}$, for any $w\in F_n$.

Equality is equality in the free group, including free cancellation.
Rank stays fixed: no generator–relator pair is added or removed.
Reachability means a finite sequence of moves, including the empty sequence,
with no bound on its length or the sizes of intermediate words.

**Conjecture.** For every $n\ge1$ and every $R\in F_n^n$, if $P_R$ is
the trivial group, then $R$ can be transformed into $X$ by these moves.

A **counterexample** is a positive rank $n$ and a tuple $R$ for which
$P_R$ is trivial but $X$ is not reachable from $R$.

Left multiplication follows in two moves: with $a=r_i$ and $b=r_j$
($i\ne j$), right-multiply and then conjugate by the unchanged $b$,
giving $a\to ab\to b(ab)b^{-1}=ba$.
Multiplication by inverse relators and relator permutations are also
derivable, so the ordered standard endpoint adds no restriction.
Arbitrary-word conjugation is a finite composition of conjugations by
generators and their inverses. These conventions agree with
[Lackenby, §1](https://arxiv.org/html/2606.06122v1#S1).

## Stable AC

In addition to ordinary AC moves, allow **stabilization**:

$$\langle x_0,\ldots,x_{n-1}\mid r_0,\ldots,r_{n-1}\rangle
\longrightarrow
\langle x_0,\ldots,x_{n-1},z\mid r_0,\ldots,r_{n-1},z\rangle.$$

Here $z$ is fresh. The reverse deletes a generator $z$ and a relator
that is exactly $z$ when no other relator contains $z$ or $z^{-1}$.
The display appends the pair for convenience; the Lean definition permits
insertion at any generator and relator positions, renumbering existing
generators consistently.

Each intermediate presentation is balanced. A stable path is finite,
with no bound on its length, intermediate rank, or word size.

**Stable conjecture.** Every balanced presentation of the trivial group
at positive rank $n$ can reach the standard presentation at that same rank
using these moves. Equivalently, it can reach the empty presentation:
standard tuples can be reduced to empty by deleting their generator–relator
pairs, and reconstructed by stabilization.

A **stable counterexample** presents the trivial group but cannot reach
that standard presentation by any stable path. This follows the stable
convention in [Lackenby, §1](https://arxiv.org/html/2606.06122v1#S1).

Ordinary AC implies Stable AC, since every ordinary path is stable.
Consequently, a stable counterexample is also an ordinary counterexample.
An ordinary disproof alone does not settle Stable AC, and a Stable AC proof
alone does not settle ordinary AC. The rank-8 limit in the
[Discovery benchmark](discovery.md) is not part of this mathematical statement.

## Submissions

The submission identifies the following:

| Field | Requirement |
|---|---|
| `conjecture` | `ac` or `stable_ac` |
| `claim_type` | `proof` or `disproof` |
| `description` | State the claim, its scope, the argument or its outline, and the authors' contribution |
| Supporting materials | Paper/PDF, GitHub link for a Lean formalization, arXiv link, or a combination, as needed to supply the complete argument |
| Attribution | Identify prior work, submissions, versions, or comments used and explain their contribution |

The description may contain the full argument itself. Otherwise the
supporting materials must supply it. PDF and Lean are both optional;
an uploaded PDF must be at most **25 MB**. A title, claim announcement,
or search log without a complete argument cannot establish acceptance or
priority. The materials and cited public references must make the argument
and all its assumptions accessible for review.

GitHub materials must identify a fixed commit, the theorem, and its build
instructions. arXiv materials must identify a specific version, such as
`v2`. The platform preserves the submitted content as described under
[Public versions](#public-versions); changing an external link later does
not revise that record. The platform associates the team and authors with
the submission and assigns its version ID and timestamp. Contestants do
not supply a version selector to change the official mathematical statement.

If a submission exhibits a concrete counterexample, identify its rank and
exact presentation, and name the challenge if it is a pool instance.
Counterexamples may lie outside the Discovery pool. These fields are not
required for a nonconstructive disproof. Any use of a pool presentation
must map its words accurately to the mathematical tuple.

## Lean

The [Lean project](../tools/lean/README.md) belongs to Proof Track and defines
both conjectures in [AC.lean](../tools/lean/AC.lean). Using Lean is optional.
[Discovery Track](discovery.md) uses the
[Python verifier](../tools/verifier/README.md) and does not depend on this project.

| Problem | Proof target | Disproof target | Equivalent existence statement |
|---|---|---|---|
| AC | `AC.Conjecture` | `¬ AC.Conjecture` | `AC.Counterexample` |
| Stable AC | `AC.StableConjecture` | `¬ AC.StableConjecture` | `AC.StableCounterexample` |

In classical logic, each negation is equivalent to the corresponding
counterexample existence statement:

```lean
AC.not_conjecture_iff_counterexample : (¬ AC.Conjecture) ↔ AC.Counterexample
AC.not_stable_conjecture_iff_counterexample :
  (¬ AC.StableConjecture) ↔ AC.StableCounterexample
```

These are existence propositions, not requirements to exhibit a particular
tuple. Both disproof routes must establish triviality and full unbounded
non-reachability for the same presentation. The equivalences do not settle
either conjecture.

| Mathematical object | Lean definition |
|---|---|
| Free group $F_n$ | `FreeGroup (Fin n)` |
| Ordered relator tuple | `AC.Relators n` |
| Standard tuple $X$ | `AC.standard n` |
| Presented group is trivial | `AC.PresentsTrivialGroup R := Subsingleton (PresentedGroup (Set.range R))` |
| Ordinary elementary move | `AC.Step`: `inv`, `mulRight`, `conj` |
| Finite, unbounded ordinary reachability | `AC.Reachable` |
| A particular ordinary counterexample | `AC.IsCounterexample R` |
| Rank and its balanced presentation | `AC.Presentation` |
| Insertion of a fresh generator–relator pair | `AC.stabilize` |
| Stable elementary moves and finite reachability | `AC.StableStep`, `AC.StableReachable` |
| A particular stable counterexample | `AC.IsStableCounterexample R` |

The local project pins Lean `4.29.1` and Mathlib commit
`5e932f97dd25535344f80f9dd8da3aab83df0fe6`.
`statement-lock.json` records source and dependency SHA-256 snapshots.
Follow the [Lean guide](../tools/lean/README.md) to acquire the pinned
dependencies and run `lake build`, which builds only `AC`. A formalization
needs `import AC`; authors provide separate instructions for checking
their submitted theorem. The release process checks the official source snapshot.

`lake build Check` optionally runs [Check.lean](../tools/lean/Check.lean):
semantic examples, the compiler-hash
check, and an axiom audit against `propext`, `Classical.choice`, and
`Quot.sound`. This auxiliary target is not a submission requirement.
A successful build does not automatically establish acceptance. Community
review of formalizations includes their exact theorem, scope, dependencies,
axioms, and trust boundary, alongside review of written arguments.

## Public versions

Every Proof submission is public from receipt. Its page contains the
description, materials, author and team attribution, version history,
comments, and any assessment decisions. Participants may question an
argument, suggest corrections, and learn from it. Comments and author
responses identify the version they discuss and carry server timestamps;
substantive edits retain an accessible history.

The server assigns each complete submitted version an immutable,
globally unique, monotonically increasing version ID and a UTC
`received_at`; the ID breaks equal-time ties. It preserves the description,
authors, supplied files, and submitted content of linked arguments,
together with content hashes and fixed external revision identifiers.
A replacement PDF or changed argument creates a new version linked to
its predecessor. Older versions, comments, and decisions remain accessible.
Withdrawal marks the record as withdrawn rather than erasing it.

Publication and a receipt timestamp record a claim; they do not certify
its correctness.

## Community review

Community peer review is the primary way to examine submissions and
advance the work. Participants are encouraged to discuss arguments,
identify gaps, suggest corrections, and contribute improvements.
Participation is voluntary. Publication does not place a submission in
a mandatory organizer screening or review queue.

Organizers may assess selected claims for competition recognition,
drawing on community discussion and additional expert review as needed.
They and their designated reviewers are not expected to assess every
submission. For selected claims, any organizer decision is supported by
a public explanation. Comment counts, votes, and successful Lean builds
do not establish mathematical correctness.

| Decision | Meaning for the identified version |
|---|---|
| `accepted` | The stated proof or disproof has been accepted for competition recognition, with a public explanation |
| `rejected` | The claim has been declined for competition recognition, with a reason |
| `revision_requested` | The assessment identifies changes needed; a revision is published as a new version |
| `retracted` | Organizers have withdrawn a prior acceptance, with a public explanation |

Decisions identify the exact version, reviewers or responsible organizers,
decision time, and reasons. A new version does not inherit acceptance or
erase an earlier assessment. When a substantive error is established,
organizers may correct a decision while preserving its history and reasons.
Substantive objections to an accepted version remain visible during any
assessment. Recognition based on a withdrawn or retracted version is
updated accordingly. Withdrawal alone does not establish that an argument
was mathematically incorrect.

## Priority and credit

When competition priority is assessed, it belongs to the earliest eligible
submitted version confirmed to already contain a complete, correct
argument for the stated result. Order qualifying versions by server
`(received_at, version ID)`, rather than the time assessment finishes or
an external publication date. External dates remain relevant to scholarly
attribution but do not replace the competition receipt record.

Only versions received within the official Proof submission window
qualify: the complete version's server receipt must be at or after the
opening instant and before the deadline. Assessment may finish later.
Later corrections may be published and assessed as non-competitive
versions, but cannot create or backdate an eligible version. Withdrawn
or retracted versions do not hold competition priority; their historical
contributions remain attributable.

An incomplete announcement cannot reserve priority. If a later version
supplies a missing essential argument, its receipt time applies. If an
earlier version was already complete and correct, later wording or
exposition changes do not erase its priority. Any priority decision
identifies the earliest qualifying version and why it qualifies; it may
be corrected if a later assessment validates an earlier version or
retracts a previously accepted one.

Priority and contribution credit are recorded separately. Authors must
cite the particular submissions, versions, papers, code, and comments
they used and explain their contribution. For example, if a public comment
supplies a key lemma used in a revision, that contribution must be
acknowledged even when the original authors submit the completed argument.
These records inform assessment of contributions and attribution disputes.
The platform does not automatically assign contribution percentages or
turn a comment into coauthorship. `Independent Confirmation` applies only
to later accepted work whose independence has been established; a
disclosed extension or correction of another submission is credited as such.
