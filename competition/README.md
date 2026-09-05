# ACC: The Andrews–Curtis Conjecture Competition

**Prelaunch preview — registration and submissions are not open.** The
rules, 10,115-instance pool, training data, and reference verifier can
be tried locally now. The official freeze and all competition dates
are still to be announced; their metadata values are `null`.

ACC is a mathematical discovery competition on the Andrews–Curtis
conjecture, open since 1965 and widely expected to be false, though no
counterexample has ever been verified. The competition will give teams a pool of
10,115 balanced presentations of the trivial group — from warm-up
exercises to instances that are open research problems — and score by
trivializing them with atomic Andrews–Curtis moves, with the shortest
verified path winning the points. A second track is planned for
purported disproofs of the conjecture submitted as PDFs for expert
review after submissions open. The optional Lean route is not open.

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
`solutions[]` array of objects `{challenge_id, moves[]}`, where `moves`
are atomic AC move ids in the range 0–13 under the frozen move
specification `ac-r2-v1`. Each solution contains only the challenge id
and moves; optional `method` and `notes` belong to the top-level
document. The server reads the move-spec version from the official
challenge and replays each path deterministically from its
`initial_relators` and computes length, peak, and work itself, so any
client-asserted result field rejects the whole submission. The move
table, the exact-ordered target, the limits, and the full error-code
contract are in [rules/overview.md](rules/overview.md) and
[rules/evaluation.md](rules/evaluation.md);
The [examples guide](examples/README.md) includes a successful training
submission, its expected receipt, and a separate rejection example.

From the repository or exported package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

The training example is unscored and uses its own manifest; it is not
a solution to a challenge in the competition pool.

## Reference tools

`tools/verifier/` is the reference verifier — pure Python, standard
library only — which replays a submission against the supplied manifest,
recomputes every hash, and runs the included golden vectors. The
planned competition service will use the same verifier sources; only
its server-side verdicts will count as official results once the
competition opens. `tools/lean/` describes the optional Lean 4 route,
which is still in development and is not available for submissions.

Submission handling and the leaderboard belong to the planned
competition service. This preview contains the data, rules, and
reference implementations of the mathematical checks.
