# Lean counterexample track

The frozen competition formalization (definitions, `ac_iff_atomic`,
template project, toolchain pins, container digest) is delivered in
milestone P4 and will be published here. Until then, see
`../../rules/evaluation.md` §9 for the frozen requirements: offline
`lake build`, axiom whitelist `propext` / `Classical.choice` /
`Quot.sound`, no `sorry`/`unsafe`/`native_decide`, hash-pinned
definitions, independent-machine re-check.
