# Proof Track — Andrews–Curtis statements in Lean

This directory serves [Proof Track](../../rules/proof.md).
[AC.lean](AC.lean) contains the shared official AC and Stable AC definitions;
using Lean is optional.

Lean 4 formalizations of ideas and partial results are welcome. Import `AC`
to use the definitions. The following targets apply to **complete proofs or
disproofs**; partial work may instead establish lemmas toward either direction.

| Claim | Ordinary AC | Stable AC |
|---|---|---|
| Proof | `AC.Conjecture` | `AC.StableConjecture` |
| Disproof | `¬ AC.Conjecture` | `¬ AC.StableConjecture` |
| Existence of a counterexample | `AC.Counterexample` | `AC.StableCounterexample` |

The negation and counterexample targets are equivalent, by
`AC.not_conjecture_iff_counterexample` and
`AC.not_stable_conjecture_iff_counterexample`, respectively.
A rigorous nonconstructive proof of either negation is a complete disproof;
no explicit rank or relator tuple needs to be exhibited. An explicit
counterexample argument identifies its rank and full presentation.
Both conjectures cover every positive finite starting rank. Ordinary AC fixes
the rank along each path. Stable AC also permits adding an isolated generator
and its singleton relator, or deleting such a pair, at arbitrary positions.
Its finite paths have no bounds on intermediate rank, length, or word size.

`AC.Conjecture.stable` proves that ordinary AC implies stable AC;
`AC.StableCounterexample.counterexample` proves that a stable counterexample
also disproves ordinary AC. These implications do not assume either conjecture.
See the [problems](../../rules/proof.md#problems) for the mathematical statements.

To [submit](../../rules/proof.md#submit), choose AC or Stable AC and a proof
or disproof direction, and describe your work. Cite any work by others that
you use in the description and explain how you use it. These directions
include unfinished research. A public GitHub repository containing Lean 4
formalization and arXiv or paper links are optional. If you provide a GitHub
link, you must also provide the **full commit hash** for the submitted version.

Participation is voluntary; submitting requires agreeing to share. Every
submission is automatically published in the SAIR Contributor Network for
others to use and build on with credit. Keep citations and any GitHub commit
hash accurate when submitting an updated version. See
[Sharing and credit](../../rules/proof.md#sharing-and-credit).

## Build

From the repository root, download dependencies on first use, then build:

```sh
cd competition/tools/lean
MATHLIB_NO_CACHE_ON_UPDATE=1 lake update
lake exe cache get Mathlib/GroupTheory/PresentedGroup.lean Mathlib/Data/Fin/Tuple/Basic.lean
lake build
```

Pinned dependencies: Lean `4.29.1`, Mathlib
`5e932f97dd25535344f80f9dd8da3aab83df0fe6`.

| File | Purpose |
|---|---|
| [AC.lean](AC.lean) | Both conjectures, counterexamples, and their implication |
| [lakefile.toml](lakefile.toml) | Build target and pinned Mathlib revision |
| [lean-toolchain](lean-toolchain) | Lean version |

`lake update` generates `lake-manifest.json` from the pinned dependencies.
The generated manifest and `.lake/` build directory are ignored by Git.

`lake build` builds only `AC`; a formalization needs only `import AC`.
Building the official statement does not verify a contestant's theorem.
Authors should identify the variant and formalized result, describe its scope,
and provide instructions for checking their own source.
