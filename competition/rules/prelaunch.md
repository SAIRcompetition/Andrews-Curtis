# Andrews–Curtis Conjecture Challenge (ACC)

A competition to find short trivializations of group presentations and to prove or disprove the Andrews–Curtis conjecture and its stable version.

## Co-organizers

ACC is co-organized by (in alphabetical order by surname):

- Lucas Fagan
- Sergei Gukov
- Terence Tao

The co-organizing institutions are [Caltech](https://www.caltech.edu/) and the [SAIR Foundation](https://sair.foundation/).

<!-- logo URLs: re-host under /competition-assets/acms/ at site onboarding -->
<p align="center">
  <a href="https://www.caltech.edu/"><img src="https://www.caltech.edu/static/core/img/caltech-new-logo.png" alt="Caltech" width="260"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://sair.foundation/"><img src="https://competition.sair.foundation/competition-assets/lean-kernel-challenge/sair-foundation-logo.png" alt="SAIR Foundation" width="260"></a>
</p>

## Background

The [Andrews–Curtis conjecture](https://en.wikipedia.org/wiki/Andrews%E2%80%93Curtis_conjecture) concerns balanced presentations of the trivial group: descriptions with the same number of generators and defining relations. It asks whether every such presentation can be reduced to the standard presentation at the same rank by inverting a relation, multiplying one by another, or conjugating a relation.

The stable version additionally allows adding a fresh generator together with a relation setting it equal to the identity. Such a pair can be removed when the generator occurs in no other relation. These extra operations may make a presentation easier to simplify. The challenge brings together computational search for explicit simplifications and mathematical work on the two conjectures.

## Task

The challenge has **two tracks: Discovery and Proof**. Each covers two problems: **AC** and **Stable AC**.

### Discovery Track

Find short sequences of moves that simplify given presentations of the trivial group. The AC and Stable AC problems use the same pool of **10,115 two-generator presentations**, with different allowed moves and targets:

- **AC:** use ordinary Andrews–Curtis moves to reach the standard presentation `(x, y)`. The rank stays fixed at 2.
- **Stable AC:** use Andrews–Curtis moves together with stabilization and destabilization to reach the empty presentation. The rank may grow up to 8 along the way.

Each solution contains only a **challenge ID and a list of moves**. The verifier checks the sequence, and the AC and Stable AC problems have **separate leaderboards**, rewarding the shortest verified paths. Move sequences remain private during the competition and are published afterwards.

### Proof Track

Submit a proof or disproof of either conjecture:

- **AC:** the full Andrews–Curtis conjecture, using ordinary moves at fixed rank.
- **Stable AC:** the full stable Andrews–Curtis conjecture, allowing stabilization with no bound on intermediate rank.

Both conjectures concern balanced presentations at every positive finite rank. A proof must establish the full conjecture; a disproof must establish its negation. This may be done by giving a counterexample or by proving that one exists without explicitly identifying it.

Submit a description and a complete argument, supplied in the description, a paper or PDF, a GitHub repository containing a Lean proof at a fixed commit, an arXiv version, or a combination.

Every submission is public, with timestamped versions and comments. We encourage community peer review so participants can examine arguments, identify gaps, suggest corrections, and build on one another's work. Lean formalizations are also open to this scrutiny.

Priority belongs to the earliest complete, correct version; contributions from other submissions or comments must be acknowledged.

A proof or disproof can receive the competition's highest mathematical honor. Results in the Proof Track do not earn Discovery points or automatically end the Discovery Track.

## Key Dates

- Registration and team formation open: **September 8, 2026**
- Discovery Track opens: **September 11, 2026**
- Proof Track opens: **September 20, 2026**
- Submission deadline for all tracks: **November 30, 2026**

## Registration & Teams

Registration and team management take place on [SAIR](https://competition.sair.foundation/). Participants must have a SAIR account, complete the required profile information, and agree to the SAIR competition terms before registering. They may compete individually or form a team on SAIR.

## Official Repository & Playground

The official repository, SAIR Playground, and submission system will become available at the official launch.

## Team Participation and Anti-Cheating Policy

- Each individual or organization can participate in only one team.
- Teams must register members and sponsors in advance.
- If coordinated cheating is detected (including sockpuppet teams), all related teams will be disqualified.

## Experimental Status

The Andrews–Curtis Conjecture Challenge is experimental. Participants are responsible for any computing costs they incur while developing, testing, submitting, or otherwise participating in the challenge. The co-organizers do not reimburse these costs.

## Community Feedback

Join the [SAIR Foundation Zulip community](https://zulip.sair.foundation/) to discuss the challenge, ask questions, and contribute feedback.
