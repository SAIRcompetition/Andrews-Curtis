# SAIR Andrews–Curtis Competition — Backend Design Document v0.3 (MS Phase)

**Current release state: prelaunch / development preview.** The current
competition pool has 10,115 instances. Registration, submissions, and
official scoring are not open; the PDF review channel is planned for after
submissions open, and the optional Lean route is not available. Earlier
dated decision records below are historical where they describe a smaller
pool or imply a live service.

`build/competition_state.json` is the maintained source for `status` and
release metadata. Current `status` is `prelaunch`; `freeze_date`,
`freeze_commit`, `registration_opens`, `submissions_open`,
`submission_deadline`, and `certificate_release` are all `null`.
`build/build_manifest_v2.py` synchronizes generated manifest and YAML
metadata from this source. A preview is runnable locally; it is not an
official frozen release (§9.3, §10.1).

> **Scope: backend only.** This document covers spec / data / verifier / scoring / submission
> service / public API / Lean pipeline. **Frontend pages are out of scope for this design** —
> our only deliverable to the frontend is the API contract in Section 8 (including the public-field whitelist).
>
> **[D-n]** = decision item, summarized in Section 12.
> **[Verified]** = math/data conclusions from scripts run on this machine; see Section 11 for the scripts.
>
> **Decision record (2026-08-06)**
>
> | # | Decision | Conclusion |
> |---|---|---|
> | — | Development scope | Backend only; do **P1** first (frozen definitions + manifest + verifier + unit tests) |
> | **D-0** | Repo root | `caltech/Andrews–Curtis/` ✅ **landed** (`reference/index.html` copied with SHA-256 verified; the empty `prototype/` deleted) |
> | **D-2** | $r_1$ convention | **Adopt the prototype's $x w^{-1}$** ⚠️ the formula in the requirements document §2 needs an erratum, see §1.1 |
> | **D-3** | Challenge pool scope | Include only the **550 open** entries; the 216 uncertified ones are not included |
> | **D-8** | `base_score` | All = **1**, to be adjusted manually later; code reads it from the manifest |
> | **D-10** | Verifier language | **Python as the sole implementation** (no Rust / WASM / Pyodide / JS) |
> | **D-10a** | Browser-side verifier | **Not built**. Contestants self-check with a downloadable Python package |
> | **D-11** | `max_work` | **5 000 000** (§4.3) |
> | **D-5** | bridge certificate | **No points**; only registered in the API |
> | **D-4 / D-6** | — | No per-class damping / no organizer baseline |
> | **D-1 / D-7** | — | Frontend matters, **moved out of this document** |
> | — | Public release package | Build `ACMS-public` following the `SAIRcompetition/IGP24-public` structure (§9) |
>
> **Only D-9 (timeline) remains pending**; it does not block P1.

---

## 0. Scope and External Contract

### 0.1 What this document does / does not do

| | |
|---|---|
| **Does** | Frozen mathematical definitions and move spec, manifest schema and hash, deterministic verifier, submission service, scoring engine, path confidentiality rules, public API, Lean counterexample pipeline |
| **Does not** | Any pages, components, styling, tab layouts, or interactions. The frontend is designed separately |

The frontend–backend interface is **the API in Section 8**. Anything a page needs to
display (current shortest length, First Solver, $k_i$, $V_i$, certificate hash, peak
length, bridge list, …) the backend must expose as **structured fields** in the API;
how the page lays it out is not our concern. Conversely, **the API's public-field
whitelist is the confidentiality boundary** (§6.1, §8) — whatever the frontend cannot
obtain is exactly what must not leak during the competition.

### 0.2 Alignment with IGP24 (API / scoring layer only)

IGP24's public interface shape (extracted from its frontend bundle) is
`/api/<competition>/{leaderboard,discoveries,scoring-history}`,
plus `/competitions/:id.md` (the full rules as a single Markdown file) and `/llms.txt`.
ACMS adopts the same shape, with slug `acms` (§8).

Three **deliberate deviations** from IGP24 at the scoring layer:

1. IGP24's scoring unit is the `(24Tt, r)` pair, which naturally has the frozen LMFDB
   baseline acting as "a baseline team". ACMS's scoring unit is the challenge, and v1
   has **no organizer baseline team** (§5.4).
2. IGP24 publishes the discriminant and merely withholds the coefficients. ACMS
   **publishes nothing except length during the competition** (§6), because the move
   sequence itself is the answer.
3. IGP24 has a single numeric target. ACMS has two tracks: the regular leaderboard +
   the Lean counterexample track (§7); the latter does not enter the regular leaderboard.

---

## 1. Frozen Mathematical Objects and the Move Specification (`ac-r2-v1`)

### 1.1 Encoding

| Symbol | Encoding |
|---|---|
| $x$ | `1` |
| $x^{-1}$ | `-1` |
| $y$ | `2` |
| $y^{-1}$ | `-2` |

Word = `int32[]`. Presentation = **ordered pair** `[r0, r1]`; both words are kept freely reduced.

Miller–Schupp instances:

$$MS(n,w)=\langle x,y \mid x^{-1}y^n x y^{-(n+1)},\ x\,w^{-1} \rangle,\qquad n\ge 1,\ \sigma_x(w)=0.$$

The initial state is given directly by the manifest as `initial_relators` (the server does not recompute it from `n,w`);
`n` and `w` serve only as human-readable metadata. This makes the manifest the single source of truth,
and what `instance_hash` covers is the actual replay starting point.

> ### ⚠️ [D-2 Decided] The requirements document §2 needs an erratum
>
> Requirements §2 writes $r_1 = x^{-1}w$; **this design freezes $r_1 = x\,w^{-1}$**
> (consistent with `ms_()` in `reference/index.html` and the Shehper et al. dataset).
>
> The two are equivalent as group relations (both say $x = w$), but they **differ as ordered words in the free group**,
> and the verifier replays literally, so different initial states ⟹ different `instance_hash` ⟹
> different path-length baselines. One of the two had to be chosen and frozen for good.
>
> Note that the two are **not** inverses of each other: $(x^{-1}w)^{-1} = w^{-1}x \neq x w^{-1}$.
> The actual relationship is "invert + conjugate by $x$":
> **[Verified]** $x w^{-1} = x\,(x^{-1}w)^{-1}\,x^{-1}$, i.e. move 1 → move 10, exactly 2 steps.
>
> | $w$ | $x^{-1}w$ per requirements §2 | **$x w^{-1}$ frozen by this design** |
> |---|---|---|
> | $y$ | `[-1, 2]` | **`[1, -2]`** |
> | $y^{-1}$ | `[-1,-2]` | **`[1, 2]`** |
> | $yxy^{-1}$ | `[-1,2,1,-2]` | **`[1,2,-1,-2]`** |
>
> **Action item**: change the formula in the requirements document §2 to
> $MS(n,w)=\langle x,y \mid x^{-1}y^nxy^{-(n+1)},\ x w^{-1}\rangle$.
> This is the **only** place among all decisions in this round that requires revising the requirements text.

### 1.2 Target state

$$T=(x,\;y)\quad\Longleftrightarrow\quad \texttt{[[1],[2]]}$$

**Exact ordered**. $(y,x)$, $(x^{-1},y)$, etc. are **not** the target; you must walk to $T$ using atomic moves that count toward scoring.

**[Verified]** Under the 14-move set of §1.3, the minimal cost from each of the 8 "loose trivial states" to the exact $T$:

| Final state | Min moves to $T$ | One shortest path (move ids) |
|---|---|---|
| $(x,y)$ | 0 | — |
| $(x,y^{-1})$ | 1 | `[1]` |
| $(x^{-1},y)$ | 1 | `[0]` |
| $(x^{-1},y^{-1})$ | 2 | `[0,1]` |
| $(y^{-1},x)$ | 4 | `[2,5,2,8]` |
| $(y,x^{-1})$ | 4 | `[3,4,3,10]` |
| $(y^{-1},x^{-1})$ | 4 | `[2,0,4,3]` |
| $(y,x)$ | **5** | `[0,2,5,2,8]` |

That is, the "exact ordered endpoint" rule adds at most **5** steps to any path; the upper bound is a constant, provable by exhaustive enumeration, and cannot
make any instance unsolvable. This table must go into the rules text and the `move_spec` download,
so contestants do not mistakenly believe extra theory is required.

### 1.3 The frozen 14 atomic moves

`move_spec_version = "ac-r2-v1"`. **Once frozen, IDs must never change**.

| id | Category | Effect | Inverse move |
|---:|---|---|---:|
| 0 | inversion | $r_0 \leftarrow r_0^{-1}$ | 0 |
| 1 | inversion | $r_1 \leftarrow r_1^{-1}$ | 1 |
| 2 | multiplication | $r_0 \leftarrow r_0 r_1$ | 3 |
| 3 | multiplication | $r_0 \leftarrow r_0 r_1^{-1}$ | 2 |
| 4 | multiplication | $r_1 \leftarrow r_1 r_0$ | 5 |
| 5 | multiplication | $r_1 \leftarrow r_1 r_0^{-1}$ | 4 |
| 6 | conjugation | $r_0 \leftarrow x\,r_0\,x^{-1}$ | 7 |
| 7 | conjugation | $r_0 \leftarrow x^{-1} r_0\,x$ | 6 |
| 8 | conjugation | $r_0 \leftarrow y\,r_0\,y^{-1}$ | 9 |
| 9 | conjugation | $r_0 \leftarrow y^{-1} r_0\,y$ | 8 |
| 10 | conjugation | $r_1 \leftarrow x\,r_1\,x^{-1}$ | 11 |
| 11 | conjugation | $r_1 \leftarrow x^{-1} r_1\,x$ | 10 |
| 12 | conjugation | $r_1 \leftarrow y\,r_1\,y^{-1}$ | 13 |
| 13 | conjugation | $r_1 \leftarrow y^{-1} r_1\,y$ | 12 |

After every step, apply deterministic free reduction immediately (left-fold cancellation of adjacent mutually inverse letters, see §3.2).

**The set is closed under inversion** (the last column of the table above is a surjective involution), so the AC reachability relation is symmetric:
paths can be searched bidirectionally and bridges can be used in reverse. This is the practical meaning of a "symmetric move set".

### 1.4 Compatibility with the standard AC relation

Requirements §10 requires proving that the finite closure of the production atomic moves is compatible with the standard AC relation. Two directions:

* **Soundness** (a path is found ⟹ genuinely AC-equivalent): every atomic move is a special case of a standard AC move
  (generator conjugation is a special case of conjugation by an arbitrary word). Trivial.
* **Completeness** (standard AC relation ⊆ finite closure of the atomic moves): three things are needed
  1. Conjugation by an arbitrary word $g$ = $|g|$ single-generator conjugations. ✔ Obvious
  2. Left multiplication $r_i \leftarrow r_j r_i$: $r_j r_i = r_j (r_i r_j) r_j^{-1}$, right-multiply then conjugate. ✔
  3. **Relator swap** $(r_0,r_1)\to(r_1,r_0)$: not in the move table, must be derived.
     **[Verified]** Bidirectional BFS on random word pairs confirms the swap is indeed derivable and cheap:

     | $(r_0,r_1)$ | Swap cost |
     |---|---:|
     | $(y x^{-1},\ y^{-1} x)$ | 4 |
     | $(xxy,\ xxx)$ | 5 |
     | $(y^{-1}y^{-1}xx,\ y^{-1}xxx)$ | 6 |

     The general case follows the Nielsen identity: 3 multiplications + some number of conjugations, cost $O(|r_0|+|r_1|)$, finite. ✔

Conclusion: **14-move closure = the standard (non-stable, unbounded) AC relation**. This must be proved in the Lean library as the
`ac_iff_atomic` theorem (§7.2); otherwise a counterexample proof only targets the competition metric and does not constitute an AC counterexample.

### 1.5 ID remapping from the prototype 12-move set

`reference/index.html` uses a 12-move set (missing $r_i \leftarrow r_i r_j^{-1}$,
with its conjugation block starting at 4). **The move ids are incompatible**; training-set paths must be remapped:

| prototype id | Effect | `ac-r2-v1` id |
|---:|---|---:|
| 0 | $r_0\leftarrow r_0^{-1}$ | 0 |
| 1 | $r_1\leftarrow r_1^{-1}$ | 1 |
| 2 | $r_0\leftarrow r_0 r_1$ | 2 |
| 3 | $r_1\leftarrow r_1 r_0$ | **4** |
| 4,5,6,7 | conj $r_0$ by $x,x^{-1},y,y^{-1}$ | 6,7,8,9 |
| 8,9,10,11 | conj $r_1$ by $x,x^{-1},y,y^{-1}$ | 10,11,12,13 |

That is, `f(m) = m` for m≤2, `f(3)=4`, `f(m)=m+2` for m≥4.

**Complete training-set conversion recipe** (two concatenated segments). Because D-2 chose the prototype's $r_1$ convention,
**no** convention-bridging prefix is needed; there are only two steps:

```
new_path = [ f(m) for m in old_path ]   # ① move id remapping (table above)
         + CANON[final_state]           # ② canonicalization moves to the exact ordered T=(x,y), see the §1.2 table
```

**[Verified] All 424 paths converted successfully, 0 failures**, with endpoints landing exactly on $(x,y)$
(script `build/checks/convert.py`):

| Metric | min | median | max | mean |
|---|---:|---:|---:|---:|
| Original prototype length (12-move, loose endpoint) | 6 | 23 | 155 | 30.6 |
| **`ac-r2-v1` length** (14-move, exact endpoint) | 7 | **26** | 159 | 33.6 |
| peak total relator length | 7 | 14 | 25 | 14.7 |
| `work` = Σ total length after each step (§4.3) | 43 | 229 | 2161 | 347.0 |

That is, the frozen "exact ordered endpoint" decision adds only **3 steps (median)** to known paths, and the peak is completely unchanged.
This table also serves as the empirical basis for the limit values chosen in §4.3.

The published training set must use the remapped ids and carry `move_spec_version` in file names/fields.
The prototype's 12-move table may appear only in `reference/` and literature citations;
it must **not** appear in the rules text or the `move_spec` download.

---

## 2. Challenge Pool: The Real State of MS-1190

> ### Update 2026-09-03 — upstream data source, and the pool beyond D-3
>
> **Upstream.** `reference/index.html` is **no longer the upstream** for the frozen data. The
> manifest is now built from `build/data/`, synced from the SAIR dataset release by
> `build/sync_dataset.py` and assembled by `build/build_manifest_v2.py`. `reference/index.html`
> stays exactly as it is — frozen, read-only, cited as the prototype and as the provenance of
> the 424 converted training paths — and is not a production dependency.
>
> **Pool.** D-3 (§2.2) scoped v1 to the 550 open MS-1190 instances. The shipped pool is larger:
> **10 115 challenges**, `ac-v1-00001 … ac-v1-10115`, spanning warm-up to research frontier,
> drawn from an extended Miller–Schupp family, automorphic disguises of known hard classes, and
> solvable-by-construction walks, and containing all 550 open MS-1190 instances. Instances with
> a publicly known certificate are excluded from scoring; `training_424.json` remains published
> training data. Per-instance difficulty, provenance, and status are **withheld** from
> contestants — an extension of the §2.3 anti-hint reasoning (cf. O-4's numbering-leaks-difficulty
> point) from ordering to metadata generally. The analysis in §2.1–§2.4 below is retained as the
> record of how the MS-1190 core was scoped.

### 2.1 [Verified] Actual composition of the prototype dataset

`reference/index.html` embeds 1190 instances of $MS(n,w)$, $n=1\ldots7$ × 170 values of $w$. Breakdown:

| status | has path | count | meaning |
|---|---|---:|---|
| `trivial` | yes | **424** | has a publicly replayable certificate |
| `trivial` | no | **216** | reported as solved in the literature, but **no publicly replayable certificate** |
| `unsolved` | no | **550** | no known trivialization |

**All 424 paths replay successfully under the prototype's 12-move semantics, with 0 failures.**
Their statistics: length min 6 / median 23 / max 155 / mean 30.6;
peak total relator length min 7 / median 14 / max 25.
Only 38 of them land exactly on the exact ordered $T=(x,y)$; the rest need the canonicalization moves of §1.2
(1 move for 80, 2 moves for 43, 4 moves for 187, 5 moves for 76).
→ After switching to `ac-r2-v1`, the training-set median length goes from 23 to **26** (measured in §1.5).

### 2.2 The two tiers of "no public certificate"

Requirements §3, item 1 reads "instances that still have no public, replayable trivialization certificate as of the freeze date".
Taken literally, that is **550 + 216 = 766** instances, not 550. The two tiers differ completely in difficulty:

* **Tier T1 — Open (550 instances)**: no known trivialization of any kind. Finding a path = a new mathematical result.
* **Tier T2 — Uncertified (216 instances)**: reported solvable in the literature but with no public atomic path.
  Finding a path = supplying a reproducible piece of evidence — real value, but below T1.

**[D-3 Decided: the v1 official challenge pool admits only the 550 T1 instances.]**
The 216 T2 instances do not enter the pool, are not scored, and receive no handling in v1.
The manifest still keeps the `status_at_freeze` field for future extension, but v1 only generates `open` entries.

`status_at_freeze` values: `open` (the only one used in v1) | `uncertified` | `certified`.
The latter two are reserved for later phases.

→ **The v1 official challenge pool = 550 challenges, all with `status_at_freeze = "open"`, `scored = true`.**

### 2.3 AC-equivalence class: a risk that must be handled head-on

The prototype's `cls` field partitions the 550 open instances into **261 reported classes**:

| class size | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 9 | 16 | 22 | 34 | 36 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| class count | 193 | 16 | 19 | 10 | 8 | 5 | 4 | 2 | 1 | 1 | 1 | 1 |

The 4 largest classes cover 36+34+22+16 = **108 instances** (19.6% of the open set).
If these classes are real, one breakthrough could cascade into solving dozens of challenges.

Three verified facts determine how to handle this:

1. **[Verified] The `cls` label is not a quantity under our metric**: its prefix number disagrees with the MS initial
   total relator length in 354/550 cases (and always `cls ≤ actual length`),
   which shows it is the representative length obtained by external work reducing over **a different move set (the substitution graph)** —
   it cannot be carried into this competition as-is.
2. **[Verified] There is no cheap atomic bridge within a class**: for each of the 4 largest classes we took
   two members and ran bidirectional BFS (node cap 250,000, peak-length cap = max(initial length)+8);
   `14_1`, `13_1`, `15_1`, `16_1` — **no bridge found in any of them**.
   (This is "not found within that budget", not "does not exist" — exactly the reason requirements §3 forbids merging based on paper tables.)
3. **[Verified] The move set is closed under inverses** (§1.3), so a bridge $A\to B$ is naturally usable in reverse:
   given a solution $A\to T$ and a bridge $A\to B$, you obtain $B\to T$, with length
   $=|{\rm bridge}|+|A\to T|$.

**Design conclusion (all three take effect together)**

* **v1 scores per challenge, item by item, with no merging of any kind.** Requirements §3 already explicitly forbids merging based on paper tables,
  and we have verified that bridges are not cheap under our metric.
* **Add a bridge certificate submission type** (§4.4). A verified bridge is a
  real, machine-checkable mathematical fact, published via the `bridges[]` field of `GET /challenges/:id`,
  and is the **only** admissible evidence for any future merging. v1 does not auto-merge scoring because of a bridge;
  merging may only be executed by the organizers at an announced scoring epoch boundary (policy hook, off by default).
* **The "shortest path only" rule itself suppresses bridge arbitrage**: a bridge-derived path
  is necessarily longer than the direct solution of the original challenge and usually earns no score on it. This must be written into the Rules,
  so contestants understand that bridges are honor and information, not a score-farming shortcut.

**[D-4]** Should `base_score` be damped by reported class size (e.g. $V_i = V/\sqrt{|{\rm class}|}$)?
**Recommendation: do not.** That would amount to injecting unverified external paper tables into the scoring formula, conflicting with the spirit of §3.
Recommend equal scores within a tier, and in the API put `reported_class` inside the `source` object
with a `reported_class_normative: false` flag, so the frontend can label it as non-normative metadata.

### 2.4 `base_score` $V_i$

**[D-8 Decided: v1 sets `base_score = 1` everywhere; manual adjustment later.]**

All 550 entries in the manifest carry `"base_score": 1`. Code **must** read it from the manifest —
no hardcoding, no assuming all challenges score equally — because it will be manually changed later.
Accompanying requirements:

* The scoring engine does nothing with $V_i$ beyond "read → multiply by $2^{1-k_i}$", with no simplification that depends on "all $V$ being equal".
* Scoring tests include at least one fixture with **non-uniform** $V_i$ (e.g. `1, 7, 100`),
  so that "all 1s" cannot leave the $V_i$ multiplication path untested.
* Changing `base_score` **does not change** `instance_hash` (§3.2 deliberately excludes it from the hash),
  so manual score adjustments never invalidate any verified certificate and never require re-freezing the challenge pool.
* After changing `base_score`, trigger a full `recompute()` (§5.2) and write a new `scoring_run` record.

There is no need for $V_i$ to be a multiple of $2^k$, because scoring uses exact rational arithmetic (§5.5).

---

## 3. Challenge Manifest

### 3.1 Schema

`competition/challenges/manifest.json` (`manifest_version: acms-ms-v1`):

```jsonc
{
  "manifest_version": "acms-ms-v1",
  "competition": "acms",
  "move_spec_version": "ac-r2-v1",
  "move_spec_hash": "sha256:…",          // §3.3
  "freeze_date": null,
  "generators": ["x", "y"],
  "target_relators": [[1], [2]],
  "limits": { "max_path_length": 100000, "max_total_relator_length": 10000,
              "max_work": 5000000 },
  "challenges": [
    {
      "challenge_id": "ms-v1-0001",
      "family": "miller-schupp",
      "n": 3,
      "w": "x^{-1}y^{-1}xy^{-1}",
      "generators": ["x", "y"],
      "initial_relators": [[-1,2,2,2,1,-2,-2,-2,-2], [1,2,-1,2,1]],
      "target_relators": [[1], [2]],
      "move_spec_version": "ac-r2-v1",
      "status_at_freeze": "open",
      "scored": true,
      "base_score": 1,
      "instance_hash": "sha256:…",       // §3.2
      "source": {
        "presentation_set": "Shehper et al. 2025, MS-1190",
        "status_source": "Fagan et al., The Two-Hump Problem, ICML 2026",
        "reported_class": "13_1",
        "reported_class_size": 34,
        "reported_class_normative": false
      },
      "freeze_date": null
    }
  ]
}
```

`initial_relators` must be in **freely reduced** form; the manifest builder is responsible for reducing them and asserting idempotence.

### 3.2 `instance_hash`

Serialization uses an **explicit byte template** rather than "some JSON canonicalization scheme" — fixed key order, no whitespace, no non-ASCII, integers in shortest decimal form (`-1`, not `-01`; `-0` forbidden), so any implementation can reproduce it byte for byte:

```
canon = '{"challenge_id":"<id>","generators":["x","y"],'
      + '"initial_relators":[[<r0>],[<r1>]],'
      + '"target_relators":[[1],[2]],'
      + '"move_spec_version":"<ver>","move_spec_hash":"<sha256:...>"}'
instance_hash = "sha256:" + lowercase_hex(SHA256(utf8(canon)))
```

`certificate_hash` works the same way:

```
canon = '{"challenge_id":"<id>","move_spec_version":"<ver>","moves":[<m0>,<m1>,...]}'
```

In both templates, `<ver>` is read from the official challenge's
`move_spec_version`; contestants do not supply this field. The canonical
certificate bytes retain the version so existing certificate hashes stay valid.

This way an independent third-party implementation needs no RFC 8785 dependency and never trips over the JSON serialization quirks of individual languages.

This is exactly what the requirements demand: "covers the initial state, the target state, and the move specification."
It **excludes** `base_score`, `status_at_freeze`, and `source` — these are policy fields, and changing them must not invalidate already-verified certificates.

### 3.3 `move_spec_hash` and `manifest_hash`

```
move_spec_hash = sha256(JCS of the frozen 14-row move table, including id/category/params/inverses)
manifest_hash  = sha256(JCS of sorted list of instance_hash)
```

All three hashes are published in the Overview / Evaluation Setup / `GET /challenges`.
**Acceptance §16.11**: changing the manifest or the move spec changes at least
one hash. Replay and certificate hashing use the official challenge's version,
not a contestant-supplied value.

---

## 4. Submissions and Verification

### 4.1 Regular submission format (`POST /submissions`)

```json
{
  "solutions": [
    { "challenge_id": "ms-v1-0001", "moves": [0,4,8,3] }
  ]
}
```

Each solution must contain exactly `challenge_id` and `moves`. The top-level
document may also include optional `method` (a method name) and `notes` (free
text, at most 2000 characters). The server resolves `move_spec_version` from
the official challenge for verification and certificate hashing.

The server **does not accept** any user-claimed length / endpoint / state / score fields;
if keys such as `length`, `score`, or `final_state` appear, the whole submission is rejected with
`CLIENT_ASSERTED_RESULT` (aligned with IGP24's clean-up principle that "claimed columns are treated as invalid input",
but we are stricter: reject outright, because the only use of such fields is probing).

### 4.2 Deterministic verifier

Pure integer arithmetic, no floating point, no concurrency, no randomness. Pseudocode:

```
verify(challenge, moves, limits):
  move_spec_version = challenge.move_spec_version  # official manifest value
  assert len(moves) <= limits.max_path_length       -> E_PATH_TOO_LONG
  s = challenge.initial_relators            # already reduced
  peak = work = |s0| + |s1|
  for k, m in enumerate(moves):
      if not (integer(m) and 0 <= m <= 13): -> E_BAD_MOVE_ID(k, m)
      s = free_reduce(apply(s, m))
      tot = |s0| + |s1|
      if tot > limits.max_total_relator_length: -> E_LENGTH_LIMIT(k, tot)
      peak = max(peak, tot); work += tot
      if work > limits.max_work:            -> E_WORK_BUDGET(k, work)   # §4.3
  if s != challenge.target_relators:        -> E_NOT_TARGET(final_shape=(|s0|,|s1|))
  return { ok, length: len(moves), peak_total_relator_length: peak, work: work,
           certificate_hash: sha256(JCS{challenge_id, move_spec_version, moves}) }
```

`free_reduce`: single left-fold stack cancellation (pop when `out[-1] == -a`, otherwise push).
Because each step only concatenates at one or both ends, incremental reduction yields the same result as reducing the whole word — this must have a unit test.

Error codes are part of the API contract; every one carries `move_index` so contestants can self-diagnose:

| code | trigger |
|---|---|
| `E_UNKNOWN_CHALLENGE` | `challenge_id` not in the manifest |
| `E_BAD_MOVE_ID` | move is not an integer or not in 0–13 |
| `E_PATH_TOO_LONG` | step count exceeds the limit |
| `E_LENGTH_LIMIT` | intermediate-state total relator length exceeds the limit |
| `E_WORK_BUDGET` | cumulative work exceeds the limit (§4.3, prevents CPU exhaustion) |
| `E_NOT_TARGET` | every step is legal but the endpoint ≠ $(x,y)$ |
| `E_MALFORMED` | JSON corrupted / truncated / wrong type |
| `E_DUPLICATE_CHALLENGE` | same challenge repeated within one submission |
| `E_CLIENT_ASSERTED_RESULT` | forbidden field present |

**Whole-submission rejection vs per-item rejection**: structural errors (`E_MALFORMED`, `E_DUPLICATE_CHALLENGE`,
`E_CLIENT_ASSERTED_RESULT`, exceeding the item-count/byte caps) reject the whole submission and do **not** count against the daily quota;
single-path errors (all other codes) reject only that item, the remaining items are stored as usual, and a per-item report is returned.

### 4.3 Submission limits and work budget

| Item | Recommended value | Basis |
|---|---:|---|
| Submissions per team per day | 100 | Website and API counted jointly |
| Solutions per submission | 500 | |
| Raw body cap | 4 MB | AC paths are longer than polynomials |
| `max_path_length` | 100 000 | Longest known path is 159 |
| `max_total_relator_length` | 10 000 | Largest known peak is 25 |
| **`max_work`** | **5 000 000** | Largest known work is 2 161 (§1.5), ~2300× headroom |

All values live in the manifest / configuration, never hardcoded (requirements §6).

#### Why `max_work` is mandatory (**a direct consequence of D-10 choosing Python**)

`max_path_length` and `max_total_relator_length` are each reasonable in isolation, but their **product** is
the worst case: each step's multiplication/conjugation + free reduction costs $O(|r_0|+|r_1|)$,
and $10^5 \text{ steps} \times 10^4 \text{ chars} = 10^9$ character operations.
CPython takes **well over ten minutes** to run that — a single carefully crafted legal path can pin down a worker.

So the limits cannot just cap "step count" and "length" separately; a cumulative work budget must be added:

$$\text{work} \;=\; \sum_{k=0}^{|\text{path}|}\bigl(|r_0^{(k)}| + |r_1^{(k)}|\bigr)
\;\le\; \texttt{max\_work}$$

**[Verified]** work across the 424 known paths: min 43 / median 229 / max 2 161.
Choosing `max_work = 5_000_000` satisfies both ends: it leaves three orders of magnitude of headroom for real paths,
while nailing the worst case down to a few seconds of CPython.

**[D-11] needs confirmation**: the value `max_work = 5_000_000`.
If it is relaxed later (say someone genuinely needs million-step paths), worker timeouts and queue capacity must be re-evaluated in tandem.

Companion requirement: the verifier must execute in a **separate process** with a hard timeout (30 s recommended);
a timeout is handled as `E_WORK_BUDGET` and logged as an alert — timeouts must never be swallowed, nor treated as any state other than "verification failed".

### 4.4 Bridge certificate submission (`POST /bridge-submissions`)

```json
{ "from_challenge_id": "ms-v1-0001", "to_challenge_id": "ms-v1-0042",
  "moves": [ … ] }
```

The server determines the move-spec version from the official challenges.
The verification logic is identical to §4.2, except the endpoint becomes `to_challenge.initial_relators` (exact ordered).
Effects:

* A `verified AC bridge` entry is registered in both challenges' `GET /challenges/:id` responses
  (public fields: length, team, time, hash; the move sequence is **not** public during the competition).
* **Scoring is unchanged** (v1). Whether to merge in some scoring epoch is carried out by the organizers per announcement.
* The bridge enters the `GET /discoveries` timeline.

**[D-5]** Do bridges score? Recommendation: v1 awards **no points** — honor and registration only —
to avoid introducing a new scoring unit after the freeze.

### 4.5 Downloadable reference verifier

**[D-10 Decided: Python as the single source of truth.]** No Rust, no WASM, no Pyodide.

The deliverable is a pure Python package (no third-party dependencies, standard library only), providing both a library interface and a CLI:

```
acms-verify --manifest acms-ms-v1-manifest.json --submission mine.json
```

It **uses the exact same `competition/tools/verifier/acms_verify` source** as the server — not a port.
Golden vectors (§9) ship with the package; anyone can run them once to prove for themselves that it matches the official verifier.

The documentation must state clearly: **the reference verifier is only for contestants' self-checking; the server-side verifier is the sole basis for official results.**

**[D-10a Decided: no browser verifier.]** No JS, no WASM, no Pyodide.
Contestants self-check exclusively with the downloadable Python package above.

Rationale: any second implementation pays a long-term consistency cost — JSON number types (`1.0` is a float in Python and gets rejected,
while in JS `1.0` is just the integer `1`), canonical serialization and character escaping for `certificate_hash`
(Python's `json.dumps` defaults to `ensure_ascii=True`; `JSON.stringify` does not escape non-ASCII),
and sync/async API differences for SHA-256. The competition needs exactly **one** authoritative verifier.

**The two trust bases are mutually independent**: regular track = this section's Python verifier; counterexample track = Lean (§7).
They share no code and do not depend on each other — deliberately.

---

## 5. Scoring Engine

### 5.1 Definitions

For challenge $i$:

* $V_i$ = the manifest's `base_score`
* $L_{t,i}$ = the **minimum atomic path length over all accepted submissions** by team $t$ on challenge $i$
* $L_i^\star = \min_t L_{t,i}$
* $k_i = \#\{t : L_{t,i} = L_i^\star\}$

$$P_{t,i}=\begin{cases} V_i\,2^{1-k_i}, & L_{t,i}=L_i^\star\\ 0,&\text{otherwise}\end{cases}
\qquad P_t=\sum_i P_{t,i}$$

$k_i=1,2,3,4 \Rightarrow V_i,\ V_i/2,\ V_i/4,\ V_i/8$.

### 5.2 Recomputation Algorithm

The leaderboard is **derived as a pure function of the best-results table**, with no incremental patching:

```
best[(team, challenge)] = min(length over accepted solutions)   -- the only mutable state
recompute():
  for each scored challenge i:
     Lstar = min(best[*, i]);  k = count(best[t,i] == Lstar)
     for t: P[t,i] = (best[t,i] == Lstar) ? V_i / 2^(k-1) : 0
  P[t] = sum_i P[t,i];  rank by P desc, then by earliest time-of-current-total
```

Every accepted submission triggers one full recomputation (the v1 pool as scoped here was ~766 challenges;
**update 2026-09-03**: the actual scored pool is **10 115** challenges, so a full recomputation is ~10⁴ challenges × ~10² teams —
still ~10⁶ cheap operations, negligible, and the "no incremental patching" rule stands unchanged).
Every recomputation writes a `scoring_run` record (including `manifest_hash`, `verifier_version`, and timestamp),
aligned with IGP24's `scoring-history`, guaranteeing that any historical leaderboard can be reproduced.

### 5.3 First Solver Is Immutable

```
first_solver[i] = argmin over accepted solutions of (received_at, submission_id)
```

`submission_id` is monotonically increasing and breaks ties within the same millisecond. Once written, it is **never changed by later, shorter paths**
(acceptance §16.9). It is displayed as a permanent honor, explicitly annotated as "not guaranteed to keep earning points for this challenge."

### 5.4 No Organizer Baseline

IGP24 treated LMFDB as a baseline team (so a single team unlocking a baseline pair earned only 0.5 points).
ACMS v1 **introduces no baseline team**: the 550 entries in the challenge pool have no known paths to begin with,
so there is no public number that could serve as a lower bound for $L^\star$, and forcing one in would be unverifiable.
Consequence: the first (and sole shortest) solution to any challenge earns the full score $V_i$. This is deliberate, and better matches
the principle of "rewarding machine-verifiable results." **[D-6 Decided: none.]**

### 5.5 Exact Arithmetic

$P_{t,i} = V_i/2^{k_i-1}$ is an exact binary rational. **It must be stored as an exact rational or fixed-point value**
(Postgres `NUMERIC`, Python `Fraction`, Rust `num-rational`);
float accumulation is forbidden, or different machines / different summation orders would produce different totals,
violating the "identical results" clause of acceptance §16.5. For display, uniformly round-half-even to 4 decimal places.

### 5.6 Scoring Worked Example (goes into the rules text, and serves as a test fixture for the scoring engine)

$V_i = 1$ (the v1 value), four teams on the same challenge:

| Stage | A | B | C | D | $L^\star$ | $k$ | Score |
|---|---:|---:|---:|---:|---:|---:|---|
| ① A first-solves in 40 moves | 40 | – | – | – | 40 | 1 | A=1 |
| ② B also reaches 40 moves | 40 | 40 | – | – | 40 | 2 | A=B=1/2 |
| ③ C reaches 40 moves | 40 | 40 | 40 | – | 40 | 3 | 1/4 each |
| ④ D reaches **38 moves** | 40 | 40 | 40 | 38 | 38 | 1 | **D=1; A/B/C all drop to 0** |
| ⑤ A matches at 38 moves | 38 | 40 | 40 | 38 | 38 | 2 | A=D=1/2, B/C=0 |

Throughout, `First Solver = A` never changes.

> This rule is harsh: between ③→④, three teams are zeroed out in a single step. This is the literal requirement of requirements §8,
> and it also maximizes the incentive to "keep optimizing."
>
> **Corresponding backend obligation**: `GET /leaderboard` and `GET /challenges/:id` must return
> `k_teams`, `current_best_length`, and the requester's own `my_best_length`,
> so the frontend can compute "how many moves away am I from being zeroed out." The backend only guarantees the fields are complete; presentation is not our concern.

---

## 6. Path Confidentiality and Teams

### 6.1 Public Surface During the Competition

For each challenge, **public**: `status`, `current_best_length`, `current_best_solver` (team name),
`first_solver`, `first_solved_at`, `k_teams`, `V_i`, `certificate_hash`,
`peak_total_relator_length` (not scored), and the verified bridge list.

For each challenge, **not public**: any move sequence, any intermediate state, any path statistics other than length.

Teams can only see their own submissions (`GET /submissions/me`, with full moves downloadable).

Purpose of `certificate_hash`: it lets a team publicly announce a result without leaking the path
(cite the hash in a paper/preprint; publishing the path after the competition then self-certifies the claim).

### 6.2 Post-Competition Disclosure

After the competition ends, or after a phase end announced by the organizers, all valid certificates (including moves) become publicly downloadable,
forming a new public benchmark. This must be written into the Overview, because it is the long-term reason for contestants to participate.

### 6.3 Team Rules (carried over from IGP24 wording)

One person, one team; team size is unlimited; members may be added during the competition (subject to organizer approval);
**teams may not merge once either party has submitted**; discovery of coordinated cheating (including sockpuppets) disqualifies all involved teams.

Sharing a specific certificate for a challenge across teams counts as joint-team collaboration and may not be resubmitted as multiple independent teams
— this cannot be fully detected in the implementation, but it must be written into the rules, and the organizers reserve the right to request provenance.

---

## 7. Lean Counterexample Track

> ### Update 2026-09-03 — planned official channel: PDF + expert review; Lean is an optional fast track
>
> This section was written on the assumption that a Lean package is the *only* admissible
> counterexample artifact. That assumption did not survive O-3: `ac_iff_atomic` (§7.2) is
> **still unproven**, so the competition cannot require a Lean proof and must not advertise the
> frozen library as delivered. The shipped design is:
>
> * **Planned official channel after submissions open**: a self-contained mathematical
>   argument uploaded as a single PDF. The intended `POST /counterexample-submissions`
>   contract accepts `application/pdf`, **≤ 25 MB**, one file; no channel is open in prelaunch.
>   States: `received → screening → under_review → accepted | rejected | revision_requested`.
>   Review by the organizer panel plus reviewers they designate (see O-6); no guaranteed
>   turnaround; organizers may summarily decline submissions with no substantive new
>   mathematical content; **at most one active claim per team**, a new upload replacing the
>   pending one (its receipt time is the one that counts).
> * **Lean fast track (optional)**: a claim accompanied by — or later formalized as — a
>   machine-checked Lean 4 proof in the frozen environment skips expert review and, on passing
>   the CI gates of §7.5, settles the claim. Everything in §7.2–§7.6 remains the specification
>   of that track, stated in advance; none of it is available yet, and the contestant-facing
>   docs describe the library in the future tense only.
> * §7.4 (what is not a counterexample) and §7.7 (Highest Mathematical Achievement, no
>   leaderboard points) are unchanged and apply to both routes.
>
> Normative text: `competition/rules/evaluation.md` §9.

### 7.1 Submission Artifact

A standalone Lean package (tar.gz or git bundle) that must pass `lake build`
**without network access** in the frozen container and prove three theorems.

### 7.2 Definitions and Bridge Theorems the Competition Library Must Provide

```lean
namespace StandardAC

abbrev Letter := Int                 -- ±1 = x^{±1}, ±2 = y^{±1}
abbrev Word   := List Letter
structure Pres where (r0 r1 : Word)

/-- The full, unbounded, non-stable Andrews–Curtis one-step relation. -/
inductive Step : Pres → Pres → Prop
  | inv  (i : Fin 2)                     : …          -- r_i ← r_i⁻¹
  | mul  (i j : Fin 2) (h : i ≠ j) (ε : Bool) : …      -- r_i ← r_i r_j^{±1}
  | conj (i : Fin 2) (g : Word)          : …          -- r_i ← g r_i g⁻¹, g arbitrary

def Reachable : Pres → Pres → Prop := Relation.ReflTransGen Step
def trivialPresentation : Pres := ⟨[1], [2]⟩
def Pres.PresentsTrivialGroup (P : Pres) : Prop := …

end StandardAC

namespace Competition
/-- The 14 atomic moves of ac-r2-v1. -/
def atomicStep (m : Fin 14) : Pres → Pres := …
inductive AtomicRel : Pres → Pres → Prop | step (m) : AtomicRel P (atomicStep m P)

/-- The compatibility theorem required by requirements §10: the two reflexive-transitive closures are equal. -/
theorem ac_iff_atomic (P Q : Pres) :
    StandardAC.Reachable P Q ↔ Relation.ReflTransGen AtomicRel P Q := …

def instance (id : String) : Pres := …   -- generated from the manifest, annotated with instance_hash
end Competition
```

The `←` direction of `ac_iff_atomic` rests on the soundness of §1.4; the `→` direction requires
arbitrary-conjugator decomposition, derived left multiplication, and **derived relator swap**
(§1.4 point 3, already numerically verified to be feasible).
**This is the credibility linchpin of the entire counterexample track**: without it, a proof of
"no atomic path" is merely a statement about the competition metric, not an AC counterexample.

### 7.3 The Three Theorems Contestants Must Prove

```lean
theorem candidate_matches_manifest :
    P = Competition.instance challenge_id
theorem candidate_presents_trivial_group :
    P.PresentsTrivialGroup
theorem candidate_not_ac_reachable :
    ¬ StandardAC.Reachable P StandardAC.trivialPresentation
```

### 7.4 What Explicitly Does **Not** Constitute a Counterexample (Written into the Rules Verbatim)

* No path found within a fixed compute budget
* No path of length ≤ $N$ exists
* No path with peak length ≤ $B$ exists
* Unreachable in the substitution graph or any restricted move set
* Unreachable in the sense of stable AC (which allows adding/removing trivial relators)

### 7.5 Frozen Environment and Prohibited Items

Freeze and publish the hashes of: the Lean version, `lean-toolchain`, the Mathlib commit,
the competition formalization commit, `lake-manifest.json`, and the container image digest.

Prohibited: `sorry` / `admit` / `sorryAx` / adding unapproved `axiom`s / `unsafe` /
FFI or external programs as proof oracles / modifying the frozen competition definitions.

Automated gates (CI, all fail-closed):

1. `lake build` in a clean, network-free container
2. Run `#print axioms` on the three theorems; the whitelist is **only** `propext`, `Classical.choice`, `Quot.sound`
3. Source scan for `sorry|admit|sorryAx|unsafe|native_decide|@[implemented_by]`
4. Compare SHA-256 hashes against the frozen definition files; any change means rejection
5. Repeat 1–2 on **a separate, independent machine**

### 7.6 State Machine

```
received → ci_running → ci_passed  ──►  Provisional Counterexample
                     └→ ci_failed  ──►  Rejected (with full logs)
Provisional ──► (Lean expert reviews the trust boundary + math expert confirms the statement
                 matches the standard AC conjecture + source made public for community review) ──► Verified Counterexample
```

"First" is determined by **the time the server receives the complete Lean package**, but it only takes effect after passing all reviews.
Subsequent independent proofs are marked `Independent Confirmation`.

### 7.7 Highest Mathematical Achievement

The first counterexample to pass full verification is marked
**Highest Mathematical Achievement of the Competition**,
displayed in a standalone banner **above** the regular leaderboard, containing: team name, challenge,
Lean proof link, submission time, verification status, and the independent review report.
It is not converted into $V_i$ and does not count toward the regular leaderboard total.

---

## 8. API

Unified prefix `/api/acms`. All endpoints share the same verifier / team / rate-limit / scoring stack with the website.

| Method | Path | Auth | Returns |
|---|---|---|---|
| GET | `/challenges` | None | public view of the manifest + `manifest_hash`/`move_spec_hash` |
| GET | `/challenges/:id` | None | public view of a single challenge (§6.1 whitelisted fields) |
| GET | `/leaderboard` | None | rankings, total scores, solved count per team, `scoring_run_id` |
| GET | `/scoring-history` | None | all past `scoring_run`s |
| GET | `/discoveries` | None | timeline of first solves, best-length updates, verified bridges |
| GET | `/submissions/me` | Required | **own team only**, includes full moves |
| POST | `/submissions` | Required | per-item verdict + the team's updated score |
| POST | `/bridge-submissions` | Required | bridge verdict |
| POST | `/counterexample-submissions` | Required | planned after submissions open: PDF claim receipt + state (`application/pdf`, ≤ 25 MB, one active claim per team); the optional Lean route is not available yet |
| GET | `/counterexample-submissions/me` | Required | own team's counterexample claims, their states, and (fast track only) CI logs |

The public response of `GET /challenges/:id` (**this is the privacy contract**, enforced by schema rather than comments —
acceptance §16.10):

```jsonc
{
  "challenge_id": "ms-v1-0001",
  "family": "miller-schupp", "n": 3, "w": "x^{-1}y^{-1}xy^{-1}",
  "initial_relators": [[…],[…]], "target_relators": [[1],[2]],
  "move_spec_version": "ac-r2-v1", "instance_hash": "sha256:…",
  "status_at_freeze": "open", "base_score": 1, "scored": true,
  "current_best_length": 42,
  "current_best_solver": "Team Foo",
  "current_best_certificate_hash": "sha256:…",
  "current_best_peak_total_relator_length": 31,     // not scored
  "k_teams": 2,
  "first_solver": "Team Bar", "first_solved_at": "2026-09-14T…Z",
  "first_certificate_hash": "sha256:…",
  "bridges": [ { "to": "ms-v1-0042", "length": 61, "team": "Team Foo", "hash": "sha256:…" } ],
  "source": { … },
  "freeze_date": null
}
```

The serializer uses an **explicit whitelist**, plus one test: a fully recursive
string search over the public response of any challenge must never surface any `moves` array (acceptance §16.10).

Additionally provide `/competitions/acms.md` (the full rules as a single file) and an `/llms.txt` entry, consistent with IGP24.

---

## 9. Public release package `ACMS-public`

Benchmarked against `github.com/SAIRcompetition/IGP24-public` (its complete structure has been verified hands-on).

### 9.1 Core principle: public package ≠ production code

The IGP24-public README states this explicitly:

> The public reference tools are intentionally small. The official competition system
> runs the production evaluator, while this repository exposes the core mathematical
> checks used for reproducibility.

ACMS adopts this boundary: **the public package contains data, rules text, and the reproducible core mathematical checks;
the submission service, scoring engine, leaderboard, authentication, and rate limiting all stay in the internal system.**
The planned competition service will use the same
`competition/tools/verifier/acms_verify` sources as the public package.
The current export is a prelaunch preview; it contains no production
scheduling, storage, or scoring, and does not establish that a service is live.

### 9.2 Directory structure

```
ACMS-public/
  README.md                              # what it is, organizers, background, layout, Start Here
  LICENSE                                # Apache-2.0 (same as IGP24-public)
  NOTICE                                 # attribution (Apache-2.0 §4d): dataset + status sources
  competition/
    README.md                            # submission format, reference tools, internal-system boundary
    competition.yaml                     # machine-readable metadata (§9.4)
    rules/
      overview.md                        # contestant-facing
      evaluation.md                      # technical
      prelaunch.md                       # prelaunch preview page; no countdown while dates are null
    challenges/
      README.md                          # exact semantics of every column of every file + freeze date
      manifest.json                      # 10,115-instance pool + hashes; official freeze pending
      move_spec.json                     # machine-readable definition of the 14 moves of ac-r2-v1
      ms1190_metadata.csv                # full MS-1190 set, 1190 entries (the challenge pool's "universe")
      training_424.json                  # 424 paths already converted to ac-r2-v1
      golden_vectors.json                # conformance vectors (passing + each error code)
    examples/
      README.md                          # commands, successful receipt, separate failure example
      sample_submission.json             # successful unscored training solution
      training_manifest.json             # separate example manifest, outside scored pool
      sample_verdict.json                # expected complete successful receipt
      invalid_submission.json            # deliberate E_NOT_TARGET example
    tools/
      verifier/                          # Python reference verifier (library + CLI, standard library only)
        README.md
        acms_verify/
      lean/                              # optional Lean route description; not open
        README.md
```

### 9.3 Item-by-item comparison with IGP24-public

| IGP24-public | ACMS-public | Notes |
|---|---|---|
| `rules/overview.md` + `rules/evaluation.md` | Same names | Full rules for the planned competition; `prelaunch.md` separately describes the current preview |
| `competition.yaml` | Same name | Machine-readable metadata, see §9.4 |
| `baseline/lmfdb_baseline.csv` | `challenges/manifest.json` | Data defining the scoring task; ACC's official freeze is pending |
| `baseline/valid_pairs.csv` (full set of 165 836 pairs) | `challenges/ms1190_metadata.csv` (full MS set of 1190 entries) | Reference context for the MS family; ACC's current scored pool has 10,115 instances |
| `examples/sample_submission.txt` | `examples/sample_submission.json` plus `training_manifest.json` and `sample_verdict.json` | Runnable successful local example; unscored and separate from the competition manifest |
| `tools/magma/t24.m` (requires a commercial CAS) | `tools/verifier/` (self-contained Python) | **We are stronger here**: IGP24's core verification requires Magma; the ACMS verifier is pure standard library — anyone can run it |
| `tools/number_field_discriminant/` (PARI/GP) | `tools/lean/` | IGP24 supplies discriminant tools; ACC's optional Lean route is only a plan and is not open |
| `baseline/README.md` records `LMFDB baseline snapshot: 2026-05-20` | `challenges/README.md` records `freeze_date` | The freeze date must live next to the data, not only in the rules |

Before an official release, the organizers must approve the schedule and
freeze date, regenerate metadata from `build/competition_state.json`, and
freeze `manifest.json` and `move_spec.json` in git. Record that commit as
`freeze_commit` in the maintained state, then run
`python3 build/build_manifest_v2.py` again to synchronize YAML before
running the release command.
The default `python3 build/release.py` must fail if required metadata is
missing or the declared git freeze cannot be verified. For local review,
`python3 build/release.py --preview` writes `dist/ACMS-public` with a
prominent prelaunch/preview notice and no claim of an official release.

### 9.4 `competition.yaml`

```yaml
id: acms
name: "ACC: The Andrews–Curtis Conjecture Competition"
status: prelaunch
task_type: mathematical_discovery
submission_artifact: submission.json
submission_format: "JSON; solutions[] of {challenge_id, moves[]} where moves are atomic AC move ids 0-13"
verifier: "Python, competition/tools/verifier (standard library only)"
counterexample_verifier: "Planned after submissions open: PDF + expert review; optional Lean route not open"
primary_metric: leaderboard_score
scoring_unit: team_challenge
scoring_formula: "V_i * 2^(1-k_i) for teams at the current shortest length, 0 otherwise"
move_spec_version: ac-r2-v1
move_spec_hash: "sha256:…"
manifest_hash: "sha256:…"
freeze_date: null
freeze_commit: null
registration_opens: null
submissions_open: null
submission_deadline: null
certificate_release: null
challenge_count: 10115
challenge_policy: "10,115-instance competition pool; official freeze pending; training examples are not scored"
overview: rules/overview.md
evaluation: rules/evaluation.md
manifest: challenges/manifest.json
move_spec: challenges/move_spec.json
```

The generated file keeps `id: acms` and the existing code identifiers.
Maintain status, freeze information, and all four schedule fields in
`build/competition_state.json`; do not hand-edit generated YAML or manifest dates.

### 9.5 Content split for `rules/`

There are three files. `prelaunch.md` describes the current prelaunch
preview, including locally usable rules, data, and tools. A future site
may render it separately; no countdown should be shown while dates are
`null`. The planned full-rules document combines `overview.md` and
`evaluation.md`, not `prelaunch.md`.

| File | Contents | Maps to this document |
|---|---|---|
| `overview.md` | Mathematical background, Miller–Schupp, the task, the 14-move table, submission format, scoring (including the §5.6 worked example), summary of the Lean counterexample track, integrity and team rules, timeline, the three final wordings from §13 | §1, §2, §4.1, §5, §6.3, §7.1/7.3/7.4, §13 |
| `evaluation.md` | Parsing rules, full error-code table, step-by-step verifier semantics, limits and work budget, hash templates, scoring recomputation algorithm, First Solver ordering, confidentiality whitelist, Lean frozen environment and axiom audit | §3, §4.2–4.4, §5.2–5.5, §6.1, §7.2, §7.5, §7.6, §8 |

This document (`DESIGN.md`) is an **internal design document and does not go into the public package**.

---

## 10. Repository structure and milestones

### 10.1 Structure

**[D-0 landed]** Repository root = `caltech/Andrews–Curtis/`.
`reference/index.html` has been copied over from `lean-competition/andrews-curtis-competition/`,
its SHA-256 check passed (`bc84ec5a90842e7cadd8c2be63631699f5181e6b1e16d0e90a7ef927a6b72fdf`),
and the empty `prototype/` has been deleted.

**One repository; the public tree lives inside it, in place** (revised
2026-08-06: the IGP24-public-shaped tree is kept at `competition/` as
the single source of truth, so rules, frozen data, and the verifier
never exist in two copies):

```
Andrews–Curtis/                    # ← development repository (private), repository root
  README.md   development-repo guide (the public root README is written at export)
  LICENSE     Apache-2.0 (exported verbatim)
  competition/                     # ← THE public tree, IGP24-public-aligned (§9.2)
    competition.yaml               generated by build_manifest_v2.py (hashes and release metadata)
    rules/       overview.md, evaluation.md, prelaunch.md   ← source of truth
    challenges/  manifest.json, move_spec.json, ms1190_metadata.csv,
                 training_424.json, golden_vectors.json, README.md
    examples/    sample_submission.json, training_manifest.json, sample_verdict.json,
                 invalid_submission.json, README.md
    tools/verifier/  acms_verify/ (Python, the only implementation) + README.md
    tools/lean/      README.md (frozen formalization published at P4)
  spec/       DESIGN.md (this document, internal, not in the public package)
              (the IGP24 rules text used for comparison is no longer vendored here;
               read it at https://competition.sair.foundation/competitions/igp24.md)
  build/      build_manifest.py (regenerates challenges/ + competition.yaml;
              2026-09-03: demoted to a library, driven by sync_dataset.py + build_manifest_v2.py)
              competition_state.json (maintained status, freeze, schedule)
              release.py (gates official releases; --preview exports a marked preview)
              checks/ acheck.py bridge.py convert.py demo.py
  tests/      verifier + frozen-data acceptance tests (internal, not shipped)
  server/     scoring/ (P2); api/, storage/, privacy/ pending O-1   ← not in the public package
  lean/       Competition/ (O-3 spike → frozen definitions at P4)
  reference/  index.html (prototype; must not be modified and must not be depended on by production code)
```

**No `web/`** — the frontend is out of scope for this document (§0.1).

`ACMS-public` (§9.2) is **not maintained by hand**; `build/release.py`
exports it from the in-repo `competition/` tree. `--preview` is the
development path and writes `dist/ACMS-public`; the default invocation
is the official release gate. It rejects incomplete schedule/freeze
metadata or an unverified git freeze before producing an official package.
Both modes verify the package, and preview mode labels its root README
prominently as prelaunch/preview:

1. Recompute all three hashes from the frozen data and assert
   `competition.yaml` quotes the same values
2. Copy `LICENSE`, `NOTICE`, and `competition/` to the output directory and
   write the public root README
3. **Run the golden vectors and the hash check from the copied
   package** in an isolated environment; also verify the successful
   training example and its expected receipt; abort if checks fail
4. Assert the package contains exactly `{README.md, LICENSE, NOTICE,
   competition/}` and no file from `server/` (prevents accidental
   leakage of scoring/auth logic)

### 10.2 Milestones (aligned with requirements §17)

| Phase | Deliverables | Completion criteria |
|---|---|---|
| **P1** (local preview) | Mathematical definitions + move spec; 10,115-entry manifest + generator + hashes; deterministic Python verifier + unit tests | Acceptance §11 items 1–5 and 11 all green; golden vectors and successful training example available; official data freeze remains separate |
| **P2** | Submission service, scoring engine, leaderboard computation, certificate privacy | Acceptance 6–10 all green |
| **P3** | Public API (§8), the `ACMS-public` release package (§9), `overview.md` + `evaluation.md` | End to end: authentication → submission → leaderboard recomputation → API response; public-field whitelist tests pass; an external party can independently run the golden vectors against the `release.py` artifacts |
| **P4** | Lean AC formalization (including `ac_iff_atomic`), counterexample pipeline, axiom audit | Acceptance 12–13 all green; the template project builds offline |

The frontend (pages, components, interactions) is handled by a separate track and depends on the P3 API contract.

---

## 11. Acceptance Test Matrix

The 13 items of requirements §16, each mapped to an executable test:

| # | Requirement | Test | Layer |
|---:|---|---|---|
| 1 | Correct certificates are accepted | All 424 training paths (remapped + canonicalized to the exact $T$) accept; length/peak/work match the §1.5 table item by item | verifier |
| 2 | Invalid move IDs are rejected | `-1, 14, 1.5, "3", null` → `E_BAD_MOVE_ID` with index | verifier |
| 2b | Work budget takes effect | Construct a legal path whose work exceeds `max_work` → `E_WORK_BUDGET`, returned within 30 s | verifier |
| 3 | Every move legal but target not reached | Take a genuine path truncated by 1 move; also construct a path that stops at $(y,x)$ → `E_NOT_TARGET` | verifier |
| 4 | Corrupted/truncated certificate | Truncated JSON, missing `moves`, `moves` not an array → `E_MALFORMED` | verifier |
| 5 | Same result across machines | Golden vectors agree field by field on linux/mac × CPython 3.11/3.12 (including `certificate_hash`) | CI |
| 6 | A team's shorter path replaces its old one | Submit 40 → 38, `best` becomes 38; then submit 45, `best` stays 38 | scoring |
| 7 | Rescore after a new global shortest appears | Assert the 5-stage worked example of §5.6 frame by frame | scoring |
| 8 | Scoring correct for $k=1,2,3,4$ | Assert $V,\ V/2,\ V/4,\ V/8$, compared exactly with `Fraction`; **includes one non-uniform $V_i$ fixture (`1,7,100`)** | scoring |
| 9 | First Solver unchanged | After running the full §5.6 flow, `first_solver == A` | scoring |
| 10 | API does not leak other teams' paths | As team B, recursively scan `/challenges`, `/challenges/:id`, `/leaderboard`, `/discoveries` and assert no `moves`; `/submissions/me` returns only the requesting team | api |
| 11 | manifest/move spec change ⟹ hash mismatch | Change one relator / one move → `instance_hash`/`move_spec_hash` changes; replay and certificate hashing derive the version from the official challenge | data |
| 12 | Lean template builds offline | `docker run --network=none … lake build` exits with code 0 | lean |
| 13 | Submissions containing `sorry`/new axioms are rejected | Three fixtures: `sorry`, `axiom foo : False`, `native_decide` → all reject | lean |
| 14 | Release package does not leak internal logic | Assert the `release.py` output contains no `server/` files and no auth/scoring source code; the three hashes in `competition.yaml` match the actual manifest values | release |
| 15 | Release package runs standalone | In a clean container, unpack only `ACMS-public`; after installation the golden vectors run all green (no dependency on the development repo) | release |

**Verification scripts already run** (placed in `build/checks/`, runnable directly with `python3`):

| Script | What it verifies |
|---|---|
| `acheck.py` | Replays the 424 paths under the 12-move semantics; exact-target canonicalization cost table (§1.2); MS-1190 three-tier statistics (§2.1) |
| `bridge.py` | Derivability of relator swap (§1.4); bounded bridge search within the same reported class (§2.3); `cls` prefix vs actual length |
| `convert.py` | End-to-end regression of the training-set conversion recipe: 424/424 land on the exact $(x,y)$ (§1.5) |

These three scripts upgrade directly into P1 regression tests (seeds for acceptance items 1, 5, and 11).

**Update 2026-09-03**: that upgrade has happened — `build/checks/*` is superseded by the `tests/` suite and is kept only as the historical record of the [Verified] figures above.

---

## 12. Decision List

### 12.1 Decided (all landed in this document)

| # | Decision | Conclusion |
|---|---|---|
| — | Development scope | **Backend only**; P1 first |
| **D-0** | Repository root | `caltech/Andrews–Curtis/` ✅ landed |
| **D-2** | $r_1$ convention | **$x w^{-1}$** (the prototype convention) ⚠️ requirements §2 erratum pending |
| **D-3** | Challenge pool scope | 550 open challenges; the 216 uncertified ones are excluded |
| **D-4** | $V_i$ damping by class | No damping |
| **D-5** | Scoring for bridge certificates | **No score**; only recorded in `/challenges/:id` and `/discoveries` |
| **D-6** | Organizer baseline | None |
| **D-8** | `base_score` | All = 1, adjusted manually later |
| **D-10** | Verifier language | **Python as the sole implementation** |
| **D-10a** | Browser verifier | **Not built** (no JS / WASM / Pyodide); rationale in §4.5 |
| **D-11** | `max_work` | **5 000 000** (§4.3) |
| **D-1 / D-7** | Tab layout / UI hints | Moved out of this document (frontend matters) |
| — | Public release package | Build `ACMS-public` following the `IGP24-public` structure; three rule files; `release.py --preview` for development, default `release.py` for an official release after metadata and git-freeze checks (§9, §10.1) |

### 12.2 Only one item still pending

| # | Decision | Blocks | Notes |
|---|---|---|---|
| **D-9** | Official freeze and competition schedule | Formal release (does not block local previews) | Maintain `freeze_date`, `freeze_commit`, `registration_opens`, `submissions_open`, `submission_deadline`, and `certificate_release` in `build/competition_state.json`; all are currently `null`. The generator synchronizes manifest/YAML metadata. `freeze_date` remains outside `instance_hash`; default release fails until metadata and git freeze are valid |

### 12.3 Pending revisions to the requirements document

| Location | Current state | Should read |
|---|---|---|
| requirements §2 | $MS(n,w)=\langle x,y \mid x^{-1}y^nxy^{-(n+1)},\ x^{-1}w\rangle$ | $MS(n,w)=\langle x,y \mid x^{-1}y^nxy^{-(n+1)},\ x w^{-1}\rangle$ |
| requirements §6 | No mention of work budget | Add "the cumulative work limit must be configurable" (alongside the existing "path and intermediate relator length limits must be configurable") |

---

## 13. Three statements that will be scrutinized repeatedly (wording finalized — do not change)

1. **Meaning of Unresolved**
   > "Unresolved" means only: as of the data freeze date, no publicly available
   > valid trivialization certificate is known. It does **not** mean the instance
   > is a counterexample, and it does **not** mean the instance is unsolvable.

2. **Meaning of shortest path**
   > Current best-known atomic path — the shortest path among valid competition
   > submissions to date. This is **not** a mathematically proven shortest path.

3. **Meaning of counterexample**
   > A verified counterexample is a Lean proof, checked in the frozen environment
   > with an audited axiom set, that the presentation presents the trivial group
   > and is **not** related to the trivial presentation by the full, unbounded,
   > non-stable Andrews–Curtis relation. Failure to find a path — under any
   > budget, length bound, peak bound, or restricted move set — is not a counterexample.

**Update 2026-09-03**: statements 1 and 2 ship verbatim in substance. Statement 3's *second* sentence
(failure to find a path is not a counterexample) is unchanged and normative; its *first* sentence is
narrowed to the optional Lean fast track, because the official channel is now PDF + expert review
(§7 update note). The shipped wording defines a disproof by its mathematical content — an argument that
the presentation is not related to the trivial presentation by the full, unbounded, non-stable AC
relation — rather than by the artifact that carries it.

---

## 14. Open Questions and Risks

Ordered by impact. **O-1 changes the scope of P2 work and needs to be clarified as early as possible.**

### O-1 Is ACMS hosted inside the SAIR platform, or do we build our own? (**a scoping question**)

The IGP24-public README states explicitly:

> The production submission validator and leaderboard system run inside the
> SAIR competition system.

Meanwhile, the SAIR platform already provides complete facilities such as `/api/auth/*`, `/api/users/me`, teams and invitations (`/:stage/invitations/:token`), `/api/igp24/leaderboard`, and `/api/igp24/scoring-history`.

If ACMS is likewise hosted on the SAIR platform, the following parts of this document **most likely do not need to be built by us**:

| Section of this document | If the platform already provides it |
|---|---|
| §4.3 submission quotas / rate limiting | Already on the platform (IGP24's 200/day is implemented at the platform layer) |
| §6.3 team rules, one team per person | Already on the platform |
| §8 authentication, `/submissions/me` ownership resolution | Already on the platform |

In that case our deliverables converge to: **manifest + verifier + scoring engine + confidentiality whitelist + Lean pipeline**, plus an internal interface for the platform to call. The P2 workload roughly halves.

**Needs confirmation**: does ACMS go through the SAIR platform? If so, we need the platform's competition integration spec (how submissions are delivered to the evaluator, how the evaluator returns verdicts and scores, and who computes the leaderboard).

### O-2 Empty-leaderboard risk, and a proposed warm-up track — **RESOLVED 2026-09-03**

> **Resolved by the pool change (§2 update note).** The 10 115-instance pool is graded from
> warm-up to research frontier, so its easy/medium mass guarantees leaderboard activity from
> day one and shortest-path competition on solvable instances throughout — which is exactly what
> the proposed warm-up track was for, without a second leaderboard or a second scoring unit.
> `training_424.json` stays published as **training data** (not a scored track): 424 solved
> MS-1190 instances with full atomic-move certificates, excluded from scoring.
> The analysis below is kept as the record of why the pool was widened.


IGP24's target space has 165 836 possible pairs and the baseline covers only 622 — low-hanging fruit everywhere, with points available from day one. ACMS's 550 challenges are the ones Shehper et al. and Fagan et al. **attacked with large-scale RL and search and failed to crack**. The realistic outcome may be: **the main leaderboard stays empty for the entire competition.**

This is not a technical defect (the first solver would achieve a major result), but it is a substantive risk for competition operations: without visible progress, community engagement drops.

**Proposal (zero cost, strongly recommended): add a non-scoring warm-up track — shortest-path challenges on the 424 already-solved challenges.**

* The data already exists: after conversion to `ac-r2-v1`, the 424 paths have a median of 26 moves and a maximum of 159 moves (§1.5); these are almost certainly not optimal, leaving plenty of room for optimization.
* It reuses the exact same verifier, the same submission format, and the same $L^\star$/$k_i$ scoring logic; it simply **does not count toward the main leaderboard total** and gets its own separate warm-up leaderboard.
* A side benefit is a free end-to-end test bed: before the main track goes live, warm-up will already have run the verifier, the submission service, scoring recomputation, and the confidentiality whitelist hot.
* No conflict with D-3 (the challenge pool contains only the 550 open challenges) — warm-up is not part of the challenge pool and is not scored.

**Needs confirmation**: whether to add this warm-up track.

### O-3 Lean `ac_iff_atomic` is the real technical risk in P4

The bridging theorem in §7.2 is the credibility linchpin of the entire counterexample track. Mathematically it is not hard (§1.4 verified that the relator swap is derivable), but in Lean it requires handling the formalization plumbing for free-group words, and `PresentsTrivialGroup` must be correctly defined on top of Mathlib's `PresentedGroup` — both may take more time than expected.

**Recommendation**: do not wait until P4 to start. Kick off a spike during P1/P2 and scaffold `Step` / `AtomicRel` / `ac_iff_atomic` first (with `sorry` allowed), confirming the route is viable and that Mathlib has the lemmas we need. If this theorem cannot be proved, the framing of the counterexample track must be downgraded wholesale — the earlier we know, the better.

### O-4 Two pending details of manifest generation

| Item | Problem | Recommendation |
|---|---|---|
| `challenge_id` numbering scheme | In what order are the 550 challenges numbered `ms-v1-0001…0550`? Once frozen the numbering cannot change, and **the numbering order leaks information** (sorting by difficulty or initial length amounts to a hint for contestants) | Number by the order in which $(n, w)$ appears in the original MS-1190 table: neutral, reproducible, and carrying no difficulty signal |
| Canonical form of `w` | The prototype uses TeX strings (`x^{-1}y^{-1}xy^{-1}`), which carry a `y^{2}` vs `yy` spelling ambiguity | Have the manifest and `ms1190_metadata.csv` provide both `w` (TeX string, human-readable) and `w_vector` (integer array, canonical); `instance_hash` covers only `initial_relators`, not `w`, so the spelling ambiguity does not affect correctness |

### O-5 The limits are mutually inconsistent (minor issue; the docs must state the priority order)

`max_path_length = 100 000` and "500 solutions per submission" cannot both be maxed out under the 4 MB body limit: one move id is about 3 bytes, 4 MB ≈ 1.4 million moves, and 500 solutions of 100 000 moves each would require 50 million moves.

Not a bug (the body limit takes effect first), but the error-code priority must be fixed in writing to avoid confusing contestants:

```
body byte limit  →  solutions count limit  →  max_path_length  →  max_total_relator_length  →  max_work
```

Whichever limit trips first is the one reported; `evaluation.md` lists them in this order.

### O-6 The people who review counterexamples (operational, not technical)

§7.6 requires "a Lean expert to audit the trust boundary + a mathematics expert to confirm the formal statement matches the standard AC conjecture." This needs **named people**, and they must be in place before the first `Provisional Counterexample` appears — otherwise the state machine stalls at Provisional and cannot advance.

IGP24 lists 5 co-organizers. ACMS needs a similar roster, with at least one Lean expert and one combinatorial group theory expert.

**Resolved 2026-09-03.** Co-organizers, in alphabetical order by surname: **Lucas Fagan, Sergei Gukov, Terence Tao**.
Counterexample review is carried out by that organizer panel together with reviewers they designate case by case;
under the PDF channel (§7 update note) the state machine no longer stalls waiting for a standing Lean auditor, since
`under_review` is a human-review state by construction and the Lean fast track's CI gates are automated.
The contestant-facing name of the competition is **ACC: The Andrews–Curtis Conjecture Competition**; internal code
identifiers (`acms_verify`, `manifest_version`, the `acms` slug) are unchanged.
