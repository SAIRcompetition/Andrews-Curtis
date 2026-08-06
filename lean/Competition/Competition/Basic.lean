/-
ACMS Lean formalization — O-3 SPIKE (milestone P4 seed).

Purpose (DESIGN.md O-3): establish early that the `Step` / `AtomicRel` /
`ac_iff_atomic` skeleton is buildable and that the route to the bridge
theorem is viable.  `sorry` is allowed HERE and only here; the frozen
competition library shipped at P4 must be sorry-free with the audited
axiom whitelist (DESIGN.md §7.5).

Deliberately Mathlib-free for now: `ReflTransGen` is defined locally so
the spike builds offline in seconds.  At P4 this moves to Mathlib's
`Relation.ReflTransGen` and `PresentsTrivialGroup` gets its real
definition via `PresentedGroup`.
-/

namespace StandardAC

/-- `±1 = x^{±1}`, `±2 = y^{±2}` — the frozen competition encoding
(DESIGN.md §1.1). -/
abbrev Letter := Int

abbrev Word := List Letter

/-- Formal inverse of a word. -/
def wordInv (w : Word) : Word := (w.map (-·)).reverse

/-- One step of free reduction: cancel the first adjacent inverse pair. -/
def reduceStep : Word → Word
  | [] => []
  | [a] => [a]
  | a :: b :: t => if a = -b then reduceStep t else a :: reduceStep (b :: t)

/-- Free reduction to a fixed point (fuel = length suffices: each pass
shortens or fixes).  Mirrors the verifier's deterministic reduction; the
P4 library must prove this equals stack-fold reduction. -/
def reduce (w : Word) : Word :=
  go w.length w
where
  go : Nat → Word → Word
    | 0, w => w
    | n + 1, w =>
      let r := reduceStep w
      if r = w then w else go n r

/-- Reduced concatenation. -/
def wordMul (u v : Word) : Word := reduce (u ++ v)

/-- Reduced conjugate `g w g⁻¹`. -/
def conjBy (g w : Word) : Word := reduce (g ++ w ++ wordInv g)

/-- An ordered balanced presentation on two generators. -/
structure Pres where
  r0 : Word
  r1 : Word
deriving DecidableEq, Repr

namespace Pres

def get (P : Pres) : Fin 2 → Word
  | 0 => P.r0
  | 1 => P.r1

def set (P : Pres) : Fin 2 → Word → Pres
  | 0, w => ⟨w, P.r1⟩
  | 1, w => ⟨P.r0, w⟩

end Pres

/-- The full, unbounded, non-stable Andrews–Curtis one-step relation
(DESIGN.md §7.2): relator inversion, relator multiplication by the
other relator (either side handedness folded into `ε`), and conjugation
by an **arbitrary** word `g`. -/
inductive Step : Pres → Pres → Prop
  | inv (i : Fin 2) (P : Pres) :
      Step P (P.set i (wordInv (P.get i)))
  | mul (i j : Fin 2) (h : i ≠ j) (ε : Bool) (P : Pres) :
      Step P (P.set i (wordMul (P.get i)
        (if ε then wordInv (P.get j) else P.get j)))
  | conj (i : Fin 2) (g : Word) (P : Pres) :
      Step P (P.set i (conjBy g (P.get i)))

/-- Local stand-in for `Relation.ReflTransGen` (Mathlib at P4). -/
inductive ReflTransGen (r : α → α → Prop) : α → α → Prop
  | refl {a : α} : ReflTransGen r a a
  | tail {a b c : α} : ReflTransGen r a b → r b c → ReflTransGen r a c

def Reachable : Pres → Pres → Prop := ReflTransGen Step

def trivialPresentation : Pres := ⟨[1], [2]⟩

/-- Placeholder (P4: via Mathlib `PresentedGroup`): the group presented
by `⟨x, y ∣ r0, r1⟩` is trivial. -/
def Pres.PresentsTrivialGroup (_P : Pres) : Prop := sorry

end StandardAC

namespace Competition

open StandardAC

/-- The frozen 14 atomic moves of `ac-r2-v1` (DESIGN.md §1.3), in id
order.  Must stay byte-aligned with `move_spec.json`; the P4 library
pins this file's hash. -/
def atomicStep (m : Fin 14) (P : Pres) : Pres :=
  match m with
  | 0  => ⟨wordInv P.r0, P.r1⟩
  | 1  => ⟨P.r0, wordInv P.r1⟩
  | 2  => ⟨wordMul P.r0 P.r1, P.r1⟩
  | 3  => ⟨wordMul P.r0 (wordInv P.r1), P.r1⟩
  | 4  => ⟨P.r0, wordMul P.r1 P.r0⟩
  | 5  => ⟨P.r0, wordMul P.r1 (wordInv P.r0)⟩
  | 6  => ⟨conjBy [1] P.r0, P.r1⟩
  | 7  => ⟨conjBy [-1] P.r0, P.r1⟩
  | 8  => ⟨conjBy [2] P.r0, P.r1⟩
  | 9  => ⟨conjBy [-2] P.r0, P.r1⟩
  | 10 => ⟨P.r0, conjBy [1] P.r1⟩
  | 11 => ⟨P.r0, conjBy [-1] P.r1⟩
  | 12 => ⟨P.r0, conjBy [2] P.r1⟩
  | 13 => ⟨P.r0, conjBy [-2] P.r1⟩

inductive AtomicRel : Pres → Pres → Prop
  | step (m : Fin 14) (P : Pres) : AtomicRel P (atomicStep m P)

/-- Soundness half of the bridge: every atomic move is a special case
of a standard AC move (DESIGN.md §1.4).  Spike goal: this direction
should fall to case analysis once the `set/get` plumbing is stated
right. -/
theorem atomic_to_standard {P Q : Pres} (h : AtomicRel P Q) : Step P Q := by
  cases h with
  | step m P =>
    match m with
    | 0  => exact Step.inv 0 P
    | 1  => exact Step.inv 1 P
    | 2  => exact Step.mul 0 1 (by decide) false P
    | 3  => exact Step.mul 0 1 (by decide) true P
    | 4  => exact Step.mul 1 0 (by decide) false P
    | 5  => exact Step.mul 1 0 (by decide) true P
    | 6  => exact Step.conj 0 [1] P
    | 7  => exact Step.conj 0 [-1] P
    | 8  => exact Step.conj 0 [2] P
    | 9  => exact Step.conj 0 [-2] P
    | 10 => exact Step.conj 1 [1] P
    | 11 => exact Step.conj 1 [-1] P
    | 12 => exact Step.conj 1 [2] P
    | 13 => exact Step.conj 1 [-2] P

/-- The credibility linchpin of the counterexample track (DESIGN.md
§7.2, requirements §10): the reflexive-transitive closures agree.
`←` is soundness (`atomic_to_standard`); `→` needs conjugation
decomposition into single-generator conjugations, left-multiplication
derivation, and the relator-swap derivation — all numerically verified
feasible in DESIGN.md §1.4. -/
theorem ac_iff_atomic (P Q : Pres) :
    Reachable P Q ↔ ReflTransGen AtomicRel P Q := by
  constructor
  · intro h
    -- P4: induction on h; decompose each Step into atomic moves.
    sorry
  · intro h
    induction h with
    | refl => exact ReflTransGen.refl
    | tail _ hbc ih => exact ReflTransGen.tail ih (atomic_to_standard hbc)

/-- P4: generated from the manifest, one definition per challenge,
with the `instance_hash` recorded alongside. -/
def instancePres (id : String) : Pres := sorry

end Competition
