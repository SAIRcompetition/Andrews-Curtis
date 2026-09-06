# Andrews–Curtis conjecture — official statement

This is the shared mathematical target for a proof or disproof of the
full, non-stable Andrews–Curtis conjecture. Its Lean definition is in
[AC.lean](../tools/lean/AC.lean), under namespace `AC`.

## Mathematical statement

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

A **counterexample** is a positive rank $n$ and an explicit tuple $R$
for which $P_R$ is trivial but $X$ is not reachable from $R$.

This uses the ordinary AC convention in
[Lackenby, §1](https://arxiv.org/html/2606.06122v1#S1).
Arbitrary-word conjugation is a finite composition of conjugations by
generators and their inverses. Relator permutations follow from inversion
and multiplication, so the ordered standard endpoint is equivalent.

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
| Existence of a positive-rank counterexample | `AC.Counterexample` |

## Proof and disproof

The proof target is `AC.Conjecture`; the disproof target is
`¬ AC.Conjecture`. The supplied logical equivalence is

```lean
AC.not_conjecture_iff_counterexample : (¬ AC.Conjecture) ↔ AC.Counterexample
```

This equivalence does not prove the conjecture or construct a counterexample.
A proof must cover all positive finite ranks, not only the rank-two
competition pool. A disproof may use a presentation outside that pool;
it must establish both triviality and full, unbounded non-reachability.
A failed search or bounded-path result does not establish non-reachability.

Papers, PDFs, and Lean arguments address this same statement. Authors do
not supply a version field to change the target. See the
[Lean guide](../tools/lean/README.md) for build instructions.
