# Proof Track — Andrews–Curtis statements in Lean

Import `AC` and identify whether your claim concerns ordinary or stable AC:

| Claim | Ordinary AC | Stable AC |
|---|---|---|
| Proof | `AC.Conjecture` | `AC.StableConjecture` |
| Disproof | `¬ AC.Conjecture` | `¬ AC.StableConjecture` |
| Existence of a counterexample | `AC.Counterexample` | `AC.StableCounterexample` |

The negation and counterexample targets are equivalent, by
`AC.not_conjecture_iff_counterexample` and
`AC.not_stable_conjecture_iff_counterexample`, respectively.
A rigorous nonconstructive proof of either negation qualifies as a disproof;
no explicit rank or relator tuple needs to be exhibited. If a submission
provides a specific counterexample, it must identify its rank and full presentation.
Both conjectures cover every positive finite starting rank. Ordinary AC fixes
the rank along each path. Stable AC also permits adding an isolated generator
and its singleton relator, or deleting such a pair, at arbitrary positions.
Its finite paths have no bounds on rank, length, or word size; the Discovery
benchmark's rank-8 limit is not part of the conjecture.

`AC.Conjecture.stable` proves that ordinary AC implies stable AC;
`AC.StableCounterexample.counterexample` proves that a stable counterexample
also disproves ordinary AC. These implications do not assume either conjecture.
See the [mathematical statements](../../rules/statement.md) for details.

The Proof Track is part of the Andrews–Curtis Conjecture Challenge (ACC).
It accepts a proof or disproof with a description and complete argument,
which may be carried by the description, a PDF or paper, a GitHub
repository at a fixed commit, or an arXiv paper at a fixed version.
Submissions and immutable versions are public, with comments for review
and discussion. Reviewers make the final mathematical determination;
Lean does not provide an exemption from review. See the
[evaluation rules](../../rules/evaluation.md) for versions and credit.

## Build

From the repository root, download dependencies on first use, then build:

```sh
cd competition/tools/lean
lake exe cache get Mathlib/GroupTheory/PresentedGroup.lean Mathlib/Data/Fin/Tuple/Basic.lean
lake build
```

Pinned dependencies: Lean `4.29.1`, Mathlib
`5e932f97dd25535344f80f9dd8da3aab83df0fe6`.

| File | Purpose |
|---|---|
| [AC.lean](AC.lean) | Both conjectures, counterexamples, and their implication |
| [Check.lean](Check.lean) | Optional semantic examples, axiom audit, and compiler-hash check |

`lake build` builds only `AC`; a formalization needs only `import AC`.
Building the official statement does not verify a contestant's theorem.
Authors should identify the claimed variant and the theorem proving its official
target, and provide instructions for checking their own source.
To run the auxiliary checks, optionally use `lake build Check`.
Those checks are not a submission requirement. Source snapshots are
checked separately at release. The optional checks verify the embedding used
by stabilization, the equivalence of the standard and empty stable endpoints,
paths beyond rank 8, and the allowed axioms. Proof submissions address the
chosen full conjecture or its negation; a formal bridge to a Discovery
verifier's finite move encoding is not required.
