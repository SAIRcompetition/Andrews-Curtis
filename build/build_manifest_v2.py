#!/usr/bin/env python3
"""Generate the frozen ACC data artifacts (manifest version ``acms-v3``).

Generate verifier data, the two public problem lists, training data, and
optional ``competition/competition.yaml`` metadata.
Run ``build/sync_dataset.py`` first: the scored pool comes from
``build/data/`` (distilled from the private SAIR dataset release), not
from ``reference/index.html`` any more.  ``reference/index.html`` is
still the source of the MS-1190 denominator and of the 424 published
trivializations, so the MS-only builders are imported from
``build/build_manifest.py`` unchanged.

The two Discovery problems use the same 10115 presentations, so the
manifest holds 20230 scored challenges: ``ac-NNNNN`` under
``ac-r2-v1`` (target the ordered pair (x, y)) and ``sac-NNNNN`` under
``sac-r8-v1`` (target the empty presentation, stabilization allowed up
to rank 8).  ``sac-N`` and ``ac-N`` are the same presentation.

Outputs:

  competition/problems/ac.jsonl                         10115 AC descriptions
  competition/problems/stable_ac.jsonl                  10115 Stable AC descriptions
  competition/tools/verifier/data/manifest.json         20230 scored challenges
  competition/tools/verifier/data/move_spec.json        FROZEN, byte-identity checked
  competition/tools/verifier/data/stable_move_spec.json FROZEN once written
  competition/tools/verifier/data/ms1190_metadata.csv   the MS-1190 denominator
  competition/tools/verifier/data/golden_vectors.json   conformance vectors
  competition/examples/training_424.json               FROZEN, byte-identity checked
  competition/examples/stable_training_424.json        FROZEN once written
  competition/competition.yaml                         generated metadata
  build/private/challenge_map_private.tsv              NEVER published
  build/private/pool_stats.json                         NEVER published

The manifest omits internal difficulty labels and direct source mappings: every scored
challenge is exactly {challenge_id, generators, initial_relators,
target_relators, move_spec_version, scored, base_score, instance_hash,
freeze_date}, challenge ids are a seeded shuffle of the pool, and
:func:`leak_check` re-reads the emitted file to prove no private id or
provenance token survived. Public relators can still be matched to known
mathematical sources; this is not an anonymity guarantee.

Deterministic: the only randomness is ``random.Random(CHALLENGE_ID_SEED)``,
so identical inputs give byte-identical outputs.
"""

import argparse
import collections
import csv
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from acms_verify import (  # noqa: E402
    __version__, canon, core, specs, stable_core)

from build_manifest import (  # noqa: E402
    GENERATORS, LIMITS, MOVE_DESCRIPTIONS, TARGET, build_golden,
    build_move_spec, build_training, dump, load_items, ms_initial, stats)
from build_problems import write_problems  # noqa: E402
from sync_dataset import (  # noqa: E402
    DATA_DIR, EXPECTED_ADDED_OPEN, EXPECTED_MS_STATUS,
    EXPECTED_OVERLAP_BY_STATUS, EXPECTED_POOL_ROWS, EXPECTED_TIERS,
    POOL_PATH, SOURCES_PATH, canon_pair)

MANIFEST_VERSION = "acms-v3"
COMPETITION = "acms"
CHALLENGE_ID_SEED = 20260903
CHALLENGE_ID_FORMAT = "ac-%05d"
STABLE_CHALLENGE_ID_FORMAT = "sac-%05d"
#: The Stable AC problem's target: the empty presentation.
STABLE_TARGET = []

VERIFIER_DATA_DIR = REPO / "competition" / "tools" / "verifier" / "data"
EXAMPLES_DIR = REPO / "competition" / "examples"
PROBLEMS_DIR = REPO / "competition" / "problems"
PRIVATE_DIR = REPO / "build" / "private"
COMPETITION_STATE_PATH = REPO / "build" / "competition_state.json"
SCHEDULE_FIELDS = ("freeze_date", "registration_opens", "submissions_open", "prove_submissions_open",
                   "submission_deadline")

#: Exactly the keys a public challenge record may carry (O-4: no
#: difficulty, family, or provenance signal reaches contestants).
CHALLENGE_KEYS = {"challenge_id", "generators", "initial_relators",
                  "target_relators", "move_spec_version", "scored",
                  "base_score", "instance_hash", "freeze_date"}

#: Substrings that must not occur in the emitted manifest.  None of them
#: can appear legitimately: the manifest is lowercase ASCII JSON whose
#: only string values are the nine keys above, "x"/"y", "ac-r2-v1" and
#: "sac-r8-v1", the two move-spec file names, "acms"/"acms-v3",
#: "sha256:"-prefixed lowercase hex, the ac / sac ids and the
#: freeze date.
BANNED_TOKENS = ("tier", "pool", "family", "provenance", "w_vector",
                 "status_at_freeze", "MS-", "AUTH-", "INTL") + tuple(
                     "T%d_" % i for i in range(6))

PRIVATE_MAP_FIELDS = ("challenge_id", "master_id", "public_id", "pool",
                      "tier", "tier_basis", "total_length", "in_draw",
                      "ms1190_status", "ms1190_seq")


def serialize(obj):
    """Exactly what :func:`build_manifest.dump` writes."""
    return json.dumps(obj, indent=1) + "\n"


def load_competition_state(path=None):
    """Read the sole source of publication state and dates.

    Unannounced values are JSON null. Dates, when announced, are UTC
    timestamps; a freeze commit is a full Git object id, never a label.
    Release readiness and Git verification are enforced by release.py.
    """
    path = Path(path) if path is not None else COMPETITION_STATE_PATH
    state = json.loads(path.read_text(encoding="utf-8"))
    expected = {"status", "freeze_commit", "announced_dates", *SCHEDULE_FIELDS}
    if not isinstance(state, dict) or set(state) != expected:
        raise ValueError("competition state must contain exactly %s" %
                         ", ".join(sorted(expected)))
    announced = state["announced_dates"]
    if not isinstance(announced, dict) or set(announced) != {
            "registration", "discovery", "prove", "deadline"}:
        raise ValueError("announced_dates must contain registration, discovery, "
                         "prove, and deadline")
    for value in announced.values():
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("announced dates must be calendar dates in YYYY-MM-DD form")
        datetime.strptime(value, "%Y-%m-%d")
    status = state["status"]
    if status not in ("prelaunch", "active", "finished"):
        raise ValueError("competition status must be prelaunch, active, or finished")
    for field in SCHEDULE_FIELDS:
        value = state[field]
        if value is None:
            continue
        if not isinstance(value, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
            raise ValueError("%s must be null or a UTC timestamp" % field)
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError("%s is not a valid UTC timestamp" % field) from exc
    commit = state["freeze_commit"]
    if commit is not None and (not isinstance(commit, str) or not re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit)):
        raise ValueError("freeze_commit must be null or a full Git object id")
    return state



def freeze_guard(name, obj, create_if_missing=False):
    """Abort unless a frozen artifact regenerates byte for byte.

    With ``create_if_missing`` the first build writes the file and every
    later build must reproduce it exactly — the mode used for the two
    Stable AC artifacts, which are frozen from the moment they first
    land in git.
    """
    directory = (EXAMPLES_DIR if name in ("training_424.json", "stable_training_424.json")
                 else VERIFIER_DATA_DIR)
    path = directory / name
    generated = serialize(obj).encode("utf-8")
    if create_if_missing and not path.exists():
        print("freeze guard: creating %s (%d bytes); frozen from now on"
              % (name, len(generated)))
        return generated
    on_disk = path.read_bytes()
    assert generated == on_disk, (
        "FROZEN ARTIFACT DRIFT: %s would change (%d -> %d bytes).  "
        "move_spec.json, training_424.json, stable_move_spec.json and "
        "stable_training_424.json are frozen; refusing."
        % (name, len(on_disk), len(generated)))
    return generated


def ms1190_rows(items, training_ids):
    """The MS-1190 denominator csv rows (no challenge_id, no scored:
    MS instances are no longer the pool, so those columns would be
    meaningless — and challenge_id would leak the pool membership)."""
    rows = []
    for seq, it in enumerate(items, 1):
        has_path = bool(it.get("path"))
        status = {("trivial", True): "certified",
                  ("trivial", False): "uncertified",
                  ("unsolved", False): "open"}[(it["status"], has_path)]
        rows.append({
            "seq": seq, "n": it["n"], "w": it["w"],
            "w_vector": " ".join(str(a) for a in it["wv"]),
            "status_at_freeze": status,
            "reported_class": it.get("cls", ""),
            "training_id": training_ids.get(seq, ""),
            "prototype_path_length": len(it["path"]) if has_path else "",
        })
    counts = collections.Counter(r["status_at_freeze"] for r in rows)
    assert dict(counts) == EXPECTED_MS_STATUS, dict(counts)
    return rows


def ms1190_keys(items):
    """``status -> set of canonical relator pairs`` over all 1190 rows."""
    keys = collections.defaultdict(set)
    for it in items:
        status = {("trivial", True): "certified",
                  ("trivial", False): "uncertified",
                  ("unsolved", False): "open"}[
                      (it["status"], bool(it.get("path")))]
        keys[status].add(canon_pair(ms_initial(it["n"], it["wv"])))
    assert {k: len(v) for k, v in keys.items()} == EXPECTED_MS_STATUS
    return keys


def load_pool(items, training):
    """Read build/data and re-assert every pool invariant independently."""
    assert POOL_PATH.exists() and SOURCES_PATH.exists(), (
        "missing %s — run build/sync_dataset.py first" % DATA_DIR)
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in
            POOL_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == EXPECTED_POOL_ROWS, len(rows)
    assert sources["scored_pool_rows"] == EXPECTED_POOL_ROWS

    ids = [r["id"] for r in rows]
    assert len(set(ids)) == len(ids), "duplicate master id in the pool"
    assert dict(collections.Counter(r["tier"] for r in rows)) == \
        EXPECTED_TIERS
    assert max(r["total_length"] for r in rows) == \
        sources["max_total_relator_length"]

    keys = {}
    for r in rows:
        for w in r["relators_int"]:
            assert list(core.free_reduce(w)) == w, \
                "initial relator not freely reduced: %s" % r["id"]
            assert all(a in (-2, -1, 1, 2) for a in w), \
                "alphabet outside {+-1,+-2}: %s" % r["id"]
        assert sum(len(w) for w in r["relators_int"]) == r["total_length"]
        key = canon_pair(r["relators_int"])
        assert key not in keys, "duplicate canonical pair in the pool"
        keys[key] = r["id"]

    ms = ms1190_keys(items)
    assert ms["open"] <= set(keys), "an open MS-1190 instance is unscored"
    assert not (ms["certified"] & set(keys)), \
        "a certified MS-1190 instance is scored"
    assert len(ms["uncertified"] & set(keys)) == \
        EXPECTED_OVERLAP_BY_STATUS["uncertified"]

    # Independent recomputation: the published training paths must not
    # solve any scored challenge.
    train_keys = {canon_pair(e["initial_relators"])
                  for e in training["instances"]}
    assert len(train_keys) == 424, len(train_keys)
    assert not (train_keys & set(keys)), \
        "a training instance is also a scored challenge"

    by_status = collections.Counter(r["ms1190_status"] for r in rows)
    assert by_status["open"] == EXPECTED_MS_STATUS["open"], by_status
    assert by_status["uncertified"] == \
        EXPECTED_OVERLAP_BY_STATUS["uncertified"], by_status
    assert sum(1 for r in rows if not r["in_draw"]) == EXPECTED_ADDED_OPEN
    return rows, sources


def assign_ids(rows):
    """Seeded shuffle of the master-id order, then ac-NNNNN in order."""
    assert canon._ID_RE.match(CHALLENGE_ID_FORMAT % 1), CHALLENGE_ID_FORMAT
    ordered = sorted(rows, key=lambda r: r["id"])
    random.Random(CHALLENGE_ID_SEED).shuffle(ordered)
    for seq, row in enumerate(ordered, 1):
        row["seq"] = seq
        row["challenge_id"] = CHALLENGE_ID_FORMAT % seq
    ordered.sort(key=lambda r: r["challenge_id"])
    assert [r["challenge_id"] for r in ordered] == \
        [CHALLENGE_ID_FORMAT % i for i in range(1, len(ordered) + 1)]
    return ordered


def challenge_record(challenge_id, initial, target, version, move_spec_hash, freeze_date):
    return {
        "challenge_id": challenge_id,
        "generators": GENERATORS,
        "initial_relators": initial,
        "target_relators": target,
        "move_spec_version": version,
        "scored": True,
        "base_score": 1,
        "instance_hash": canon.instance_hash(
            challenge_id, GENERATORS, initial, target, version,
            move_spec_hash),
        "freeze_date": freeze_date,
    }


def build_manifest_v3(rows, competition_state=None):
    """One record per presentation and problem: all ac- IDs, then all sac- IDs.

    Matching numeric suffixes carry identical generators and initial relators.
    Targets and move specifications distinguish AC from Stable AC. The
    challenge ID is included in instance_hash, so changing an ID requires
    recomputing that hash and the enclosing manifest_hash.
    """
    if competition_state is None:
        competition_state = load_competition_state()
    freeze_date = competition_state["freeze_date"]
    ac_hash = specs.SPECS[core.MOVE_SPEC_VERSION].move_spec_hash
    sac_hash = specs.SPECS[stable_core.MOVE_SPEC_VERSION].move_spec_hash
    challenges = []
    for row in rows:
        initial = [list(w) for w in row["relators_int"]]
        challenges.append(challenge_record(
            row["challenge_id"], initial, TARGET, core.MOVE_SPEC_VERSION,
            ac_hash, freeze_date))
    for row in rows:
        initial = [list(w) for w in row["relators_int"]]
        challenges.append(challenge_record(
            STABLE_CHALLENGE_ID_FORMAT % row["seq"], initial, STABLE_TARGET,
            stable_core.MOVE_SPEC_VERSION, sac_hash, freeze_date))
    for c in challenges:
        assert set(c) == CHALLENGE_KEYS, sorted(set(c) ^ CHALLENGE_KEYS)
    assert len(challenges) == 2 * len(rows), len(challenges)

    ids = [c["challenge_id"] for c in challenges]
    assert len(set(ids)) == len(ids)
    assert ids[:len(rows)] == sorted(ids[:len(rows)])
    assert ids[len(rows):] == sorted(ids[len(rows):])
    for ac, sac in zip(challenges[:len(rows)], challenges[len(rows):]):
        assert ac["challenge_id"][3:] == sac["challenge_id"][4:]
        assert ac["generators"] == sac["generators"]
        assert ac["initial_relators"] == sac["initial_relators"]
        assert sac["target_relators"] == STABLE_TARGET

    move_specs = move_spec_headers()
    assert specs.check_move_specs(move_specs) == []
    return {
        "manifest_version": MANIFEST_VERSION,
        "competition": COMPETITION,
        "move_specs": move_specs,
        "manifest_hash": canon.manifest_hash(
            [c["instance_hash"] for c in challenges]),
        "freeze_date": freeze_date,
        "generators": GENERATORS,
        "limits": LIMITS,
        "challenge_count": len(challenges),
        "presentation_count": len(rows),
        "challenges": challenges,
    }


# ---------------------------------------------------------------------------
# the Stable AC problem (sac-r8-v1)
# ---------------------------------------------------------------------------

#: Loose-trivial rank-2 final state -> shortest suffix to the EMPTY
#: presentation under sac-r8-v1.  One uniform recipe: invert every
#: inverted relator (ids 0 and 1), then destabilize r1 and r0 (ids 16,
#: 15).  The general law, BFS-verified in build/checks/stable_canon.py
#: and in tests/test_stable_core.py: from any rank-k state whose k
#: relators are k distinct single generator letters, the minimal cost to
#: () is k + (number of inverted letters).
STABLE_CANON_SUFFIX = {
    ((1,), (2,)): [16, 15],
    ((2,), (1,)): [16, 15],
    ((-1,), (2,)): [0, 16, 15],
    ((1,), (-2,)): [1, 16, 15],
    ((-2,), (1,)): [0, 16, 15],
    ((2,), (-1,)): [1, 16, 15],
    ((-1,), (-2,)): [0, 1, 16, 15],
    ((-2,), (-1,)): [0, 1, 16, 15],
}

#: Suffix appended to every ac-r2-v1 certificate to make it a sac-r8-v1
#: one: the 424 training paths all end at the exact ordered pair (x, y).
STABLE_TRAINING_SUFFIX = STABLE_CANON_SUFFIX[((1,), (2,))]

#: [Verified] aggregate statistics of the 424 stable training paths.
#: Each is the ac-r2-v1 path plus STABLE_TRAINING_SUFFIX: +2 moves,
#: +0 peak (the suffix only shrinks the state), +1 work (totals 1 then 0).
EXPECTED_STABLE_LEN_STATS = (9, 28, 161, 35.6)
EXPECTED_STABLE_PEAK_STATS = (7, 14, 25, 14.7)
EXPECTED_STABLE_WORK_STATS = (44, 230, 2162, 348.0)
STABLE_DELTA = {"length": 2, "peak_total_relator_length": 0, "work": 1}

STABLE_CANON_RULE = (
    "From any rank-k state whose k relators are the k generators as "
    "single letters, each of g1..gk occurring exactly once and possibly "
    "inverted, the minimal cost to the empty presentation is "
    "k + (number of inverted letters): invert each inverted relator, "
    "then destabilize from the highest relator index down to 0.  The "
    "rows below are the k = 2 instance of that law, exhaustively "
    "verified by breadth-first search."
)


def stable_replay(initial, moves):
    """Replay under sac-r8-v1; every move must be applicable."""
    state = tuple(tuple(w) for w in initial)
    tot = sum(len(w) for w in state)
    peak = work = tot
    for m in moves:
        state, reason = stable_core.apply_move(state, m)
        assert reason is None, (m, reason)
        tot = sum(len(w) for w in state)
        peak = max(peak, tot)
        work += tot
    return state, peak, work


def stable_move_descriptions():
    """One human-readable line per move id, 0..256."""
    out = dict(MOVE_DESCRIPTIONS)
    for row in stable_core.MOVE_TABLE[core.NUM_MOVES:]:
        cat = row["category"]
        if cat == "stabilize":
            text = ("stabilize: rank k -> k+1; append the relator "
                    "r_k = g(k+1), a generator not used so far")
        elif cat == "destabilize":
            i = row["relator"]
            text = ("destabilize r%d: requires r%d to be exactly one "
                    "positive generator letter that occurs in no other "
                    "relator; drops r%d and that generator, rank k -> k-1, "
                    "renumbering every larger generator down by one" % (i, i, i))
        elif cat == "inversion":
            i = row["relator"]
            text = "r%d <- r%d^-1" % (i, i)
        elif cat == "multiplication":
            i, j = row["relator"], row["other"]
            text = "r%d <- r%d r%d%s" % (i, i, j,
                                         "^-1" if row["invert_other"] else "")
        else:
            i, c = row["relator"], row["conjugator"]
            name = stable_core.generator_name(c)
            text = ("r%d <- %s r%d %s^-1" % (i, name, i, name) if c > 0
                    else "r%d <- %s^-1 r%d %s" % (i, name, i, name))
        out[row["id"]] = text
    assert sorted(out) == list(range(stable_core.NUM_MOVES)), len(out)
    return {str(k): out[k] for k in sorted(out)}


def stable_letter_encoding():
    enc = {}
    for g in range(1, stable_core.MAX_RANK + 1):
        name = stable_core.generator_name(g)
        enc[name] = g
        enc[name + "^-1"] = -g
    return enc


def build_stable_move_spec(move_spec_hash):
    """competition/tools/verifier/data/stable_move_spec.json (frozen once written)."""
    rows = []
    for state, suffix in STABLE_CANON_SUFFIX.items():
        final, _, _ = stable_replay([list(w) for w in state], suffix)
        assert final == (), (state, suffix)
        negatives = sum(1 for w in state if w[0] < 0)
        assert len(suffix) == len(state) + negatives, (state, suffix)
        rows.append({"final_state": [list(w) for w in state],
                     "cost": len(suffix), "path": list(suffix)})
    rows.sort(key=lambda r: (r["cost"], r["final_state"]))
    assert len(rows) == 8, len(rows)
    return {
        "move_spec_version": stable_core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "hash_covers": "moves",
        "max_rank": stable_core.MAX_RANK,
        "generators": GENERATORS,
        "extra_generators": list(
            stable_core.GENERATOR_NAMES[len(GENERATORS):]),
        "letter_encoding": stable_letter_encoding(),
        "target_relators": STABLE_TARGET,
        "moves": [dict(r) for r in stable_core.MOVE_TABLE],
        "descriptions": stable_move_descriptions(),
        "canonicalization_table": {"rule": STABLE_CANON_RULE, "rows": rows},
        "notes": [
            "A state is an ordered list of k freely reduced relators over "
            "the k generators g1..gk, written as nonzero integers: +g for "
            "the generator, -g for its inverse.  g1 is x and g2 is y, "
            "matching ac-r2-v1; g3..g8 are the generators that only "
            "stabilization can introduce.  Every challenge starts at "
            "k = 2 and k never exceeds max_rank = 8.",
            "Words are freely reduced after every move (single left-fold "
            "stack cancellation).",
            "Move ids 0-13 are row for row identical to the ac-r2-v1 move "
            "table and act on r0 and r1 exactly as they do there, so the "
            "two specs agree wherever they overlap.",
            "Consequence: any accepted ac-r2-v1 certificate followed by "
            "[16, 15] reaches the stable target for the same presentation, "
            "provided the extended path still satisfies the limits: "
            "length increases by 2 and work by 1.  The ac-r2-v1 target is the ordered pair "
            "(x, y); destabilizing r1 then r0 empties it.  That costs "
            "exactly 2 more moves, 0 more peak total relator length and "
            "1 more work.  competition/examples/stable_training_424.json "
            "is that construction applied to all 424 published paths.",
            "stabilize (14) and destabilize (15-22) are inverse only up "
            "to relabeling: dropping generator g renumbers every larger "
            "generator down by one, so neither move has a fixed partner "
            "id and both carry inverse: null.  Every other row is closed "
            "under inversion, as in ac-r2-v1.",
            "destabilize requires the relator to be EXACTLY one positive "
            "generator letter -- (g), never (g^-1) and never a longer "
            "word -- and requires that generator to occur in no other "
            "relator.  Invert the relator first (ids 0, 1, 23-28) if it "
            "reads as an inverse.",
            "A move whose relator index is beyond the current rank, whose "
            "generator is beyond the current rank, that would stabilize "
            "past max_rank, or that fails the destabilize precondition is "
            "not applicable: the path is rejected with "
            "E_MOVE_NOT_APPLICABLE, carrying move_index, move and one of "
            "the reasons relator_out_of_rank, generator_out_of_rank, "
            "max_rank_exceeded, destabilize_precondition.  Applicability "
            "is checked at replay time, so the same move id means the "
            "same thing at every rank.",
            "The target is the EMPTY presentation, target_relators = []; "
            "a rejected path reports final_shape, the list of relator "
            "lengths it actually ended on.",
            "move_spec_hash = sha256 of the canonical JSON (RFC 8785 "
            "compatible: sorted keys, no whitespace, ASCII) of the "
            "'moves' array only.",
        ],
    }


def build_stable_training(training, move_spec_hash):
    """competition/examples/stable_training_424.json (frozen once written)."""
    entries = []
    lens, peaks, works = [], [], []
    for e in training["instances"]:
        moves = list(e["moves"]) + list(STABLE_TRAINING_SUFFIX)
        challenge = {
            "challenge_id": e["training_id"],
            "move_spec_version": stable_core.MOVE_SPEC_VERSION,
            "initial_relators": e["initial_relators"],
            "target_relators": STABLE_TARGET,
        }
        v = stable_core.verify(challenge, moves,
                               stable_core.MOVE_SPEC_VERSION, LIMITS)
        assert v["ok"], (e["training_id"], v)
        for key, delta in STABLE_DELTA.items():
            assert v[key] == e[key] + delta, (e["training_id"], key, v[key])
        lens.append(v["length"])
        peaks.append(v["peak_total_relator_length"])
        works.append(v["work"])
        entries.append({
            "training_id": e["training_id"],
            "family": e["family"],
            "n": e["n"], "w": e["w"], "w_vector": e["w_vector"],
            "generators": e["generators"],
            "initial_relators": e["initial_relators"],
            "target_relators": STABLE_TARGET,
            "move_spec_version": stable_core.MOVE_SPEC_VERSION,
            "moves": moves,
            "length": v["length"],
            "peak_total_relator_length": v["peak_total_relator_length"],
            "work": v["work"],
            "certificate_hash": v["certificate_hash"],
            "prototype_path_length": e["prototype_path_length"],
        })
    assert len(entries) == 424, len(entries)
    assert stats(lens) == EXPECTED_STABLE_LEN_STATS, stats(lens)
    assert stats(peaks) == EXPECTED_STABLE_PEAK_STATS, stats(peaks)
    assert stats(works) == EXPECTED_STABLE_WORK_STATS, stats(works)
    return {
        "format": "acms-training-v1",
        "move_spec_version": stable_core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "note": ("The 424 ac-r2-v1 training certificates of "
                 "training_424.json, each extended by the two-move "
                 "canonicalization suffix [16, 15] that destabilizes r1 "
                 "then r0, so every path ends at the EMPTY presentation "
                 "under sac-r8-v1.  Same 424 instances, same initial "
                 "relators; length +2, peak +0, work +1 against the "
                 "ac-r2-v1 entry with the same training_id.  These "
                 "instances are NOT scored challenges; they are published "
                 "training data (DESIGN.md 1.5, O-2)."),
        "length_stats": dict(zip(("min", "median", "max", "mean"),
                                 EXPECTED_STABLE_LEN_STATS)),
        "instances": entries,
    }


def move_spec_headers():
    """The manifest / golden / yaml ``move_specs`` list, from the registry."""
    return [{"move_spec_version": version,
             "move_spec_hash": spec.move_spec_hash,
             "file": spec.file,
             "target_relators": spec.target,
             "max_rank": spec.max_rank,
             "id_prefix": spec.id_prefix}
            for version, spec in specs.SPECS.items()]


def build_golden_v3(manifest, training, stable_training):
    """acms-golden-v2 conformance vectors for both move specifications.

    The AC half comes from :func:`build_manifest.build_golden`; the header
    supplies both ``move_specs`` and the stable vectors are appended.
    Synthetic submission IDs follow the current challenge naming scheme.
    """
    ac_hash = specs.SPECS[core.MOVE_SPEC_VERSION].move_spec_hash
    doc = build_golden(manifest, training, ac_hash)
    challenges = doc["challenges"]
    vectors = doc["verify_vectors"]
    sub_vectors = doc["submission_vectors"]

    stable_by_id = {e["training_id"]: e for e in stable_training["instances"]}
    picks = [e for e in training["instances"]
             if e["training_id"] in {c for c in challenges}]
    picks.sort(key=lambda e: (e["length"], e["training_id"]))
    assert len(picks) == 3, len(picks)

    def stable_challenge(cid, initial):
        return {"challenge_id": cid,
                "move_spec_version": stable_core.MOVE_SPEC_VERSION,
                "generators": GENERATORS,
                "initial_relators": initial,
                "target_relators": STABLE_TARGET}

    sac_ids = {}
    for e in picks:
        cid = "sac-train-" + e["training_id"].rsplit("-", 1)[1]
        sac_ids[e["training_id"]] = cid
        challenges[cid] = stable_challenge(cid, e["initial_relators"])
    challenges["golden-stable-xy"] = stable_challenge(
        "golden-stable-xy", [[1], [2]])
    challenges["golden-stable-yx"] = stable_challenge(
        "golden-stable-yx", [[2], [1]])
    challenges["golden-stable-pump"] = stable_challenge(
        "golden-stable-pump", [[1, 2], [1, 1, 2]])

    def sac_verify(cid, moves, limits=None):
        return stable_core.verify(challenges[cid], moves,
                                  stable_core.MOVE_SPEC_VERSION,
                                  limits or LIMITS)

    def accept(name, cid, moves):
        v = sac_verify(cid, moves)
        assert v["ok"], (name, v)
        vectors.append({
            "name": name, "challenge_id": cid, "moves": list(moves),
            "expected": {"ok": True, "length": v["length"],
                         "peak_total_relator_length":
                             v["peak_total_relator_length"],
                         "work": v["work"],
                         "certificate_hash": v["certificate_hash"]}})

    def reject(name, cid, moves, code, version=None, **expected):
        v = stable_core.verify(
            challenges[cid], list(moves),
            version or stable_core.MOVE_SPEC_VERSION, LIMITS)
        assert v["code"] == code, (name, v)
        for key, want in expected.items():
            assert v[key] == want, (name, key, v)
        vec = {"name": name, "challenge_id": cid, "moves": list(moves),
               "expected": dict({"ok": False, "code": code}, **expected)}
        if version is not None:
            vec["move_spec_version"] = version
        vectors.append(vec)

    # -- accepts ---------------------------------------------------------
    for tag, e in zip(("shortest", "median", "longest"), picks):
        cid = sac_ids[e["training_id"]]
        moves = stable_by_id[e["training_id"]]["moves"]
        assert moves == e["moves"] + list(STABLE_TRAINING_SUFFIX)
        accept("accept-stable-%s-%s" % (tag, cid), cid, moves)
    accept("accept-stable-canon-xy", "golden-stable-xy",
           STABLE_CANON_SUFFIX[((1,), (2,))])
    accept("accept-stable-canon-yx", "golden-stable-yx", [15, 15])

    # A genuine rank-3 detour: stabilize, conjugate the new relator by x
    # and back, then destabilize r2, r1, r0.
    conj = {(row["relator"], row["conjugator"]): row["id"]
            for row in stable_core.MOVE_TABLE
            if row["category"] == "conjugation"}
    destab = {row["relator"]: row["id"] for row in stable_core.MOVE_TABLE
              if row["category"] == "destabilize"}
    rank3 = [14, conj[(2, 1)], conj[(2, -1)],
             destab[2], destab[1], destab[0]]
    assert rank3 == [14, 161, 162, 17, 16, 15], rank3
    accept("accept-stable-rank3-detour", "golden-stable-xy", rank3)

    # -- rejects ---------------------------------------------------------
    short = picks[0]
    short_sac = sac_ids[short["training_id"]]
    reject("not-target-stable-missing-destabilizations", short_sac,
           short["moves"], "E_NOT_TARGET", final_shape=[1, 1])
    reject("not-target-stable-empty-path", short_sac, [], "E_NOT_TARGET")
    reject("move-not-applicable-relator-out-of-rank", "golden-stable-xy",
           [16, 1], "E_MOVE_NOT_APPLICABLE", move_index=1,
           reason="relator_out_of_rank")
    reject("move-not-applicable-generator-out-of-rank", "golden-stable-xy",
           [16, 8], "E_MOVE_NOT_APPLICABLE", move_index=1,
           reason="generator_out_of_rank")
    reject("move-not-applicable-max-rank-exceeded", "golden-stable-xy",
           [14] * (stable_core.MAX_RANK - 1), "E_MOVE_NOT_APPLICABLE",
           move_index=stable_core.MAX_RANK - 2, reason="max_rank_exceeded")
    reject("move-not-applicable-destabilize-precondition-long-relator",
           "golden-stable-pump", [15], "E_MOVE_NOT_APPLICABLE",
           move_index=0, reason="destabilize_precondition")
    reject("move-not-applicable-destabilize-precondition-inverted",
           "golden-stable-xy", [0, 15], "E_MOVE_NOT_APPLICABLE",
           move_index=1, reason="destabilize_precondition")
    reject("move-not-applicable-destabilize-precondition-shared-generator",
           "golden-stable-xy", [4, 15], "E_MOVE_NOT_APPLICABLE",
           move_index=1, reason="destabilize_precondition")
    reject("bad-move-id-stable-257", "golden-stable-xy",
           [stable_core.NUM_MOVES], "E_BAD_MOVE_ID", move_index=0,
           move=stable_core.NUM_MOVES)
    reject("spec-mismatch-ac-version-on-stable-challenge", short_sac,
           stable_by_id[short["training_id"]]["moves"], "E_SPEC_MISMATCH",
           version=core.MOVE_SPEC_VERSION, move_index=None,
           expected=stable_core.MOVE_SPEC_VERSION)
    # ...and the other direction, on an ac-r2-v1 challenge.
    ac_short = challenges[short["training_id"]]
    v = core.verify(ac_short, short["moves"],
                    stable_core.MOVE_SPEC_VERSION, LIMITS)
    assert v["code"] == "E_SPEC_MISMATCH", v
    vectors.append({
        "name": "spec-mismatch-stable-version-on-ac-challenge",
        "challenge_id": short["training_id"],
        "move_spec_version": stable_core.MOVE_SPEC_VERSION,
        "moves": short["moves"],
        "expected": {"ok": False, "code": "E_SPEC_MISMATCH",
                     "move_index": None,
                     "expected": core.MOVE_SPEC_VERSION}})

    # -- submission vectors ---------------------------------------------
    ac_line = short["training_id"] + ": " + json.dumps(short["moves"])
    sac_entry = stable_by_id[short["training_id"]]
    sac_line = short_sac + ": " + json.dumps(sac_entry["moves"])
    sac_hash = sac_verify(short_sac, sac_entry["moves"])["certificate_hash"]
    sub_vectors += [
        {"name": "sub-accept-mixed-tracks",
         "raw": "# Both problems\n" + ac_line + " # AC\n" + sac_line + " # Stable AC\n",
         "expected": {"accepted": True, "results": [
             {"ok": True, "challenge_id": short["training_id"],
              "certificate_hash": short["certificate_hash"]},
             {"ok": True, "challenge_id": short_sac,
              "certificate_hash": sac_hash}]}},
        {"name": "sub-stable-comment-does-not-select-ac-spec",
         "raw": sac_line + " # move_spec_version: ac-r2-v1\n",
         "expected": {"accepted": True, "results": [
             {"ok": True, "challenge_id": short_sac,
              "certificate_hash": sac_hash}]}},
        {"name": "sub-duplicate-mixed-problems-select-independently",
         "raw": ac_line + "\n" + short_sac + ": []\n"
                + short["training_id"] + ": [14]\n" + sac_line + "\n"
                + short_sac + ": [257]\n",
         "expected": {"accepted": True, "results": [
             {"ok": True, "challenge_id": short["training_id"],
              "certificate_hash": short["certificate_hash"]},
             {"ok": False, "challenge_id": short_sac, "code": "E_NOT_TARGET"},
             {"ok": False, "challenge_id": short["training_id"],
              "skipped": True, "reason": "already_verified"},
             {"ok": True, "challenge_id": short_sac, "certificate_hash": sac_hash},
             {"ok": False, "challenge_id": short_sac,
              "skipped": True, "reason": "already_verified"}]}},
    ]

    move_specs = move_spec_headers()
    assert specs.check_move_specs(move_specs) == []
    return {
        "format": "acms-golden-v2",
        "move_specs": move_specs,
        "manifest_hash": manifest["manifest_hash"],
        "default_limits": LIMITS,
        "note": doc["note"],
        "challenges": challenges,
        "verify_vectors": vectors,
        "submission_vectors": sub_vectors,
    }


def leak_check(path, private_ids):
    """Raw-text scan of the emitted manifest (belt, braces, and a rope)."""
    text = path.read_text(encoding="utf-8")
    for token in BANNED_TOKENS:
        assert token not in text, "banned token %r in %s" % (token, path.name)
    # Every private id (MS-*, AUTH-*, INTL-*, ACP-*) contains an uppercase
    # letter, and the manifest is lowercase ASCII apart from the ISO-8601
    # freeze_date, so no id can occur as a substring.  Both halves are
    # asserted, plus a direct scan for any hypothetical all-lowercase id.
    freeze_date = json.loads(text)["freeze_date"]
    scrubbed = text.replace(freeze_date, "") if freeze_date is not None else text
    hit = re.search(r"[A-Z]", scrubbed)
    assert hit is None, "unexpected uppercase in %s at offset %d" % (
        path.name, hit.start() if hit else -1)
    for pid in private_ids:
        if pid == pid.lower():
            assert pid not in text, "private id %r in %s" % (pid, path.name)
    print("leak check: %s clean (%d banned tokens, %d private ids)"
          % (path.name, len(BANNED_TOKENS), len(private_ids)))


def write_private(rows, sources):
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    tsv = PRIVATE_DIR / "challenge_map_private.tsv"
    with open(tsv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(PRIVATE_MAP_FIELDS),
                                delimiter="\t")
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "challenge_id": r["challenge_id"], "master_id": r["id"],
                "public_id": r["public_id"], "pool": r["pool"],
                "tier": r["tier"], "tier_basis": r["tier_basis"],
                "total_length": r["total_length"],
                "in_draw": "true" if r["in_draw"] else "false",
                "ms1190_status": r["ms1190_status"],
                "ms1190_seq": r["ms1190_seq"]})
    assert len({r["challenge_id"] for r in rows}) == len(rows)
    assert len({r["id"] for r in rows}) == len(rows)
    print("wrote %s (%d rows)" % (tsv.relative_to(REPO), len(rows)))

    tiers = dict(collections.Counter(r["tier"] for r in rows))
    assert tiers == EXPECTED_TIERS, tiers
    added = sorted(r["id"] for r in rows if not r["in_draw"])
    assert len(added) == EXPECTED_ADDED_OPEN, len(added)
    excluded = sorted(sources["excluded_certified_overlap_ids"])
    assert len(excluded) == EXPECTED_OVERLAP_BY_STATUS["certified"]
    stats = {
        "scored_pool_rows": len(rows),
        "tier_counts": tiers,
        "pool_counts": dict(collections.Counter(r["pool"] for r in rows)),
        "tier_basis_counts": dict(
            collections.Counter(r["tier_basis"] for r in rows)),
        "ms1190_status_counts": dict(
            collections.Counter(r["ms1190_status"] or "not_ms1190"
                                for r in rows)),
        "in_draw_counts": dict(
            collections.Counter("true" if r["in_draw"] else "false"
                                for r in rows)),
        "excluded_certified_overlap": {
            "count": len(excluded), "master_ids": excluded},
        "added_open_not_in_draw": {
            "count": len(added), "master_ids": added},
    }
    path = PRIVATE_DIR / "pool_stats.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % path.relative_to(REPO))


def render_yaml(manifest, competition_state):
    """Render derived metadata without reading or writing a local YAML file."""
    assert manifest["freeze_date"] == competition_state["freeze_date"], \
        "manifest freeze date differs from competition state"
    spec_lines = []
    for entry in manifest["move_specs"]:
        spec_lines.append("  - version: %s\n    hash: %s\n    file: tools/verifier/data/%s\n"
                          "    target_relators: %s\n    max_rank: %d\n    id_prefix: %s\n"
                          % (entry["move_spec_version"], json.dumps(entry["move_spec_hash"]),
                             entry["file"], json.dumps(entry["target_relators"]),
                             entry["max_rank"], entry["id_prefix"]))
    specs_yaml = "".join(spec_lines)
    return f"""\
id: acms
name: "The Andrews–Curtis Conjecture (ACC) Challenge"
organizer: sairmath
status: {competition_state['status']}
task_type: mathematical_discovery
submission_artifact: submission.txt
submission_format: "Discovery: UTF-8 TXT; one challenge_id: [comma-separated moves] per line; blank lines and full-line or trailing # comments are ignored; ac- IDs select AC moves 0-13 and sac- IDs select stable AC moves 0-256"
verifier: "Discovery Track: Python, competition/tools/verifier (standard library only), acms-verify {__version__}"
primary_metric: leaderboard_score
scoring_unit: team_challenge
scoring_formula: "2^(1-k) per team tied at the current shortest accepted length, where k is the number of distinct tied teams; 0 otherwise"
tracks:
  - id: discovery
    name: Discovery Track
    overview: rules/discovery.md
    opens: {json.dumps(competition_state['announced_dates']['discovery'])}
    opens_at: {json.dumps(competition_state['submissions_open'])}
    objective: "Find short verified trivializations of the published presentations"
    leaderboards: independent_per_problem
    problems:
      - id: ac
        name: AC
        file: problems/ac.jsonl
        id_prefix: ac-
        move_spec_version: ac-r2-v1
        target: "The ordered pair (x, y), at fixed rank 2"
      - id: stable_ac
        name: Stable AC
        file: problems/stable_ac.jsonl
        id_prefix: sac-
        move_spec_version: sac-r8-v1
        target: "The empty presentation, with current rank at most 8"
  - id: proof
    name: Proof Track
    overview: rules/proof.md
    opens: {json.dumps(competition_state['announced_dates']['prove'])}
    opens_at: {json.dumps(competition_state['prove_submissions_open'])}
    statement: rules/proof.md
    submission_format: "Conjecture, claim type, and description required; complete argument in description, PDF or paper, GitHub at a fixed commit, or arXiv at a fixed version"
    visibility: public
    versions: immutable
    review: "Community peer review through public versions and comments, including Lean submissions; organizers may assess selected claims for competition recognition"
    credit: "Earliest eligible complete correct version, with references and contributions recorded; see rules/proof.md#priority-and-credit"
    leaderboard_points: false
    problems:
      - id: ac
        name: AC
        conjecture: AC.Conjecture
        claims: [proof, disproof]
      - id: stable_ac
        name: Stable AC
        conjecture: AC.StableConjecture
        claims: [proof, disproof]
move_specs:
{specs_yaml}announced_dates: {json.dumps(competition_state['announced_dates'])}
manifest_hash: "{manifest['manifest_hash']}"
freeze_date: {json.dumps(competition_state['freeze_date'])}
freeze_commit: {json.dumps(competition_state['freeze_commit'])}
registration_opens: {json.dumps(competition_state['registration_opens'])}
submissions_open: {json.dumps(competition_state['submissions_open'])}
prove_submissions_open: {json.dumps(competition_state['prove_submissions_open'])}
submission_deadline: {json.dumps(competition_state['submission_deadline'])}
challenge_count: {manifest['challenge_count']}
presentation_count: {manifest['presentation_count']}
challenge_policy: "Discovery Track: 10,115 balanced presentations for each of the AC and Stable AC problems, with 20,230 separately scored challenge records; base_score 1 each. Internal difficulty labels and direct source-ID mappings are omitted; public MS metadata and relators may reveal origins"
overview: rules/overview.md
evaluation: rules/discovery.md
manifest: tools/verifier/data/manifest.json
"""


def write_yaml(manifest, competition_state=None):
    if competition_state is None:
        competition_state = load_competition_state()
    path = REPO / "competition" / "competition.yaml"
    path.write_text(render_yaml(manifest, competition_state), encoding="utf-8")
    print("wrote %s" % path.relative_to(REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--metadata-only", action="store_true",
                        help="generate only the ignored competition.yaml from existing manifest and state")
    args = parser.parse_args()
    competition_state = load_competition_state()
    if args.metadata_only:
        manifest = json.loads((VERIFIER_DATA_DIR / "manifest.json").read_text())
        write_yaml(manifest, competition_state)
        return
    items = load_items()
    ac_hash = specs.SPECS[core.MOVE_SPEC_VERSION].move_spec_hash
    sac_hash = specs.SPECS[stable_core.MOVE_SPEC_VERSION].move_spec_hash
    assert ac_hash == canon.move_spec_hash(core.MOVE_TABLE)
    assert sac_hash == canon.move_spec_hash(stable_core.MOVE_TABLE)

    # 1. frozen artifacts: regenerate and refuse to change them.
    move_spec = build_move_spec(ac_hash)
    training = build_training(items, ac_hash)
    stable_move_spec = build_stable_move_spec(sac_hash)
    stable_training = build_stable_training(training, sac_hash)
    freeze_guard("move_spec.json", move_spec)
    freeze_guard("training_424.json", training)
    freeze_guard("stable_move_spec.json", stable_move_spec,
                 create_if_missing=True)
    freeze_guard("stable_training_424.json", stable_training,
                 create_if_missing=True)
    print("freeze guard: move_spec.json, training_424.json, "
          "stable_move_spec.json and stable_training_424.json byte-identical")

    # 2. the scored pool, twice: once per Discovery problem.
    rows, sources = load_pool(items, training)
    rows = assign_ids(rows)
    manifest = build_manifest_v3(rows, competition_state)
    golden = build_golden_v3(manifest, training, stable_training)

    dump(VERIFIER_DATA_DIR / "manifest.json", manifest)
    dump(VERIFIER_DATA_DIR / "move_spec.json", move_spec)
    dump(EXAMPLES_DIR / "training_424.json", training)
    dump(VERIFIER_DATA_DIR / "stable_move_spec.json", stable_move_spec)
    dump(EXAMPLES_DIR / "stable_training_424.json", stable_training)
    dump(VERIFIER_DATA_DIR / "golden_vectors.json", golden)

    write_problems(manifest, PROBLEMS_DIR)

    # 3. the MS-1190 denominator (no challenge_id / scored columns).
    train_seq, ti = {}, 0
    for seq, it in enumerate(items, 1):
        if it.get("path"):
            ti += 1
            train_seq[seq] = "ms-train-%04d" % ti
    meta_rows = ms1190_rows(items, train_seq)
    csv_path = VERIFIER_DATA_DIR / "ms1190_metadata.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()))
        writer.writeheader()
        writer.writerows(meta_rows)
    print("wrote %s (%d rows)" % (csv_path.relative_to(REPO), len(meta_rows)))

    write_yaml(manifest, competition_state)

    # 4. private side tables, then prove the public manifest is clean.
    write_private(rows, sources)
    private_ids = sorted({r["id"] for r in rows}
                         | {r["public_id"] for r in rows}
                         | set(sources["excluded_certified_overlap_ids"]))
    leak_check(VERIFIER_DATA_DIR / "manifest.json", private_ids)

    print("move_spec_hash (%s) = %s" % (core.MOVE_SPEC_VERSION, ac_hash))
    print("move_spec_hash (%s) = %s"
          % (stable_core.MOVE_SPEC_VERSION, sac_hash))
    print("manifest_hash  =", manifest["manifest_hash"])
    print("challenges: %d scored over %d presentations x %d Discovery problems, "
          "base_score 1 each"
          % (manifest["challenge_count"], manifest["presentation_count"],
             len(manifest["move_specs"])))


if __name__ == "__main__":
    main()
