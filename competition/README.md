# Andrews–Curtis Conjecture Challenge (ACC)

**Prelaunch preview — registration and submissions are not open.** Rules,
data, and the reference verifier can be tried locally. Announced dates are
September 8, 2026 for registration, September 11 for Discovery, and September
20 for Prove; exact UTC times, the deadline, and the official freeze remain
pending.

ACC is one competition with four tracks:

| Track | Task |
|---|---|
| **AC Discovery** | Reduce rank-two presentations to `(x,y)` using 14 ordinary AC moves |
| **Stable AC Discovery** | Reduce the same presentations to empty using 257 moves, permitting ranks up to 8 |
| **AC Prove** | Prove or disprove the full ordinary conjecture |
| **Stable AC Prove** | Prove or disprove the full stable conjecture, with no rank bound |

The Discovery tracks share 10,115 initial presentations, giving 20,230
challenge records with **separate leaderboards**. The 424 solved training
presentations are outside both scored tracks. Submitted moves remain
private until the post-competition release. Prove submissions include the
conjecture, claim type, description, and complete argument in the description,
a paper/PDF, Lean at a fixed GitHub commit, an arXiv version, or a combination.
A PDF is optional.

The planned Prove platform will make all versions and comments public,
preserve server timestamps and IDs, and bind reasoned review decisions
to specific versions. Priority belongs to the earliest version confirmed
to contain a complete correct argument; borrowed work must be cited with
an explanation of contributions. Either conclusion can receive the
mathematical honor, without Discovery points or automatically ending
either Discovery track. All four tracks remain closed during prelaunch.

The full contestant-facing rules are in [rules/overview.md](rules/overview.md);
verification, scoring, hashes, Discovery confidentiality, and Prove's
public review, priority, and credit rules are specified
normatively in [rules/evaluation.md](rules/evaluation.md). Machine-readable
metadata is in `competition.yaml`.

For a proof or disproof of either full conjecture, use the
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
are move IDs 0–13 for `ac-v1-` challenges (`ac-r2-v1`) or 0–256 for
`sac-v1-` challenges (`sac-r8-v1`). A batch may mix both tracks.
Each solution contains only the challenge id
and moves; optional `method` and `notes` belong to the top-level
document. The verifier reads the move-spec version from the official
challenge and replays each path deterministically from its
`initial_relators` and computes length, peak, and work itself, so any
client-asserted result field rejects the whole submission. The move
tables, exact targets, limits, and the full error-code
contract are in [rules/overview.md](rules/overview.md) and
[rules/evaluation.md](rules/evaluation.md).
The [examples guide](examples/README.md) includes a successful training
submission covering both tracks, its expected receipt, and a separate rejection example.

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
competition opens. `tools/lean/AC.lean` defines both full conjectures;
formalizations need only `import AC`. `Check.lean` is an optional
auxiliary target, run separately with `lake build Check`.

Submission handling, public Prove versions and comments, review records,
and the leaderboard belong to the planned competition service. This
preview contains the data, rules, and reference implementations of the
mathematical checks.
