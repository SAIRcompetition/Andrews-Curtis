# ACC: The Andrews–Curtis Conjecture Competition

ACC is a mathematical discovery competition on the Andrews–Curtis
conjecture, open since 1965 and widely expected to be false, though no
counterexample has ever been verified. Teams are given a frozen pool of
10,115 balanced presentations of the trivial group — from warm-up
exercises to instances that are open research problems — and score by
trivializing them with atomic Andrews–Curtis moves, with the shortest
verified path winning the points. A second track accepts purported
disproofs of the conjecture for expert review.

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
moves[]}`, where `moves` are atomic AC move ids in the range 0–13 under
the frozen move specification `ac-r2-v1`. Submit only the moves: the
server replays each path deterministically from the challenge's
`initial_relators` and computes length, peak, and work itself, so any
client-asserted result field rejects the whole submission. The move
table, the exact-ordered target, the limits, and the full error-code
contract are in [rules/overview.md](rules/overview.md) and
[rules/evaluation.md](rules/evaluation.md);
`examples/sample_submission.json` shows the accepted shape.

## Reference tools

`tools/verifier/` is the reference verifier — pure Python, standard
library only — which replays a submission against the frozen manifest,
recomputes every hash, and runs the published golden vectors. The
production system runs the same sources; the server-side verifier
remains the sole authority for official results.
`tools/lean/` covers the optional Lean 4 fast track of the
counterexample submission process.

The production submission validator and leaderboard system run inside
the competition system; this tree contains the frozen data and the
reference implementations of the mathematical checks only.
