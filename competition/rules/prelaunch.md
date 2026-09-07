# ACC: The Andrews–Curtis Conjecture Competition

*A mathematical discovery competition on the Andrews–Curtis conjecture and
its stable version: trivialize balanced presentations of the trivial group
with machine-checked certificates — or prove or disprove the conjectures.*

## Co-organizers

ACC is co-organized by (in alphabetical order by surname):

- Lucas Fagan
- Sergei Gukov
- Terence Tao

The co-organizing institutions are the
[SAIR Foundation](https://sair.foundation/) and
[Caltech](https://www.caltech.edu/).

<!-- logo URLs: re-host under /competition-assets/acms/ at site onboarding -->
<p align="center">
  <a href="https://sair.foundation/"><img src="https://competition.sair.foundation/competition-assets/lean-kernel-challenge/sair-foundation-logo.png" alt="SAIR Foundation" width="260"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.caltech.edu/"><img src="https://www.caltech.edu/static/core/img/caltech-new-logo.png" alt="Caltech" width="260"></a>
</p>

## Background

A *balanced presentation* of the trivial group is a finite list of
generators together with the same number of relators, such that the group
they define is trivial. The **Andrews–Curtis conjecture** (1965) asserts that
every such presentation can be reduced to the trivial presentation
$\langle x, y \mid x, y \rangle$ by a sequence of elementary moves: inverting
a relator, multiplying one relator by another, and conjugating a relator. The **stable Andrews–Curtis conjecture** additionally allows adding
a new generator together with a relator equal to it, and removing such a
pair. The stable conjecture is implied by the ordinary one, and it is
connected to open questions in four-dimensional topology.

Both conjectures have been open for sixty years. Most experts expect the
ordinary conjecture to be false, yet no counterexample has ever been
verified: many proposed counterexamples have later been trivialized, and the
rest remain unresolved. The main family of candidates is the
Miller–Schupp presentations
$\langle x, y \mid x^{-1} y^n x y^{-(n+1)},\ x w^{-1} \rangle$.

**Why a competition, and why now.** The problem is unusually well suited to
machine search. Every move is atomic and mechanically checkable, so a
solution is a certificate that a computer can verify in milliseconds with no
human judgment and no answer key — the ground truth is simply unknown, and a
verified trivialization of an open instance is a new mathematical result the
moment it is submitted. Recent work has used the conjecture as a testbed for
reinforcement learning and large-scale search
([Shehper et al. 2025](https://arxiv.org/abs/2408.15332)), and in
[*The Two-Hump Problem*](https://arxiv.org/abs/2606.21611) (ICML 2026) we
identified why it is hard for learning systems: instances are either easily
solved or effectively impossible, with almost nothing in between. We built
new data-generation and search techniques (supermoves, Transformer-based
policies) to bridge that gap and released the first large public datasets of
trivializations. ACC opens the frontier to everyone: humans, classical
search, and AI systems compete on the same instances under the same verifier.

After the competition, all valid certificates will be released publicly,
forming a new open benchmark for the research community to reproduce, reuse,
and build on.

## Tracks

Teams are given a frozen pool of **10,115 balanced presentations of the
trivial group**, ranging from warm-up exercises to instances that are open
research problems — which is which is not disclosed. The same presentations
are used in both trivialization tracks.

**Track 1 — AC trivialization.** Transform a presentation into the trivial
presentation $\langle x, y \mid x, y \rangle$ using the 14 atomic
Andrews–Curtis moves on two relators. A solution is a list of integers naming
the moves.

**Track 2 — Stable AC trivialization.** The same presentations, with
stabilization and destabilization moves added, so the number of generators
may grow (up to eight) and shrink along the way. The terminal state is the
**empty presentation** $\langle \ \mid \ \rangle$, reached by destabilizing
everything away. Every Track 1 solution becomes a Track 2 solution by
appending two destabilizations, but shorter stable paths may exist.

In both tracks every submission is verified deterministically by an open
reference verifier, and the leaderboard rewards the shortest verified path
per instance. The two tracks are scored separately, with separate
leaderboards and a permanent **First Solver** honor on each.

**Tracks 3 and 4 — Proof or disproof.** Open to anyone who believes they can
settle either conjecture. A claim is submitted as a self-contained
mathematical argument (PDF) and goes to expert review by the organizers and
reviewers they designate. Note that a disproof of the stable conjecture is
also a disproof of the ordinary one, and a proof of the ordinary conjecture
also proves the stable one.

The full move specifications, submission format, scoring formula, and
review mechanics will be published at the official launch, together with the
reference verifier and public warm-up data of solved instances in both
specifications.

## Key Dates

- Registration and team formation open: **September 8, 2026**
- Trivialization tracks (1 and 2) open: **September 11, 2026**
- Proof-or-disproof tracks (3 and 4) open: **September 20, 2026**
- Submission deadline: —
- Certificate release (post-competition): —

Remaining dates will be announced here.

## Registration & Teams

Registration and team management take place on
[SAIR](https://competition.sair.foundation/). Participants must have a SAIR
account, complete the required profile information, and agree to the SAIR
competition terms before registering. They may compete individually or form a
team on SAIR.

## Team Participation and Anti-Cheating Policy

- Each individual or organization can participate in only one team.
- Teams must register members in advance; teams may not merge after either
  has submitted.
- If coordinated cheating is detected (including sockpuppet teams), all
  related teams will be disqualified.

## Community Feedback

Community feedback and contributions are welcome. Join the
[SAIR Foundation Zulip community](https://zulip.sair.foundation/) for
discussion and collaboration.
