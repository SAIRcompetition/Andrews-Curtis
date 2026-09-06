import Mathlib.GroupTheory.PresentedGroup

/-!
# The Andrews–Curtis conjecture

The shared target for proof and disproof submissions, at every positive finite
rank. All transformations take place in the ambient free group, not its
presented quotient. This is the ordinary (non-stable) conjecture.

This module defines the proposition; it does not assert or assume its truth.
-/

namespace AC

/-- Words modulo free reduction on exactly `n` generators. -/
abbrev Word (n : ℕ) := FreeGroup (Fin n)

/-- An ordered balanced presentation: `n` relators on `n` generators. -/
abbrev Relators (n : ℕ) := Fin n → Word n

/-- The standard tuple: each relator is the corresponding free generator. -/
def standard (n : ℕ) : Relators n := FreeGroup.of

/-- The quotient by the normal closure of the relators has exactly one element.
It is a group, so it is nonempty independently of the `Subsingleton` condition. -/
def PresentsTrivialGroup {n : ℕ} (R : Relators n) : Prop :=
  Subsingleton (PresentedGroup (Set.range R))

/-- A single AC move, fixing the rank and changing only one relator.
The conjugator ranges over the whole free group; replacing `w` by `w⁻¹`
covers either conjugation convention. The `i ≠ j` guard excludes squaring
a relator, which need not preserve the presented group.
Left multiplication is derived: right-multiply by `R j`, then conjugate by `R j`. -/
inductive Step {n : ℕ} : Relators n → Relators n → Prop
  | inv (R : Relators n) (i : Fin n) :
      Step R (Function.update R i (R i)⁻¹)
  | mulRight (R : Relators n) (i j : Fin n) (h : i ≠ j) :
      Step R (Function.update R i (R i * R j))
  | conj (R : Relators n) (i : Fin n) (w : Word n) :
      Step R (Function.update R i (w * R i * w⁻¹))

/-- Existence of a finite sequence of AC moves, including the empty sequence.
There is no bound on its length or on the size of intermediate words.
Multiplication by inverse relators and relator permutations are derivable.
Every move can be undone by a finite sequence of moves,
so `Reachable` is an equivalence relation. -/
def Reachable {n : ℕ} : Relators n → Relators n → Prop :=
  Relation.ReflTransGen Step

/-- The full, arbitrary-rank, non-stable Andrews–Curtis conjecture.
Relator permutations are reachable, so the ordered standard target adds no restriction.
Positive rank follows the usual statement; the rank-zero case holds trivially. -/
def Conjecture : Prop :=
  ∀ (n : ℕ), 0 < n → ∀ (R : Relators n),
    PresentsTrivialGroup R → Reachable R (standard n)

/-- A specific counterexample must present the trivial group and rule out
every finite AC sequence to the standard presentation. -/
def IsCounterexample {n : ℕ} (R : Relators n) : Prop :=
  PresentsTrivialGroup R ∧ ¬ Reachable R (standard n)

/-- A disproof witnessed by a balanced relator tuple of any positive finite rank. -/
def Counterexample : Prop :=
  ∃ (n : ℕ), 0 < n ∧ ∃ (R : Relators n), IsCounterexample R

/-- Under classical logic the two disproof entry points are equivalent. -/
theorem not_conjecture_iff_counterexample : ¬ Conjecture ↔ Counterexample := by
  classical
  simp only [Conjecture, Counterexample, IsCounterexample, not_forall,
    exists_prop]

/-- An explicit counterexample disproves the shared official proposition. -/
theorem Counterexample.not_conjecture (h : Counterexample) : ¬ Conjecture :=
  not_conjecture_iff_counterexample.mpr h

end AC
