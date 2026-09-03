# Lean 4 fast track (in development)

The official channel for a purported disproof of the Andrews–Curtis
conjecture is a **self-contained PDF uploaded through the competition
site**, reviewed by the organizer panel and reviewers they designate;
see [../../rules/evaluation.md](../../rules/evaluation.md) §9.2. The
Lean track described here is an optional fast track: a claim backed by
a machine-checked proof skips expert review and, on passing
verification, settles the claim outright.

**The competition Lean library is not yet available.** When published,
this directory will carry the frozen definitions — including the full,
unbounded, non-stable AC relation and a compatibility theorem tying the
14-move closure of `ac-r2-v1` to the standard AC moves — together with
a template project, the pinned toolchain, and the container digest.

The verification requirements are already frozen so that a
formalization effort can target them (evaluation.md §9.3): offline
`lake build`, axiom whitelist `propext` / `Classical.choice` /
`Quot.sound`, no `sorry` / `unsafe` / `native_decide`, hash-pinned
definitions, and an independent-machine re-check.
