# The Andrews–Curtis Conjecture (ACC) Challenge

**Prelaunch preview — registration and submissions are not open.**
Rules, training data, and the reference verifier are available here for
local trials. The official data freeze and all dates are to be announced.

*A mathematical discovery competition on the Andrews–Curtis conjecture:
trivialize balanced presentations of the trivial group with machine-checked
certificates — or disprove the conjecture.*

## Co-organizers

ACC is co-organized by (in alphabetical order by surname):

- Lucas Fagan
- Sergei Gukov
- Terence Tao

The co-organizing institutions are
[Caltech](https://www.caltech.edu/) and the
[SAIR Foundation](https://sair.foundation/).

<!-- logo URLs: re-host under /competition-assets/acms/ at site onboarding -->
<p align="center">
  <a href="https://www.caltech.edu/"><img src="https://www.caltech.edu/static/core/img/caltech-new-logo.png" alt="Caltech" width="260"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://sair.foundation/"><img src="https://competition.sair.foundation/competition-assets/lean-kernel-challenge/sair-foundation-logo.png" alt="SAIR Foundation" width="260"></a>
</p>

## Background

The [Andrews–Curtis conjecture](https://en.wikipedia.org/wiki/Andrews%E2%80%93Curtis_conjecture)
has been open since 1965. It says that every
balanced presentation of the trivial group can be reduced to the trivial presentation by a sequence of elementary moves:
inverting a relator, multiplying one relator by another, conjugating a
relator. Most experts expect the conjecture to be false, yet in sixty years no
counterexample has ever been verified.

ACC turns that problem into a competition. Every submission is a
machine-checked certificate, verified deterministically by an open reference
verifier; a trivialization of an open instance is a new mathematical result.
After the competition, all valid certificates will be released publicly,
forming a new open benchmark for the global research community to reproduce,
reuse, and build on.

## Task

The planned competition uses a pool of **10,115 balanced presentations of the
trivial group**, ranging from warm-up exercises to instances that are open
research problems; which is which is not disclosed. A solution is a sequence
of atomic Andrews–Curtis moves, submitted as a list of integers, that
transforms a presentation into the trivial presentation; the leaderboard
rewards the shortest verified path.

A second track is planned for anyone who believes the conjecture is false:
after submissions open, purported counterexamples will be submitted as
self-contained PDFs for expert review. This PDF channel is not open yet;
the optional Lean route is also unavailable.

The full move specification, submission format, scoring formula, and
counterexample-track plan can already be inspected in
[overview.md](overview.md) and [evaluation.md](evaluation.md). Try the
[successful training example](../examples/README.md) with the included
Python verifier and warm-up data. These are preview materials; formal
release and online submissions await the announced schedule and data freeze.

## Key Dates

- Registration and team formation open: to be announced.
- Official launch (submissions open): to be announced.
- Submission deadline: to be announced.
- Certificate release (post-competition): to be announced.

`competition.yaml` records status `prelaunch`; all four schedule fields,
`freeze_date`, and `freeze_commit` are currently `null`. Dates and the
official freeze commit will be announced before formal release.

## Registration & Teams

Registration and team management are planned on
[SAIR](https://competition.sair.foundation/) when registration opens.
Participants will need a SAIR
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
