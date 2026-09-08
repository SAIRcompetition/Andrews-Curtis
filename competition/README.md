# ACC: The Andrews–Curtis Conjecture Competition

ACC is a mathematical discovery competition on the Andrews–Curtis
conjecture and its stable version, both open since 1965. The ordinary
conjecture is widely expected to be false, though no counterexample has
ever been verified. Teams are given a frozen pool of 10,115 balanced
presentations of the trivial group — from warm-up exercises to
instances that are open research problems — and compete in four tracks:

| Track | Task | Outcome |
|---|---|---|
| 1 — AC trivialization | reduce a presentation to $\langle x,y \mid x,y\rangle$ with the 14 atomic AC moves of `ac-r2-v1` | leaderboard, shortest verified path wins |
| 2 — stable AC trivialization | reduce the *same* presentation to the empty presentation with the 257 moves of `sac-r8-v1`, which add stabilization and destabilization | separate leaderboard, same formula |
| 3 — AC proof or disproof | a self-contained PDF settling the Andrews–Curtis conjecture | expert review by the organizer panel |
| 4 — stable AC proof or disproof | a self-contained PDF settling the stable Andrews–Curtis conjecture | expert review by the organizer panel |

The two trivialization tracks run on the same presentations and the
same verifier: `sac-v1-N` is the same presentation as `ac-v1-N`. They
are scored independently, on separate leaderboards that are never
summed, with a permanent **First Solver** honor on each.

The full contestant-facing rules are in [rules/overview.md](rules/overview.md);
verification, scoring, hashes, and confidentiality are specified
normatively in [rules/evaluation.md](rules/evaluation.md). Machine-readable
metadata is in `competition.yaml`.

## Organizers

ACC is co-organized by (in alphabetical order by surname):

* Lucas Fagan
* Sergei Gukov
* Terence Tao

## Submission format

A submission is a single JSON document, `submission.json`, carrying a
`solutions[]` array of objects `{challenge_id, move_spec_version,
moves[]}`, where `moves` are atomic move ids under the specification
the challenge carries: **0–13 under `ac-r2-v1`, 0–256 under
`sac-r8-v1`**. The `challenge_id` prefix selects the track — `ac-v1-`
is track 1, `sac-v1-` is track 2 — and one file may mix solutions to
both. Submit only the moves: the server replays each path
deterministically from the challenge's `initial_relators` and computes
length, peak, and work itself, so any client-asserted result field
rejects the whole submission. The move tables, the targets (the exact
ordered pair `[[1],[2]]` for `ac-r2-v1`, the empty presentation `[]`
for `sac-r8-v1`), the limits, and the full error-code contract are in
[rules/overview.md](rules/overview.md) and
[rules/evaluation.md](rules/evaluation.md);
`examples/sample_submission.json` shows the accepted shape.

## Reference tools

`tools/verifier/` is the reference verifier — pure Python, standard
library only — which replays a submission against the frozen manifest
under either move specification, recomputes every hash, and runs the
published golden vectors. The production system runs the same sources;
the server-side verifier remains the sole authority for official
results. `tools/lean/` covers the optional Lean 4 fast track of the
proof-or-disproof tracks.

The production submission validator and leaderboard system run inside
the competition system; this tree contains the frozen data and the
reference implementations of the mathematical checks only.
