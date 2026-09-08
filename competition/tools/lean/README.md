# Lean 4 fast track (in development)

The official channel for a purported proof or disproof of the
Andrews–Curtis conjecture or of its stable version is a
**self-contained PDF uploaded through the competition site**, reviewed
by the organizer panel and reviewers they designate; see
[../../rules/evaluation.md](../../rules/evaluation.md) §9.2. The Lean
track described here is an optional fast track: a claim backed by a
machine-checked proof skips expert review and, on passing verification,
settles the claim.

**The competition Lean library is not yet available, for either
conjecture.** When published, this directory will carry the frozen
definitions — the full, unbounded, non-stable AC relation, the stable
AC relation, and compatibility theorems tying the competition move sets
(`ac-r2-v1` and `sac-r8-v1`) to them — together with the exact theorem
statements a claim must prove, a template project, the pinned
toolchain, and the container digest. Nothing here is promised as
delivered, and there is nothing to build against yet.

The verification requirements are already frozen so that a
formalization effort can target them (evaluation.md §9.3): offline
`lake build`, axiom whitelist `propext` / `Classical.choice` /
`Quot.sound`, no `sorry` / `unsafe` / `native_decide`, hash-pinned
definitions, and an independent-machine re-check.
