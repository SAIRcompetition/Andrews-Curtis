# Andrews–Curtis conjectures — official statements

These are the mathematical targets for the AC and Stable AC problems
within Proof Track.
Both cover the full conjecture at every positive finite rank. Their Lean definitions are in
[AC.lean](../tools/lean/AC.lean), under namespace `AC`.

## Ordinary AC

Let $n\ge1$ be any finite positive rank and
$F_n=\langle x_0,\ldots,x_{n-1}\rangle$ the free group on $n$ generators.
An ordered relator tuple $R=(r_0,\ldots,r_{n-1})\in F_n^n$ defines

$$P_R=\langle x_0,\ldots,x_{n-1}\mid r_0,\ldots,r_{n-1}\rangle
      =F_n/\langle\!\langle r_0,\ldots,r_{n-1}\rangle\!\rangle.$$

The standard tuple is $X=(x_0,\ldots,x_{n-1})$. Each elementary move
changes one relator, leaving all others fixed:

* **Inversion:** $r_i\leftarrow r_i^{-1}$.
* **Right multiplication:** $r_i\leftarrow r_i r_j$, for $i\ne j$.
* **Conjugation:** $r_i\leftarrow w r_i w^{-1}$, for any $w\in F_n$.

Left multiplication follows in two moves: with $a=r_i$ and $b=r_j$
($i\ne j$), right-multiply and then conjugate by the unchanged $b$,
giving $a\to ab\to b(ab)b^{-1}=ba$.

Equality is equality in the free group, including free cancellation.
Rank stays fixed: no generator–relator pair is added or removed.
Reachability is a finite sequence of moves, including the empty sequence,
with no bound on its length or the sizes of intermediate words.

**Conjecture.** For every $n\ge1$ and every $R\in F_n^n$, if $P_R$ is
the trivial group, then $R$ can be transformed into $X$ by these moves.

A **counterexample** is a positive rank $n$ and a tuple $R$
for which $P_R$ is trivial but $X$ is not reachable from $R$.

This uses the ordinary AC convention in
[Lackenby, §1](https://arxiv.org/html/2606.06122v1#S1).
Arbitrary-word conjugation is a finite composition of conjugations by
generators and their inverses. Relator permutations follow from inversion
and multiplication, so the ordered standard endpoint is equivalent.

## Stable AC

In addition to ordinary AC moves, allow **stabilization**:

$$\langle x_0,\ldots,x_{n-1}\mid r_0,\ldots,r_{n-1}\rangle
\longrightarrow
\langle x_0,\ldots,x_{n-1},z\mid r_0,\ldots,r_{n-1},z\rangle.$$

Here $z$ is fresh. The reverse deletes this generator–relator pair when
$z$ occurs in no other relator. The display appends the pair for convenience;
the Lean definition permits insertion at any generator and relator positions,
renumbering existing generators consistently.
Each intermediate presentation is balanced. A stable path is finite, with
no bound on its length, intermediate rank, or word size.

**Stable conjecture.** Every balanced presentation of the trivial group
at positive rank $n$ can reach the standard presentation at that same rank
using these moves. Equivalently, it can reach the empty presentation:
standard tuples can be reduced to empty by deleting their generator–relator
pairs, and reconstructed by stabilization.

A **stable counterexample** presents the trivial group but cannot reach
that standard presentation by any stable path. Ordinary AC implies Stable
AC, since every ordinary path is stable. Consequently, a stable
counterexample is also an ordinary counterexample. An ordinary
counterexample alone does not establish a stable counterexample.
This follows the stable convention in
[Lackenby, §1](https://arxiv.org/html/2606.06122v1#S1).

The Stable AC problem in Discovery uses a rank cap of 8 (`sac-r8-v1`) as a benchmark
restriction. Proving non-reachability with that cap does not disprove this
unbounded statement.

## Lean mapping

| Mathematical object | Lean definition |
|---|---|
| Free group $F_n$ | `FreeGroup (Fin n)` |
| Ordered relator tuple | `AC.Relators n` |
| Standard tuple $X$ | `AC.standard n` |
| Presented group is trivial | `AC.PresentsTrivialGroup R := Subsingleton (PresentedGroup (Set.range R))` |
| Elementary move | `AC.Step`: `inv`, `mulRight`, `conj` |
| Finite, unbounded reachability | `AC.Reachable` |
| Conjecture for all positive finite ranks | `AC.Conjecture` |
| A particular counterexample | `AC.IsCounterexample R` |
| Existence of a positive-rank ordinary counterexample | `AC.Counterexample` |
| Stable elementary moves and finite reachability | `AC.StableStep`, `AC.StableReachable` |
| Stable conjecture | `AC.StableConjecture` |
| Existence of a positive-rank stable counterexample | `AC.StableCounterexample` |

## Proof and disproof

| Problem | Proof | Disproof |
|---|---|---|
| AC | `AC.Conjecture` | `¬ AC.Conjecture` |
| Stable AC | `AC.StableConjecture` | `¬ AC.StableConjecture` |

In classical logic, each negation is equivalent to the corresponding
counterexample existence statement:

```lean
AC.not_conjecture_iff_counterexample : (¬ AC.Conjecture) ↔ AC.Counterexample
AC.not_stable_conjecture_iff_counterexample :
  (¬ AC.StableConjecture) ↔ AC.StableCounterexample
```

These are existence propositions, not requirements to exhibit a particular
tuple. A disproof may give a concrete counterexample or use a nonconstructive
argument to prove that one exists. Both routes must establish triviality and
full unbounded non-reachability for the same presentation.

These equivalences do not settle either conjecture. Proofs must cover all
positive finite ranks; counterexamples may lie outside the rank-two pool.
A failed search or exclusion of only bounded paths does not by itself
establish full non-reachability.

Descriptions, papers, PDFs, and Lean arguments address the same selected
statement. Authors do not supply a version field to change it. See the
[Lean guide](../tools/lean/README.md) for build instructions.
