# Andrews–Curtis Conjecture Challenge (ACC)

**Prelaunch preview — registration and submissions are not open.** The
rules, 10,115-instance pool, training data, and reference verifier can
be tried locally now. The official freeze and all competition dates
are still to be announced; their metadata values are `null`.

ACC is one competition with two tracks:

- **Discovery Track:** find short atomic Andrews–Curtis trivializations
  of 10,115 balanced presentations of the trivial group. The shortest
  verified paths earn points; 424 solved training instances are separate
  from the scored pool. Submitted moves remain private until the
  post-competition certificate release.
- **Prove Track:** prove or disprove the full conjecture. Submissions
  include a description and a complete argument, carried in the
  description, a paper/PDF, Lean material at a fixed GitHub commit, an
  arXiv version, or a combination. A PDF is optional.

The planned Prove platform will make all versions and comments public,
preserve server timestamps and IDs, and bind reasoned review decisions
to specific versions. Priority belongs to the earliest version confirmed
to contain a complete correct argument; borrowed work must be cited with
an explanation of contributions. Either conclusion can receive the
mathematical honor, without Discovery points or automatically ending
Discovery Track. Both tracks remain closed during prelaunch.

The full contestant-facing rules are in [rules/overview.md](rules/overview.md);
verification, scoring, hashes, Discovery confidentiality, and Prove's
public review, priority, and credit rules are specified
normatively in [rules/evaluation.md](rules/evaluation.md). Machine-readable
metadata is in `competition.yaml`.

For a proof or disproof of the full conjecture, use the
[official statement](rules/statement.md) and
[Lean build instructions](tools/lean/README.md).

## Organizers

ACC is co-organized by (in alphabetical order by surname):

* Lucas Fagan
* Sergei Gukov
* Terence Tao

## Discovery submission format

A submission is a single JSON document, `submission.json`, carrying a
`solutions[]` array of objects `{challenge_id, moves[]}`, where `moves`
are atomic AC move ids in the range 0–13 under the frozen move
specification `ac-r2-v1`. Each solution contains only the challenge id
and moves; optional `method` and `notes` belong to the top-level
document. The verifier reads the move-spec version from the official
challenge and replays each path deterministically from its
`initial_relators` and computes length, peak, and work itself, so any
client-asserted result field rejects the whole submission. The move
table, the exact-ordered target, the limits, and the full error-code
contract are in [rules/overview.md](rules/overview.md) and
[rules/evaluation.md](rules/evaluation.md).
The [examples guide](examples/README.md) includes a successful training
submission, its expected receipt, and a separate rejection example.

From the repository or exported package root:

```sh
PYTHONPATH=competition/tools/verifier python3 -m acms_verify \
  --manifest competition/examples/training_manifest.json \
  --submission competition/examples/sample_submission.json --pretty
```

The training example is unscored and uses its own manifest; it is not
a solution to a challenge in the competition pool. Bridge certificates
themselves score zero; a complete valid trivialization derived using a
bridge scores normally for the challenge it solves, at its full length.

Prove submission and review details are in
[rules/evaluation.md](rules/evaluation.md) §9. Lean arguments remain
subject to review of their statement, scope, and trust boundary.

## Reference tools

`tools/verifier/` is the reference verifier — pure Python, standard
library only — which replays a submission against the supplied manifest,
recomputes every hash, and runs the included golden vectors. The
planned competition service will use the same verifier sources; only
its server-side verdicts will count as official results once the
competition opens. `tools/lean/AC.lean` defines the full conjecture;
formalizations need only `import AC`. `Check.lean` is an optional
auxiliary target, run separately with `lake build Check`.

Submission handling, public Prove versions and comments, review records,
and the leaderboard belong to the planned competition service. This
preview contains the data, rules, and reference implementations of the
mathematical checks.
