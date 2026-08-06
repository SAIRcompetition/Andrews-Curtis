<!-- Full rules for IGP24. Live page: https://competition.sair.foundation/competitions/igp24 — generated at build from docs/competitions/igp24/{overview,evaluation}.md -->

# IGP24: The Inverse Galois Problem in Degree 24

## Overview

IGP24 is an open mathematical discovery competition centered on the inverse
Galois problem over $\mathbb{Q}$, the field of rational numbers.

The [inverse Galois problem](https://en.wikipedia.org/wiki/Inverse_Galois_problem)
asks whether every finite group arises as the
[Galois group](https://en.wikipedia.org/wiki/Galois_group) of a
[number field](https://en.wikipedia.org/wiki/Algebraic_number_field).  A
concrete degree-by-degree version asks the following: for every positive
integer $d$ and every transitive
[permutation group](https://en.wikipedia.org/wiki/Permutation_group) $G$ on
$d$ letters, does there exist an
[irreducible polynomial](https://en.wikipedia.org/wiki/Irreducible_polynomial)
with integer coefficients whose Galois group is $G$?

For $d = 24$, this becomes a large explicit search problem.  There are 25,000
transitive permutation groups of degree 24, conventionally labelled `24T1`
through `24T25000`.  The goal of IGP24 is to find explicit irreducible integer
polynomials of degree 24 that realize as many of these groups, and as many of
their possible signatures, as possible.

## Co-organizers

IGP24 is co-organized by (in alphabetical order by surname):

- John Jones
- Jen Paulhus
- David Roe
- Andrew Sutherland
- Terence Tao

IGP24 is run in collaboration with the [LMFDB](https://www.lmfdb.org/).

[<img src="https://www.lmfdb.org/static/images/lmfdb-logo.png" alt="LMFDB logo" width="200">](https://www.lmfdb.org/)

## Mathematical Background

The inverse Galois problem is widely believed to have a positive answer: every
finite group should occur as a Galois group over $\mathbb{Q}$.  In the
degree-specific form used here, a submitted polynomial

$$
f(x) = a_0 + a_1 x + \cdots + a_{24}\, x^{24}
$$

defines a degree 24 number field when it is irreducible over $\mathbb{Q}$.
Its Galois group acts transitively on the 24 complex roots of $f$, and
[Magma](https://magma.maths.usyd.edu.au/magma/) identifies this transitive
group by a label `24Tt`.

The problem is known to be essentially solved in smaller degrees: realizations
are known for all transitive groups of degree $d \leq 22$, and for all but one
case in degree $d \leq 23$.  The remaining degree 23 case is the
[Mathieu group M23](https://en.wikipedia.org/wiki/Mathieu_group_M23), also
known as `23T5`, which appears as a FrontierMath
[inverse Galois open problem](https://epoch.ai/frontiermath/open-problems/inverse-galois).

Degree 24 is much less complete.  Existing tabulations either focus on smaller
degrees, such as the [Klüners-Malle database](http://galoisdb.math.uni-paderborn.de/home),
or contain only limited degree 24 coverage relative to the full set of 25,000
groups.  The [LMFDB](https://www.lmfdb.org/) provides public data and a
complete degree 24 group index at
[LMFDB Galois groups with n = 24](https://www.lmfdb.org/GaloisGroup/?n=24).
The frozen LMFDB-derived scoring baseline used by this repository covers 286
distinct `24Tt` labels and 622 distinct $(24\mathrm{T}t, r)$ pairs.

[Shafarevich's theorem on solvable Galois groups](https://en.wikipedia.org/wiki/Shafarevich%27s_theorem_on_solvable_Galois_groups)
implies that every finite
[solvable group](https://en.wikipedia.org/wiki/Solvable_group) occurs as a
Galois group over $\mathbb{Q}$.  This matters enormously in degree 24: 24,193
of the 25,000 transitive groups are solvable.  However, the theorem is not a
practical catalog of explicit small polynomials, and it does not by itself
give the kind of verified coefficient lists needed for this competition.

## Task

Participants submit integer polynomials of degree 24.  The official verifier
computes, for each valid polynomial:

- the `24Tt` Galois group label,
- $r$ = number of real roots.

The official scoring discriminant is computed separately by
[PARI/GP](https://pari.math.u-bordeaux.fr/).  For non-baseline pairs, it is
the exact number-field discriminant when that computation succeeds for the
whole pair, and otherwise the documented mixed discriminant described below.
For LMFDB baseline improvements, only a successfully computed exact `nfdisc`
can score.  The precise protocol is specified in [evaluation](evaluation.md).

The number $r$ is the number of real roots of the polynomial, equivalently the
number of real embeddings of the corresponding degree 24 field.  In degree 24,
$r$ must be an even number between $0$ and $24$, but not every value of $r$ is
possible for every group $G$; the allowed signatures depend on the group
structure.  Across all 25,000 degree 24 transitive groups, there are 165,836
possible $(24\mathrm{T}t, r)$ combinations.

A submission contributes to the leaderboard when it realizes a scoreable
`24Tt` label and signature pair $(24\mathrm{T}t, r)$.  Scoreable pairs include
new pairs outside the frozen LMFDB-derived baseline, and baseline pairs that
are unlocked by a strict discriminant improvement as described below.

## Scoring Update (June 18): LMFDB Baseline Improvements

The frozen LMFDB baseline is no longer only a hard exclusion.  A baseline
$(24\mathrm{T}t, r)$ pair can now be unlocked for scoring if a participant
finds a polynomial whose exact number-field discriminant is strictly smaller
than the best baseline discriminant for that pair.

For a baseline pair, let $D_{\mathrm{base}}$ be the smallest exact `nfdisc`
value recorded in the LMFDB baseline.  A participant scores on that pair only
if their exact `nfdisc` is successfully computed and satisfies
$D < D_{\mathrm{base}}$.  Mixed discriminants do not unlock LMFDB baseline
pairs.

When a baseline pair is unlocked, LMFDB is treated as one baseline team in the
scoring formula, and only participant teams beating $D_{\mathrm{base}}$ count
for that pair.

## Scoring Update (July 9): Mixed Discriminant Fallback

For non-baseline pairs, if exact `nfdisc` times out or fails for any considered
row in a pair, the whole pair is scored with the mixed discriminant fallback.
As of July 9, this mixed discriminant is computed by PARI/GP as
`nfdisc([f,100000])`.  This replaces the earlier product-form implementation.
The updated method makes mixed-discriminant computation simpler and more
efficient.  The output field names `mixed_disc_abs` and
`disc_source=mixed_disc` are unchanged for compatibility.

All leaderboard entries scored with mixed discriminants are computed and scored
using this updated algorithm, including entries submitted before this update.
As a result, scores for teams with mixed-discriminant entries may change
slightly when the leaderboard is recomputed.

This update does not change LMFDB baseline improvements: baseline pairs can
still be unlocked only by a successfully computed exact `nfdisc` satisfying
$D < D_{\mathrm{base}}$.

## Submission-Limit Update (July 31)

Effective **July 31, 2026 at 00:00 UTC**, each team may make at most **200
submissions per day**.  Each submission may contain at most **1,000
polynomials**, giving each team a maximum of **200,000 polynomials per day**.

## Timeline

- Competition opens: **June 16, 2026**
- Competition closes: **August 15, 2026**,
  [AoE](https://en.wikipedia.org/wiki/Anywhere_on_Earth) (Anywhere on Earth)

## Submission Format

The official submission artifact is a plain text file named `submission.txt`.

Each non-empty, non-comment line contains one polynomial as 25 comma-separated
integer coefficients in ascending powers of $x$, i.e. $a_0, a_1, \ldots, a_{24}$:

```text
a_0,a_1,...,a_24
```

Example from the LMFDB baseline, representing $x^{24} + 2$:

```text
2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
```

The official Magma verifier computes the Galois group label and signature.
Scoring discriminants are computed separately by the PARI/GP discriminant
workflow.

You may, however, annotate any line with a trailing `#` comment -- including
your own expected `(24Tt, r)` -- and you may add full-line `#` comments
anywhere.  All comments are ignored by the verifier and never affect scoring.

### Monic polynomials (required)

Submissions must be monic: every coefficient line must have $a_{24} = 1$ (and
$a_0 \neq 0$). Non-monic polynomials are rejected.

If you produced a non-monic polynomial $f(x) = a_0 + a_1 x + \cdots + a_{24}\,
x^{24}$ with $a_{24} > 1$, convert it to the monic polynomial defining the same
number field before submitting:

$$
g(x) := a_{24}^{23} f\left(\dfrac{x}{a_{24}}\right),
$$

which is monic of degree 24 with integer coefficients. Equivalently, the
coefficients of $g$ are

$$
g_k = a_k \cdot a_{24}^{23 - k}, \qquad k = 0, 1, \ldots, 24.
$$

Note that $|{\mathrm{disc}}(g)|$ is typically *much* larger than
$|{\mathrm{disc}}(f)|$, so the monic requirement can raise the absolute
discriminant of the polynomial you submit.

## Submission Limits

- each team may make at most **200 submissions per day**, whether
  submitted through the SAIR competition website or via API call,
- each submission may contain at most **1,000 polynomials**,
- each team may therefore submit at most **200,000 polynomials per day**,
- the raw `submission.txt` file size limit is **1,000,000 bytes**.

These limits take effect on **July 31, 2026 at 00:00 UTC**.
Organizers may revise these limits during the competition based on submission
volume and evaluator capacity.

## Scoring

The main objective is to realize as many new $(24\mathrm{T}t, r)$ pairs as
possible.  Scoreable pairs are either verified pairs outside the frozen
LMFDB-derived baseline, or LMFDB baseline pairs unlocked by a strict exact
`nfdisc` improvement over $D_{\mathrm{base}}$.

For each scoreable pair, let $k$ be the number of credited teams for that
pair.  Each participant team contributes at most one count to $k$ for that
pair; for unlocked baseline pairs, LMFDB also counts as one baseline team.
For each scoring participant team, let $D$ be that team's best official
scoring discriminant for the pair, and let $D_0$ be the smallest such value
among all credited teams for that pair.  The team's score for that pair is

$$
2^{1-k}\cdot\frac{\log D_0}{\log D}.
$$

Any logarithm base gives the same score, since only the ratio of logarithms is
used.  A team that is the only one to realize a non-baseline scoreable pair
receives 1 point for that pair.  For an unlocked baseline pair, LMFDB counts
as one baseline team, so a single participant team beating
$D_{\mathrm{base}}$ receives 0.5 points.  If several teams
realize the same pair, the value of the pair is shared exponentially, while
smaller discriminants give a mild bonus.  Two participant teams that submit
polynomials defining the same number field both count as teams finding the same
$(24\mathrm{T}t, r)$ pair.

Within a single submission, if a team submits multiple polynomials that verify
to the same $(24\mathrm{T}t, r)$ pair, only the first verified polynomial for
that pair in the original `submission.txt` line order is considered for that
submission.  Participants should therefore submit only one polynomial for a
given expected $(24\mathrm{T}t, r)$ pair within a single submission: the one
they believe has the smallest scoring discriminant.  In a later submission,
the same team may submit another polynomial to improve its value of $D$ for
the same pair, but that team still contributes one count to $k$.

The official scoring discriminant $D$ is selected by pair, not by row.  For a
scoreable non-baseline $(24\mathrm{T}t, r)$ pair, the evaluator first tries to
compute absolute number-field discriminants using PARI/GP `nfdisc` with a
60-second timeout per polynomial.  If every such computation succeeds for that
pair, those number-field discriminants are used as $D$.  If any such
computation times out or fails, the entire non-baseline pair is scored with
the mixed discriminant computed by PARI/GP as `nfdisc([f,100000])`.

LMFDB baseline improvements use the stricter rule in the June 18 update:
mixed discriminants cannot unlock baseline pairs, and only a successfully
computed exact `nfdisc` with $D < D_{\mathrm{base}}$ is scoreable.  See
[evaluation](evaluation.md) for the precise schema and evaluator behavior.

## Verification

The mathematical verifier is Magma, a computational algebra system widely used
in computational number theory and group theory.  A polynomial counts only if
Magma verifies that it is irreducible of degree 24 and computes a transitive
degree 24 Galois group label.

The verifier records the computed group label, signature, and status:

```text
computed_label, computed_r, status
```

Internal evaluator files may carry the submitted coefficient string so that the
same polynomial can be passed from Magma to PARI/GP.  User-facing responses and
public leaderboards do not echo submitted coefficients.

The PARI/GP discriminant workflow computes the polynomial, number-field,
mixed, and official scoring discriminants when available.  Participant
responses and public leaderboard data may include these discriminants and the
score components for scoreable pairs.  The exact output fields and pair-level
mixed-discriminant behavior are specified in [evaluation](evaluation.md).

## Why This Is Hard

Degree 24 is large enough that brute-force search becomes expensive, while the
space of possible groups and signatures is enormous.  Random sparse
polynomials often land in common large groups, repeated constructions can
rediscover already-covered signatures, and some groups require much more
targeted algebraic structure.

Good submissions may use computational algebra, targeted constructions,
specialization, composita, local constraints, modular factorization patterns,
resolvents, class field constructions, or other methods.  The competition
rewards verifiable mathematical output, not the method used to find it.

## Competition Integrity

IGP24 rewards newly verified mathematical coverage, not claims about coverage.
Participants may use computational algebra systems, public databases, papers,
preprints, code search, LLMs, agents, and collaborative workflows.  What
matters for scoring is that the submitted polynomials verify correctly
against the official Magma pipeline and improve on the frozen official
baseline.

Invalid competition progress includes:

1. presenting an official-baseline $(24\mathrm{T}t, r)$ pair as a new
   discovery, or as a scoreable baseline improvement without a strict exact
   `nfdisc` improvement over $D_{\mathrm{base}}$,
2. repeatedly submitting duplicate, sign-changed, translated, scaled, or
   otherwise trivially equivalent variants only to waste evaluation resources,
3. including claimed `24Tt`, `r`, discriminant, or metadata columns that try to
   bypass official verification,
4. exploiting parser edge cases, malformed text, timeouts, nondeterminism, or
   implementation details of the verifier,
5. modifying the frozen LMFDB-derived baseline, verifier, or scoring scripts
   and presenting the resulting scores as official,
6. using private organizer-only data, hidden test outputs, or leaked baseline
   updates.

Organizers may request enough provenance to reproduce or audit a high-scoring
submission.  Public mathematical sources are allowed, but participants should
cite them when a submitted polynomial is taken from or directly adapted from
existing work.  Once the competition opens, official scoring is against the
baseline frozen in git for that round.

## Verification Tools

For reference, the competition page provides:

- the Magma verifier used to compute the `24Tt` label and signature `r`,
- the PARI/GP discriminant calculator used for exact `nfdisc` and mixed
  discriminant calculations,
- the LMFDB baseline CSV, available as a static download from the competition
  website, used for official baseline comparisons.

Computing the `24Tt` label locally requires access to Magma.  The PARI/GP
discriminant calculations and the LMFDB baseline file can be inspected
independently.  The scoring algorithm is described in detail in
[evaluation](evaluation.md).

## Team Participation and Anti-Cheating Policy

Each individual or organization can participate in only one team.
Team size is not capped.  This is intended to better support collaboration,
including larger groups that combine mathematical insight, computation,
software engineering, and AI-assisted workflows.
Teams may add members during the competition, subject to organizer approval
and platform support, but teams may not merge after either team has submitted.
Participants are encouraged to collaborate within their registered team and
form teams before submitting.
If coordinated cheating is detected (including sockpuppet teams), all related
teams will be disqualified.

## Community Feedback

Questions and feedback on the rules, scoring, and evaluation procedures are
welcome.

Join the SAIR Foundation Zulip community for discussion and collaboration:
<https://zulip.sair.foundation/>


---

# IGP24 Evaluation

This document specifies the evaluation protocol for IGP24.  The
participant-facing summary is [overview](overview.md); this file is the
technical source for parser rules, verifier outputs, discriminant computation,
and leaderboard fields.

## Submission Artifact

A submission is a single plain text file:

```text
submission.txt
```

Each non-empty line contains one degree 24 integer polynomial as 25
comma-separated coefficients in ascending powers, i.e. $a_0, a_1, \ldots, a_{24}$:

```text
a_0,a_1,...,a_24
```

Lines beginning with `#` are comments and are ignored.

Example from the LMFDB baseline, representing $x^{24} + 2$:

```text
2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1
```

## Coefficient Rules

Each polynomial line must satisfy:

- exactly 25 integer coefficients,
- $a_0 \neq 0$,
- $a_{24} = 1$ (submissions must be monic; non-monic polynomials are rejected —
  see [overview](overview.md) for converting a non-monic polynomial to the monic one
  defining the same number field),
- coefficient-only format: a coefficient line is exactly 25 decimal integers.

Coefficients must be listed in ascending powers, constant term $a_0$ first.

You may annotate any line with a trailing `#` comment -- including your own
expected $(24\mathrm{T}t, r)$ -- and may add full-line `#` comments anywhere.
All comments are ignored by the verifier and never affect scoring.

## Submission Limits

Each submission must satisfy:

- at most 1,000 valid polynomial lines,
- raw `submission.txt` size at most 1,000,000 bytes.

Each team may make at most 200 submissions per day, whether submitted through
the SAIR competition website or via API call.  With at most 1,000 polynomials
per submission, each team may submit at most 200,000 polynomials per day.

These limits take effect on July 31, 2026 at 00:00 UTC.
Organizers may revise these limits during the competition based on submission
volume and evaluator capacity.

Within a single submission, if multiple submitted polynomials verify to the
same $(24\mathrm{T}t, r)$ pair, only the first verified polynomial for that
pair in the original `submission.txt` line order is considered for that
submission.  The first verified polynomial is determined after parser and
Magma validation.  Participants should therefore submit only one polynomial
for a given expected $(24\mathrm{T}t, r)$ pair within a single submission: the
one they believe has the smallest scoring discriminant.

Later submissions may improve a team's official scoring discriminant for a
pair.  Across all submissions, each team can receive credit at most once for a
given $(24\mathrm{T}t, r)$ pair and contributes at most one count to the
number of teams finding that pair.

## Scoring Unit

The scoring unit is the verified $(24\mathrm{T}t, r)$ pair together with the
team.  A scoreable pair is either:

- a verified pair outside the official LMFDB-derived baseline, or
- a baseline pair unlocked by a participant row whose exact `nfdisc` is
  successfully computed and strictly smaller than $D_{\mathrm{base}}$.

If two participant teams submit polynomials defining the same number field and
the same scoreable $(24\mathrm{T}t, r)$ pair, both teams count as teams that
found that pair.  This keeps the first phase focused on realizing as many
group and signature pairs as possible.

For baseline pairs, mixed discriminants cannot unlock scoring.  A participant
row with `nfdisc` timeout, `nfdisc` failure, or only a mixed discriminant does
not beat the baseline.

## Verification Pipeline

The official pipeline is:

1. Parse `submission.txt`.
2. Convert accepted lines into the TSV format consumed by the Magma batch
   harness.
3. Run Magma verification using the reference verifier described below.
4. Keep only rows with `status=ok`.
5. For each submission, keep only the first verified polynomial for each
   $(24\mathrm{T}t, r)$ pair, using the original line order in
   `submission.txt`.
6. Compute the discriminant data for the remaining verified rows.
7. Classify each row as either a non-baseline pair candidate or a baseline
   improvement candidate.
8. For non-baseline pairs, apply the standard pair-level exact/mixed
   discriminant protocol.
9. For baseline pairs, keep only rows with a successfully computed exact
   `nfdisc` satisfying $D < D_{\mathrm{base}}$.
10. For each team and scoreable pair, keep the row with the smallest official
    scoring discriminant $D$ across all of that team's submissions.
11. Score by team and $(24\mathrm{T}t, r)$ pair.

The verifier returns:

```text
computed_label, computed_r, status
```

`computed_r` is the number of real roots.  Internal evaluator files may carry
the submitted coefficient string so that the same polynomial can be passed
from Magma to PARI/GP.  User-facing responses and public leaderboards do not
echo submitted coefficients.

The scoring-discriminant step then records:

```text
poly_disc_abs, field_disc_abs, mixed_disc_abs, scoring_disc_abs, disc_source
```

`poly_disc_abs` is the absolute polynomial discriminant computed by PARI/GP,
not by the Magma verifier.  `field_disc_abs` is the absolute number-field
discriminant when `nfdisc` succeeds.  `mixed_disc_abs` is the mixed
discriminant used as fallback and for pair-level mixed scoring; as of July 9,
it is computed by PARI/GP as `nfdisc([f,100000])`.  Finally,
`scoring_disc_abs` is the value of $D$ used in the leaderboard formula.
`disc_source` is `exact_nfdisc` when the pair is scored with number-field
discriminants and `mixed_disc` when the pair is scored with mixed
discriminants.  The scoring key is the verified pair together with the team.

For non-baseline pairs, if `nfdisc` times out or fails for a row but the mixed
discriminant is computed successfully, the row remains scoreable with
`disc_source=mixed_disc`.  For baseline pairs, the mixed fallback is not
scoreable: only exact `nfdisc` rows with $D < D_{\mathrm{base}}$ can unlock
the pair.  A baseline row with only mixed discriminant data is not scoreable
even if the discriminant workflow itself completed successfully.  Rows with
`timeout` or `error` status are never scoreable.

The user-facing response should not echo submitted coefficients.  For accepted
polynomials, it may report `computed_label`, `computed_r`, the available
discriminants above, and the score components for each scoreable pair:
`k_teams`, `other_teams_count`, `best_scoring_disc_abs`, `scoring_disc_abs`,
`disc_source`, and `points`.

## Reference Programs

The following programs are provided for reference and reproducibility.  The
official competition service remains the source of truth for accepted
submissions, verified results, and leaderboard updates.

### Reference Magma Verifier

Computing the `24Tt` label requires access to
[Magma](https://magma.maths.usyd.edu.au/magma/).  The reference Magma verifier
checks that a coefficient string defines an irreducible degree 24 polynomial,
then computes the degree-24 transitive group label and the number of real
roots.

```magma
function t24polydata(s)
/*
    Given a string containing a sequence of integers representing an
    irreducible polynomial f(x) of degree 24, returns:
    - the T-number of the Galois group of f(x)
    - the number of real roots of f(x)
    - the absolute value of the discriminant of f(x)
    and otherwise 0,0,0 is returned.

    Reversing the order of coefficients will not change the results
    so they can be ordered either by increasing powers of x or by
    decreasing powers of x, there is no need to fix a convention.
*/
    regex := "[ \t]*[+-]?[0-9]+([ \t]*,[ \t]*[+-]?[0-9]+)*[ \t]*";
    b,s := Regexp(regex,s);
    if not b then return 0,0,0; end if;
    a := [Integers()|StringToInteger(c):c in Split(s,",")];
    if #a ne 25 or a[1] eq 0 or a[#a] eq 0 then return 0,0,0; end if;
    R<x> := PolynomialRing(Integers());
    f := R!a;
    if not IsIrreducible(f) then return 0,0,0; end if;
    n := TransitiveGroupIdentification(GaloisGroup(f));
    r := NumberOfRealRoots(f);
    d := Abs(Discriminant(f));
    return n,r,d;
end function;

function t24labeldata(s)
/*
    Given a string containing a sequence of integers representing an
    irreducible polynomial f(x) of degree 24, returns:
    - the T-number of the Galois group of f(x)
    - the number of real roots of f(x)
    and otherwise 0,0 is returned.

    This lighter path is used by the competition verifier, where scoring
    discriminants are computed separately by PARI/GP.
*/
    regex := "[ \t]*[+-]?[0-9]+([ \t]*,[ \t]*[+-]?[0-9]+)*[ \t]*";
    b,s := Regexp(regex,s);
    if not b then return 0,0; end if;
    a := [Integers()|StringToInteger(c):c in Split(s,",")];
    if #a ne 25 or a[1] eq 0 or a[#a] eq 0 then return 0,0; end if;
    R<x> := PolynomialRing(Integers());
    f := R!a;
    if not IsIrreducible(f) then return 0,0; end if;
    n := TransitiveGroupIdentification(GaloisGroup(f));
    r := NumberOfRealRoots(f);
    return n,r;
end function;

/*
   Example command:

     magma -b f:="2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1" t24.m
*/
if assigned f then
    n,r,d := t24polydata(f);
    printf "%o,%o,%o\n",n,r,d;
    exit;
end if;
```

### Reference PARI/GP Discriminant Calculator

The official scoring discriminant is computed separately from the Magma
verifier.  For a polynomial with coefficients listed in ascending powers, use
`Polrev([a0,a1,...,a24])` in [PARI/GP](https://pari.math.u-bordeaux.fr/).
The exact number-field discriminant is computed with
[`nfdisc`](https://pari.math.u-bordeaux.fr/dochtml/html/General_number_fields.html#nfdisc),
which returns the discriminant of the number field defined by a monic
irreducible polynomial.  The evaluator attempts `nfdisc` with a 60-second
timeout.  The polynomial discriminant `poldisc(f)` is also computed as an
auxiliary value.

For non-baseline pairs, if any relevant `nfdisc` computation for that pair
times out or fails, the whole pair is scored with the mixed discriminant
below, using bound `100000`.  This updated method is simpler and more
efficient than the earlier product-form implementation.

```gp
\\ Computes the PARI/GP bounded discriminant used as the mixed fallback.
mixed_disc(f, B = 100000) = {
  return(nfdisc([f, B]));
}
```

Example PARI/GP session:

```gp
f = Polrev([2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]);
abs(nfdisc(f))
abs(poldisc(f))
abs(mixed_disc(f, 100000))
```

For baseline pairs, the mixed fallback is disabled: only a successfully
computed exact `nfdisc` strictly below $D_{\mathrm{base}}$ can unlock and
score on a baseline pair.

## Official Baseline

The official baseline is the frozen LMFDB-derived baseline CSV, available as
a static download from the competition website.

It contains known polynomials, together with their Galois group, signature,
absolute polynomial discriminant `poly_disc_abs`, exact number-field
discriminant `nfdisc_abs`, scoring discriminant type `scoring_disc`, and
coefficients.  For official scoring, the baseline is used both to define the
set of already-known $(24\mathrm{T}t, r)$ pairs and to define the improvement
threshold $D_{\mathrm{base}}$ for each baseline pair.

The baseline consists of the frozen LMFDB snapshot, and the baseline used for
official scoring is frozen in git.

For a baseline $(24\mathrm{T}t, r)$ pair, $D_{\mathrm{base}}$ is the smallest
`nfdisc_abs` recorded for that pair in the baseline.  The
current LMFDB-derived baseline has exact `nfdisc` values for all 622 baseline
pairs, so baseline improvements are compared only against exact `nfdisc`
values.

## Leaderboard Metrics

Scoring is computed independently for each scoreable
$(24\mathrm{T}t, r)$ pair:

1. Within a single submission from one team, only the first verified polynomial
   for that pair in the original line order is considered.
2. Across later submissions, the same team may improve its official scoring
   discriminant $D$ for that pair.  The team still contributes only once to
   the number of teams finding the pair.
3. Let $k$ be the number of credited teams for the pair.  Each participant
   team contributes at most one count to $k$; for unlocked baseline pairs,
   LMFDB also counts as one baseline team.  For each scoring participant team,
   let $D$ be that team's best official scoring discriminant for the pair, and
   let $D_0$ be the smallest such value among all credited teams.  That
   participant team receives

   $$
   2^{1-k}\cdot\frac{\log D_0}{\log D}
   $$

   points for the pair.

Any logarithm base gives the same score, since only the ratio of logarithms is
used.  If a participant team is the only team to realize a non-baseline
scoreable pair, then $k=1$ and $D=D_0$, so the pair is worth 1 point.  For an
unlocked baseline pair, LMFDB counts as one baseline team, so a single
participant team beating $D_{\mathrm{base}}$ has $k=2$ and receives 0.5
points.  If several teams realize the same pair, the exponential factor shares
the value of the pair, while the logarithmic factor mildly rewards smaller
discriminants.

For an unlocked baseline pair, only participant teams with exact `nfdisc`
values strictly smaller than $D_{\mathrm{base}}$ count for the pair, so
$k = 1 +$ the number of participant teams beating $D_{\mathrm{base}}$.  The
value $D_0$ is the smallest discriminant among $D_{\mathrm{base}}$ and all
beating participant teams.

For non-baseline pairs, the official scoring discriminant $D$ is produced by
the evaluation pipeline using the following fixed pair-level protocol:

1. For each scoreable non-baseline $(24\mathrm{T}t, r)$ pair, try to compute
   the absolute number-field discriminant of every considered row with PARI/GP
   `nfdisc`, using a 60-second timeout per polynomial.
2. If all `nfdisc` computations for that pair succeed, use those absolute
   number-field discriminants as the values of $D$ for that pair.
3. If any `nfdisc` computation for that pair times out or fails, use the mixed
   discriminant for every considered row in that pair.  This is a pair-level
   flag: once triggered, all teams' scoreable rows for that
   $(24\mathrm{T}t,r)$ pair are evaluated with `mixed_disc_abs`, computed by
   PARI/GP as `nfdisc([f,100000])`.

All leaderboard entries scored with mixed discriminants, including entries
submitted before the July 9 update, are computed and scored with this updated
algorithm.  Scores for teams with mixed-discriminant entries may therefore
change slightly when the leaderboard is recomputed.

For baseline pairs, this mixed fallback is disabled.  A row unlocks and scores
only if its exact `nfdisc` is successfully computed and strictly smaller than
$D_{\mathrm{base}}$.  Equality with $D_{\mathrm{base}}$, a larger exact
`nfdisc`, `nfdisc` timeout, `nfdisc` failure, or mixed-only discriminant data
receives no score for that baseline pair.

If a row cannot supply the discriminant required by the relevant source
selection, that row is not scoreable for that leaderboard run and is reported
in the evaluator's ignored counts.

The evaluator records which source was used for each pair.  The recorded value
of $D$ is final for that leaderboard run.

## Public Outputs and Policy Hooks

During the competition, public leaderboard outputs may display scores,
verified pair coverage, the number of teams credited for each pair, the best
public scoring discriminant for each pair, and the discriminant source used
for each pair.  They do not display submitted polynomial coefficients.

The evaluator treats claimed labels, signatures, discriminants, and metadata
columns in `submission.txt` as comments or invalid input; official values are
computed only by the parser, Magma verifier, PARI/GP discriminant workflow, and
scoring reference.  If a submitted polynomial is taken from or directly
adapted from an existing public source, participants should cite that source
in their submission notes or related provenance.  Organizers may request
provenance or reproduction notes for high-scoring submissions.

Team membership, collaboration, confidentiality, and anti-cheating policy are
summarized for participants in [overview](overview.md).

