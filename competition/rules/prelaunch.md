# Andrews–Curtis Conjecture Challenge (ACC)

**Prelaunch preview — registration and submissions are not open.**
Rules, training data, and the reference verifier are available here for
local trials. The official data freeze and all dates are to be announced.

*One competition, two tracks: discover short trivializations in Discovery
Track, or prove or disprove the full conjecture in Prove Track.*

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

ACC turns that problem into a competition. Discovery certificates are
checked deterministically by an open reference verifier; a trivialization
of an open instance is a new mathematical result. Its valid certificates
will be released after the competition. Prove submissions and discussion
will be public by default from submission, with expert review of each claim.

## Task

**Discovery Track** uses a pool of **10,115 balanced presentations of the
trivial group**, ranging from warm-up exercises to open research problems.
Internal labels and maps are withheld, though instances may be recognized
from public mathematical sources. A solution is a sequence
of atomic Andrews–Curtis moves, submitted as a list of integers, that
transforms a presentation into the trivial presentation; the leaderboard
rewards the shortest verified path. The 424 solved training instances are
separate from the scored pool. Moves remain private during the competition.

**Prove Track** accepts a proof or disproof with a description of the claim
and argument. The complete argument may be in that description, a
paper/PDF, Lean material at a fixed GitHub commit, an arXiv version, or a
combination. The planned platform will preserve and publish every version
with its server timestamp and ID, alongside version-specific comments and
reasoned review decisions. Priority belongs to the earliest version
confirmed to contain a complete correct argument; borrowing from other
submissions or comments must be cited with an explanation of contributions.
Either a proof or disproof can receive the mathematical honor; neither
earns Discovery points nor automatically ends Discovery Track.

The [official mathematical statement](statement.md) and
[Lean project](../tools/lean/README.md) are available for local use.
Lean compilation does not replace expert review; auxiliary checks are
optional. Online submissions for both tracks are not open yet.

The full move specification, submission format, scoring formula, and
Prove submission, review, priority, and credit rules can be inspected in
[overview.md](overview.md) and [evaluation.md](evaluation.md). Try the
[successful training example](../examples/README.md) with the included
Python verifier and warm-up data. These are preview materials; formal
release and online submissions await the announced schedule and data freeze.

## Key Dates

- Registration and team formation open: to be announced.
- Official launch (submissions open): to be announced.
- Submission deadline: to be announced.
- Discovery certificate release (post-competition): to be announced.

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
