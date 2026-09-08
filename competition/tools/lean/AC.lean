import Mathlib.GroupTheory.PresentedGroup
import Mathlib.Data.Fin.Tuple.Basic

/-!
# The ordinary and stable Andrews–Curtis conjectures

The shared targets for proof and disproof submissions, at every positive finite
rank. All transformations take place in the ambient free group, not its
presented quotient. `Conjecture` fixes the rank; `StableConjecture` also permits
adding and removing generator–relator pairs, with no rank bound.

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

/-- Existence of a counterexample at some positive finite rank.
This proposition does not require exhibiting an explicit tuple. -/
def Counterexample : Prop :=
  ∃ (n : ℕ), 0 < n ∧ ∃ (R : Relators n), IsCounterexample R

/-- Under classical logic the two disproof entry points are equivalent. -/
theorem not_conjecture_iff_counterexample : ¬ Conjecture ↔ Counterexample := by
  classical
  simp only [Conjecture, Counterexample, IsCounterexample, not_forall,
    exists_prop]

/-- Existence of a counterexample disproves the shared official proposition. -/
theorem Counterexample.not_conjecture (h : Counterexample) : ¬ Conjecture :=
  not_conjecture_iff_counterexample.mpr h

/-- A balanced presentation together with its rank, which may change along a stable path. -/
abbrev Presentation := (n : ℕ) × Relators n

/-- Insert a fresh generator at position `g` and its singleton relator at position `i`.
The injection `g.succAbove` relabels the old generators while skipping the new one;
`Fin.insertNth` retains all old relators, in their original relative order.
Thus the new generator does not occur in any old relator. -/
def stabilize {n : ℕ} (R : Relators n) (g i : Fin (n + 1)) : Relators (n + 1) :=
  Fin.insertNth i (FreeGroup.of g) (fun j => FreeGroup.map g.succAbove (R j))

/-- A stable AC move is an ordinary AC move, insertion of an isolated
generator–relator pair, or the exact reverse of such an insertion.
Allowing either insertion position also covers deletion followed by relabeling.
There is no upper bound on the rank. -/
inductive StableStep : Presentation → Presentation → Prop
  | ac {n : ℕ} {R S : Relators n} (h : Step R S) :
      StableStep ⟨n, R⟩ ⟨n, S⟩
  | stabilize {n : ℕ} (R : Relators n) (g i : Fin (n + 1)) :
      StableStep ⟨n, R⟩ ⟨n + 1, AC.stabilize R g i⟩
  | destabilize {n : ℕ} (R : Relators n) (g i : Fin (n + 1)) :
      StableStep ⟨n + 1, AC.stabilize R g i⟩ ⟨n, R⟩

/-- A finite sequence of stable moves, including the empty sequence.
Neither path length, intermediate word size, nor intermediate rank is bounded. -/
def StableReachable : Presentation → Presentation → Prop :=
  Relation.ReflTransGen StableStep

/-- The full stable Andrews–Curtis conjecture at every positive finite rank.
The endpoint is the standard tuple of the original rank. Equivalently it can
be the empty presentation: standard tuples reduce to it by deleting their pairs,
and can be reconstructed from it by adding those pairs. -/
def StableConjecture : Prop :=
  ∀ (n : ℕ), 0 < n → ∀ (R : Relators n),
    PresentsTrivialGroup R → StableReachable ⟨n, R⟩ ⟨n, standard n⟩

/-- A stable counterexample rules out every finite stable path, at every rank. -/
def IsStableCounterexample {n : ℕ} (R : Relators n) : Prop :=
  PresentsTrivialGroup R ∧ ¬ StableReachable ⟨n, R⟩ ⟨n, standard n⟩

/-- Existence of a stable counterexample at some positive finite rank.
This proposition does not require exhibiting an explicit tuple. -/
def StableCounterexample : Prop :=
  ∃ (n : ℕ), 0 < n ∧ ∃ (R : Relators n), IsStableCounterexample R

theorem not_stable_conjecture_iff_counterexample :
    ¬ StableConjecture ↔ StableCounterexample := by
  classical
  simp only [StableConjecture, StableCounterexample, IsStableCounterexample,
    not_forall, exists_prop]

theorem StableCounterexample.not_stable_conjecture (h : StableCounterexample) :
    ¬ StableConjecture :=
  not_stable_conjecture_iff_counterexample.mpr h

/-- Every ordinary path is also a stable path. -/
theorem Reachable.stable {n : ℕ} {R S : Relators n} (h : Reachable R S) :
    StableReachable ⟨n, R⟩ ⟨n, S⟩ := by
  induction h with
  | refl => exact Relation.ReflTransGen.refl
  | tail _ hs ih => exact Relation.ReflTransGen.tail ih (StableStep.ac hs)

/-- The ordinary conjecture implies the stable conjecture. -/
theorem Conjecture.stable (h : Conjecture) : StableConjecture :=
  fun n hn R hR => (h n hn R hR).stable

/-- A stable counterexample also disproves the ordinary conjecture. -/
theorem StableCounterexample.counterexample (h : StableCounterexample) : Counterexample :=
  not_conjecture_iff_counterexample.mp (fun hAC => h.not_stable_conjecture hAC.stable)

end AC
