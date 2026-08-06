# Competition formalization — O-3 spike (P4 seed)

Status: **spike**, per DESIGN.md O-3 ("do not wait for P4"). Builds
offline in seconds with no dependencies:

```sh
cd lean/Competition && lake build
```

What exists and what it establishes:

| Item | State | Meaning |
|---|---|---|
| `StandardAC.Step` (full, unbounded, non-stable AC relation) | defined | the sketch of DESIGN.md §7.2 typechecks |
| `Competition.atomicStep` (the frozen 14 moves) | defined | byte-aligned with `move_spec.json` id order |
| `atomic_to_standard` (soundness, §1.4) | **proven, sorry-free** | the easy half of the bridge falls to case analysis, as predicted |
| `ac_iff_atomic` (the credibility linchpin) | stated; `→` direction `sorry` | P4 work: conjugation decomposition, left-mul derivation, relator-swap derivation (numerically verified feasible, §1.4) |
| `Pres.PresentsTrivialGroup` | `sorry` placeholder | P4: real definition via Mathlib `PresentedGroup` |
| `instancePres` | `sorry` placeholder | P4: generated from `manifest.json` with instance hashes |

P4 hardening checklist (DESIGN.md §7.5): swap the local `ReflTransGen`
for Mathlib's `Relation.ReflTransGen`; prove `reduce` equals the
verifier's left-fold reduction; remove every `sorry`; pin
`lean-toolchain`, Mathlib commit, `lake-manifest.json`, and the
container digest by hash; wire the CI gates (offline build,
`#print axioms` whitelist, source scan, frozen-definition SHA-256,
independent-machine repeat).
