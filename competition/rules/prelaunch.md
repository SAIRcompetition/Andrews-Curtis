# Andrews–Curtis Conjecture Challenge (ACC)

**Prelaunch preview — registration and submissions are not open.**
Rules, training data, and the reference verifier are available here for
local trials. Calendar dates are announced below; the official data freeze
and exact UTC schedule remain pending.

*One competition, four tracks: AC and Stable AC, each with Discovery
for short trivializations and Prove for proofs or disproofs.*

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
balanced presentation of the trivial group can be reduced to its standard
presentation at the same rank by a sequence of elementary moves:
inverting a relator, multiplying one relator by another, conjugating a
relator. Most experts expect the conjecture to be false, yet in sixty years no
counterexample has ever been verified. The stable conjecture additionally
allows adding or removing a fresh generator together with a relation
setting it to the identity, with no bound on intermediate rank.

ACC turns that problem into a competition. Discovery certificates are
checked deterministically by an open reference verifier; a trivialization
of an open instance is a new mathematical result. Its valid certificates
will be released after the competition. Prove submissions and discussion
will be public by default from submission, with expert review of each claim.

## Task

**AC Discovery** and **Stable AC Discovery** share a pool of **10,115
balanced rank-two presentations of the trivial group**. Internal labels
and maps are withheld, though public mathematical sources may reveal origins.
AC Discovery uses 14 moves and the target `(x,y)`; Stable AC Discovery uses
257 moves, allows ranks up to 8, and ends at the empty presentation. The
two tracks have separate leaderboards and First Solver honors. Submissions
contain only a challenge ID and move list. The 424 solved training
presentations are outside both scored pools; their examples cover both move
specifications. Moves remain private during the competition.

**AC Prove** and **Stable AC Prove** accept a proof or disproof of the
selected full conjecture, with a description of the claim
and argument. The complete argument may be in that description, a
paper/PDF, Lean material at a fixed GitHub commit, an arXiv version, or a
combination. The planned platform will preserve and publish every version
with its server timestamp and ID, alongside version-specific comments and
reasoned review decisions. Priority belongs to the earliest version
confirmed to contain a complete correct argument; borrowing from other
submissions or comments must be cited with an explanation of contributions.
Either a proof or disproof can receive the mathematical honor; neither
earns Discovery points nor automatically ends either Discovery track.
An AC proof also settles Stable AC; a Stable AC disproof also settles AC,
with the same qualifying version and receipt time recognized for both.

The [official mathematical statement](statement.md) and
[Lean project](../tools/lean/README.md) are available for local use.
Lean compilation does not replace expert review; auxiliary checks are
optional. Online submissions for all four tracks are not open yet.

The full move specification, submission format, scoring formula, and
Prove submission, review, priority, and credit rules can be inspected in
[overview.md](overview.md) and [evaluation.md](evaluation.md). Try the
[successful training example](../examples/README.md) with the included
Python verifier and warm-up data. These are preview materials; formal
release and online submissions await the announced schedule and data freeze.

## Key Dates

- Registration and team formation: September 8, 2026.
- AC Discovery and Stable AC Discovery: September 11, 2026.
- AC Prove and Stable AC Prove: September 20, 2026.
- Submission deadline: to be announced.
- Discovery certificate release (post-competition): to be announced.

`competition.yaml` records these calendar dates in `announced_dates`.
Status remains `prelaunch`; exact UTC schedule fields, `freeze_date`, and
`freeze_commit` are currently `null`. The complete schedule and verified
freeze must be set before formal release and online submission.

## Registration & Teams

Registration and team management are planned on
[SAIR](https://competition.sair.foundation/) when registration opens.
Participants will need a SAIR
account, complete the required profile information, and agree to the SAIR
competition terms before registering. They may compete individually or form a
team on SAIR.

## Team Participation and Anti-Cheating Policy

- Each individual can participate in only one team.
- Members may join during the competition with organizer approval;
  teams may not merge after either has submitted.
- Public learning and cross-team discussion with stated contributions are
  welcome. A shared Discovery certificate must not be resubmitted by
  multiple teams for independent credit or scoring.
- If coordinated cheating is detected (including sockpuppet teams), all
  related teams will be disqualified.

## Community Feedback

Community feedback and contributions are welcome. Join the
[SAIR Foundation Zulip community](https://zulip.sair.foundation/) for
discussion and collaboration.
