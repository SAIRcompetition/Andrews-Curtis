# Prove Track — Andrews–Curtis statement in Lean

Import `AC` and use one of the two official targets:

* **Proof:** `AC.Conjecture`.
* **Disproof:** `¬ AC.Conjecture`, equivalently `AC.Counterexample` via
  `AC.not_conjecture_iff_counterexample`.

See the [mathematical statement](../../rules/statement.md) for the full,
arbitrary-positive-rank, non-stable conjecture.

The Prove Track is part of the Andrews–Curtis Conjecture Challenge (ACC).
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
lake exe cache get Mathlib/GroupTheory/PresentedGroup.lean
lake build
```

Pinned dependencies: Lean `4.29.1`, Mathlib
`5e932f97dd25535344f80f9dd8da3aab83df0fe6`.

| File | Purpose |
|---|---|
| [AC.lean](AC.lean) | Complete conjecture and counterexample definitions |
| [Check.lean](Check.lean) | Optional semantic examples, axiom audit, and compiler-hash check |

`lake build` builds only `AC`; a formalization needs only `import AC`.
Building the official statement does not verify a contestant's theorem.
Authors should identify the theorem proving `AC.Conjecture` or its
negation and provide instructions for checking their own source.
To run the auxiliary checks, optionally use `lake build Check`.
Those checks are not a submission requirement. Source snapshots are
checked separately at release. Prove submissions address `AC.Conjecture`
or its negation directly; a formal bridge to the Discovery verifier's
14-move encoding is not required for this target.
