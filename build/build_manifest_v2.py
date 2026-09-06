#!/usr/bin/env python3
"""Generate the frozen ACC data artifacts (manifest version ``acms-v2``).

This is the sole generator for everything under
``competition/challenges/`` and for ``competition/competition.yaml``.
Run ``build/sync_dataset.py`` first: the scored pool comes from
``build/data/`` (distilled from the private SAIR dataset release), not
from ``reference/index.html`` any more.  ``reference/index.html`` is
still the source of the MS-1190 denominator and of the 424 published
trivializations, so the MS-only builders are imported from
``build/build_manifest.py`` unchanged.

Outputs:

  competition/challenges/manifest.json        10115 scored challenges
  competition/challenges/move_spec.json       FROZEN, byte-identity checked
  competition/challenges/training_424.json    FROZEN, byte-identity checked
  competition/challenges/ms1190_metadata.csv  the MS-1190 denominator
  competition/challenges/golden_vectors.json  conformance vectors
  competition/competition.yaml                machine-readable metadata
  build/private/challenge_map_private.tsv     NEVER published
  build/private/pool_stats.json               NEVER published

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

from acms_verify import __version__, canon, core  # noqa: E402

from build_manifest import (  # noqa: E402
    GENERATORS, LIMITS, TARGET, build_golden, build_move_spec,
    build_training, dump, load_items, ms_initial)
from sync_dataset import (  # noqa: E402
    DATA_DIR, EXPECTED_ADDED_OPEN, EXPECTED_MS_STATUS,
    EXPECTED_OVERLAP_BY_STATUS, EXPECTED_POOL_ROWS, EXPECTED_TIERS,
    POOL_PATH, SOURCES_PATH, canon_pair)

MANIFEST_VERSION = "acms-v2"
COMPETITION = "acms"
CHALLENGE_ID_SEED = 20260903
CHALLENGE_ID_FORMAT = "ac-v1-%05d"

CHALLENGES_DIR = REPO / "competition" / "challenges"
PRIVATE_DIR = REPO / "build" / "private"
COMPETITION_STATE_PATH = REPO / "build" / "competition_state.json"
SCHEDULE_FIELDS = ("freeze_date", "registration_opens", "submissions_open",
                   "submission_deadline", "certificate_release")

#: Exactly the keys a public challenge record may carry (O-4: no
#: difficulty, family, or provenance signal reaches contestants).
CHALLENGE_KEYS = {"challenge_id", "generators", "initial_relators",
                  "target_relators", "move_spec_version", "scored",
                  "base_score", "instance_hash", "freeze_date"}

#: Substrings that must not occur in the emitted manifest.  None of them
#: can appear legitimately: the manifest is lowercase ASCII JSON whose
#: only string values are the nine keys above, "x"/"y", "ac-r2-v1",
#: "acms"/"acms-v2", "sha256:"-prefixed lowercase hex, the ac-v1 ids and
#: the freeze date.
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
    expected = {"status", "freeze_commit", *SCHEDULE_FIELDS}
    if not isinstance(state, dict) or set(state) != expected:
        raise ValueError("competition state must contain exactly %s" %
                         ", ".join(sorted(expected)))
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


def freeze_guard(name, obj):
    """Abort unless a frozen artifact regenerates byte for byte."""
    path = CHALLENGES_DIR / name
    generated = serialize(obj).encode("utf-8")
    on_disk = path.read_bytes()
    assert generated == on_disk, (
        "FROZEN ARTIFACT DRIFT: %s would change (%d -> %d bytes).  "
        "move_spec.json and training_424.json are frozen; refusing."
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
    """Seeded shuffle of the master-id order, then ac-v1-NNNNN in order."""
    assert canon._ID_RE.match(CHALLENGE_ID_FORMAT % 1), CHALLENGE_ID_FORMAT
    ordered = sorted(rows, key=lambda r: r["id"])
    random.Random(CHALLENGE_ID_SEED).shuffle(ordered)
    for seq, row in enumerate(ordered, 1):
        row["challenge_id"] = CHALLENGE_ID_FORMAT % seq
    ordered.sort(key=lambda r: r["challenge_id"])
    assert [r["challenge_id"] for r in ordered] == \
        [CHALLENGE_ID_FORMAT % i for i in range(1, len(ordered) + 1)]
    return ordered


def build_manifest_v2(rows, move_spec_hash, competition_state=None):
    if competition_state is None:
        competition_state = load_competition_state()
    freeze_date = competition_state["freeze_date"]
    challenges = []
    for row in rows:
        initial = [list(w) for w in row["relators_int"]]
        challenges.append({
            "challenge_id": row["challenge_id"],
            "generators": GENERATORS,
            "initial_relators": initial,
            "target_relators": TARGET,
            "move_spec_version": core.MOVE_SPEC_VERSION,
            "scored": True,
            "base_score": 1,
            "instance_hash": canon.instance_hash(
                row["challenge_id"], GENERATORS, initial, TARGET,
                core.MOVE_SPEC_VERSION, move_spec_hash),
            "freeze_date": freeze_date,
        })
    for c in challenges:
        assert set(c) == CHALLENGE_KEYS, sorted(set(c) ^ CHALLENGE_KEYS)
    return {
        "manifest_version": MANIFEST_VERSION,
        "competition": COMPETITION,
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "manifest_hash": canon.manifest_hash(
            [c["instance_hash"] for c in challenges]),
        "freeze_date": freeze_date,
        "generators": GENERATORS,
        "target_relators": TARGET,
        "limits": LIMITS,
        "challenge_count": len(challenges),
        "challenges": challenges,
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


def write_yaml(manifest, move_spec_hash, competition_state=None):
    if competition_state is None:
        competition_state = load_competition_state()
    assert manifest["freeze_date"] == competition_state["freeze_date"], \
        "manifest freeze date differs from competition state"
    path = REPO / "competition" / "competition.yaml"
    path.write_text(f"""\
id: acms
name: "Andrews–Curtis Conjecture Challenge (ACC)"
organizer: sairmath
status: {competition_state['status']}
task_type: mathematical_discovery
submission_track: discovery
submission_artifact: submission.json
submission_format: "Discovery Track: JSON; solutions[] of {{challenge_id, moves[]}} where moves are atomic AC move ids 0-13"
verifier: "Discovery Track: Python, competition/tools/verifier (standard library only), acms-verify {__version__}"
scoring_track: discovery
primary_metric: leaderboard_score
scoring_unit: team_challenge
scoring_formula: "V_i * 2^(1-k_i) for teams at the current shortest length, 0 otherwise"
tracks:
  - id: discovery
    name: Discovery Track
    objective: "Find short verified AC move sequences for the published challenge pool"
  - id: prove
    name: Prove Track
    claims: [proof, disproof]
    statement: rules/statement.md
    submission_format: "Claim type and description required; complete argument in description, PDF or paper, GitHub at a fixed commit, or arXiv at a fixed version"
    visibility: public
    versions: immutable
    review: "Public comments; final mathematical determination by reviewers; Lean does not bypass review"
    credit: "Earliest complete correct version, with references and contributions recorded; see rules/evaluation.md"
    leaderboard_points: false
move_spec_version: {core.MOVE_SPEC_VERSION}
move_spec_hash: "{move_spec_hash}"
manifest_hash: "{manifest['manifest_hash']}"
freeze_date: {json.dumps(competition_state['freeze_date'])}
freeze_commit: {json.dumps(competition_state['freeze_commit'])}
registration_opens: {json.dumps(competition_state['registration_opens'])}
submissions_open: {json.dumps(competition_state['submissions_open'])}
submission_deadline: {json.dumps(competition_state['submission_deadline'])}
certificate_release: {json.dumps(competition_state['certificate_release'])}
challenge_count: {manifest['challenge_count']}
challenge_policy: "Discovery Track: 10,115 balanced presentations of the trivial group; base_score 1 each. Internal difficulty labels and direct source-ID mappings are omitted; public MS metadata and relators may reveal origins"
overview: rules/overview.md
evaluation: rules/evaluation.md
manifest: challenges/manifest.json
move_spec: challenges/move_spec.json
""", encoding="utf-8")
    print("wrote %s" % path.relative_to(REPO))


def main():
    competition_state = load_competition_state()
    items = load_items()
    move_spec_hash = canon.move_spec_hash(core.MOVE_TABLE)

    # 1. frozen artifacts: regenerate and refuse to change them.
    move_spec = build_move_spec(move_spec_hash)
    training = build_training(items, move_spec_hash)
    freeze_guard("move_spec.json", move_spec)
    freeze_guard("training_424.json", training)
    print("freeze guard: move_spec.json and training_424.json byte-identical")

    # 2. the scored pool.
    rows, sources = load_pool(items, training)
    rows = assign_ids(rows)
    manifest = build_manifest_v2(rows, move_spec_hash, competition_state)
    golden = build_golden(manifest, training, move_spec_hash)

    dump(CHALLENGES_DIR / "manifest.json", manifest)
    dump(CHALLENGES_DIR / "move_spec.json", move_spec)
    dump(CHALLENGES_DIR / "training_424.json", training)
    dump(CHALLENGES_DIR / "golden_vectors.json", golden)

    # 3. the MS-1190 denominator (no challenge_id / scored columns).
    train_seq, ti = {}, 0
    for seq, it in enumerate(items, 1):
        if it.get("path"):
            ti += 1
            train_seq[seq] = "ms-train-%04d" % ti
    meta_rows = ms1190_rows(items, train_seq)
    csv_path = CHALLENGES_DIR / "ms1190_metadata.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()))
        writer.writeheader()
        writer.writerows(meta_rows)
    print("wrote %s (%d rows)" % (csv_path.relative_to(REPO), len(meta_rows)))

    write_yaml(manifest, move_spec_hash, competition_state)

    # 4. private side tables, then prove the public manifest is clean.
    write_private(rows, sources)
    private_ids = sorted({r["id"] for r in rows}
                         | {r["public_id"] for r in rows}
                         | set(sources["excluded_certified_overlap_ids"]))
    leak_check(CHALLENGES_DIR / "manifest.json", private_ids)

    print("move_spec_hash =", move_spec_hash)
    print("manifest_hash  =", manifest["manifest_hash"])
    print("challenges: %d scored, base_score 1 each"
          % manifest["challenge_count"])


if __name__ == "__main__":
    main()
