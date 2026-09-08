import AC
import Mathlib.GroupTheory.FreeGroup.Reduce
import Lean.Util.CollectAxioms

/-! Kernel-checked semantic checks and useful elementary lemmas.
None assumes the conjecture or a counterexample. -/

namespace AC

/-- The formal triviality condition is exactly normal generation of the free group. -/
theorem presentsTrivialGroup_iff_normalClosure_eq_top {n : ℕ} (R : Relators n) :
    PresentsTrivialGroup R ↔ Subgroup.normalClosure (Set.range R) = ⊤ :=
  QuotientGroup.subsingleton_iff

/-- The premise is inhabited at every rank, not vacuously false. -/
theorem standard_presentsTrivialGroup (n : ℕ) : PresentsTrivialGroup (standard n) := by
  rw [presentsTrivialGroup_iff_normalClosure_eq_top]
  apply top_unique
  rw [← FreeGroup.closure_range_of (Fin n)]
  exact Subgroup.closure_le_normalClosure

/-- The standard presentation is reachable by a finite sequence of zero moves. -/
theorem standard_reachable (n : ℕ) : Reachable (standard n) (standard n) :=
  Relation.ReflTransGen.refl

/-- The trivial-group hypothesis rejects the one-generator presentation with
only the identity as its relator, whose group is infinite cyclic. -/
theorem identity_relator_not_trivial :
    ¬ PresentsTrivialGroup (fun _ : Fin 1 => (1 : Word 1)) := by
  rw [presentsTrivialGroup_iff_normalClosure_eq_top]
  have hbot : Subgroup.normalClosure (Set.range (fun _ : Fin 1 => (1 : Word 1))) = ⊥ := by
    apply le_antisymm
    · apply Subgroup.normalClosure_le_normal
      rintro w ⟨i, rfl⟩
      exact Subgroup.one_mem _
    · exact bot_le
  rw [hbot]
  exact bot_ne_top

/-- A successfully trivialized presentation cannot simultaneously be a counterexample. -/
theorem not_isCounterexample_of_reachable {n : ℕ} {R : Relators n}
    (h : Reachable R (standard n)) : ¬ IsCounterexample R :=
  fun hc => hc.2 h

/-- Left multiplication is a derived move, so removing it from `Step` does
not remove any standard AC paths. -/
theorem mulLeft_reachable {n : ℕ} (R : Relators n) (i j : Fin n) (h : i ≠ j) :
    Reachable R (Function.update R i (R j * R i)) := by
  have hr := Step.mulRight R i j h
  have hc := Step.conj (Function.update R i (R i * R j)) i (R j)
  simpa [mul_assoc] using
    Relation.ReflTransGen.tail (Relation.ReflTransGen.single hr) hc

/-- Inversion really permits returning to the original presentation. -/
theorem inverted_reachable {n : ℕ} (R : Relators n) (i : Fin n) :
    Reachable (Function.update R i (R i)⁻¹) R := by
  have h := Step.inv (Function.update R i (R i)⁻¹) i
  simpa using Relation.ReflTransGen.single h

/-- Conjugation is by any finite word, with a reverse move; it is not limited
to the rank-two verifier's four one-letter conjugators. -/
theorem conjugated_reachable {n : ℕ} (R : Relators n) (i : Fin n) (w : Word n) :
    Reachable (Function.update R i (w * R i * w⁻¹)) R := by
  have h := Step.conj (Function.update R i (w * R i * w⁻¹)) i w⁻¹
  simpa [mul_assoc] using Relation.ReflTransGen.single h

/-! A runnable success example, not a proof of the conjecture.
These are actual theorems about known trivial presentations. -/

-- The official model works beyond the two-generator discovery dataset.
example : AC.PresentsTrivialGroup (AC.standard 3) :=
  AC.standard_presentsTrivialGroup 3

example : AC.Reachable (AC.standard 3) (AC.standard 3) :=
  AC.standard_reachable 3

-- A nonempty path: invert the third relator and then invert it back.
example : AC.Reachable
    (Function.update (AC.standard 3) (2 : Fin 3) ((AC.standard 3) 2)⁻¹)
    (AC.standard 3) :=
  AC.inverted_reachable (AC.standard 3) 2

-- The standard presentation cannot be used as a purported counterexample.
example : ¬ AC.IsCounterexample (AC.standard 3) :=
  AC.not_isCounterexample_of_reachable (AC.standard_reachable 3)

/-! Stable semantics: the old free group is embedded, the new relation is exactly
the fresh generator, and the choice of standard or empty target is equivalent. -/

theorem stabilization_embedding_injective {n : ℕ} (g : Fin (n + 1)) :
    Function.Injective (FreeGroup.map g.succAbove) :=
  FreeGroup.map_injective g.succAbove_right_injective

theorem stabilize_new_relator {n : ℕ} (R : Relators n) (g i : Fin (n + 1)) :
    stabilize R g i i = FreeGroup.of g := by
  simp [stabilize]

theorem stabilize_old_relator {n : ℕ} (R : Relators n) (g i : Fin (n + 1))
    (j : Fin n) : stabilize R g i (i.succAbove j) = FreeGroup.map g.succAbove (R j) := by
  simp [stabilize]

theorem stabilize_standard (n : ℕ) :
    stabilize (standard n) (Fin.last n) (Fin.last n) = standard (n + 1) := by
  apply Fin.insertNth_eq_iff.mpr
  constructor
  · rfl
  · funext j
    simp [standard, Fin.removeNth]

theorem standard_stableReachable_empty (n : ℕ) :
    StableReachable ⟨n, standard n⟩ ⟨0, standard 0⟩ := by
  induction n with
  | zero => exact Relation.ReflTransGen.refl
  | succ n ih =>
    have h : StableStep ⟨n + 1, standard (n + 1)⟩ ⟨n, standard n⟩ := by
      simpa only [stabilize_standard] using
        StableStep.destabilize (standard n) (Fin.last n) (Fin.last n)
    exact Relation.ReflTransGen.head h ih

theorem empty_stableReachable_standard (n : ℕ) :
    StableReachable ⟨0, standard 0⟩ ⟨n, standard n⟩ := by
  induction n with
  | zero => exact Relation.ReflTransGen.refl
  | succ n ih =>
    have h : StableStep ⟨n, standard n⟩ ⟨n + 1, standard (n + 1)⟩ := by
      simpa only [stabilize_standard] using
        StableStep.stabilize (standard n) (Fin.last n) (Fin.last n)
    exact Relation.ReflTransGen.tail ih h

theorem stableReachable_standard_iff_empty {n : ℕ} (R : Relators n) :
    StableReachable ⟨n, R⟩ ⟨n, standard n⟩ ↔
      StableReachable ⟨n, R⟩ ⟨0, standard 0⟩ :=
  ⟨fun h => h.trans (standard_stableReachable_empty n),
    fun h => h.trans (empty_stableReachable_standard n)⟩

-- The full conjecture's paths can pass through rank 12: rank 8 is only a benchmark limit.
example : StableReachable ⟨0, standard 0⟩ ⟨12, standard 12⟩ :=
  empty_stableReachable_standard 12

-- Insertion and deletion do not assume that either position is last or that they coincide.
example (R : Relators 2) : StableStep ⟨3, stabilize R 0 1⟩ ⟨2, R⟩ :=
  StableStep.destabilize R 0 1

example : ¬ IsStableCounterexample (standard 3) :=
  fun h => h.2 Relation.ReflTransGen.refl

end AC

/-! Fail compilation if any declaration in the official AC namespace depends
on an axiom outside Lean's conventional classical whitelist. -/

run_cmd do
  unless Lean.githash == "f72c35b3f637c8c6571d353742168ab66cc22c00" do
    throwError "Unexpected Lean compiler revision: {Lean.githash}"
  let allowed : Array Lean.Name := #[``propext, ``Classical.choice, ``Quot.sound]
  let env ← Lean.getEnv
  let mut count := 0
  for (name, _) in env.constants.toList do
    if (`AC).isPrefixOf name then
      count := count + 1
      let axioms ← Lean.collectAxioms name
      for axiomName in axioms do
        unless allowed.contains axiomName do
          throwError "{name} depends on forbidden axiom {axiomName}"
  Lean.logInfo m!"AC axiom audit passed for {count} declarations."

#print axioms AC.Conjecture
#print axioms AC.Counterexample
#print axioms AC.not_conjecture_iff_counterexample
#print axioms AC.standard_presentsTrivialGroup
#print axioms AC.StableConjecture
#print axioms AC.StableCounterexample
#print axioms AC.not_stable_conjecture_iff_counterexample
#print axioms AC.Conjecture.stable
#print axioms AC.StableCounterexample.counterexample
#print axioms AC.stableReachable_standard_iff_empty
