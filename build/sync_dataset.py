#!/usr/bin/env python3
"""Distil the frozen ACC challenge pool out of the SAIR dataset release.

Upstream (private, outside this repo) is
``sair_dataset/release/``:

  master_private.jsonl          47236 canonical presentations, all pools
  competition_10k_proposed.tsv  the 10000-row competition draw
  id_map_private.tsv            private master_id <-> public ACP id

This script reads those three files once and writes the two committed
build inputs that ``build/build_manifest_v2.py`` consumes:

  build/data/scored_pool_source.jsonl   the 10115 scored-pool rows
  build/data/SOURCES.json               upstream digests + pinned counts

Pool definition (DESIGN.md §2.1 as amended for the v2 pool):

    scored pool = the 10000-row draw
                - the 89 draw rows that are MS-1190 instances with a
                  public replayable certificate (the training 424)
                + the 204 MS-1190 *open* instances the draw missed,

so that the full MS-1190 open set (550) is scored and nothing with a
published certificate is.

Matching between the draw and MS-1190 is by canonical relator pair —
lex-min over all rotations of each word and of its inverse, then the
pair sorted.  (n, w) does not survive the upstream canonicalization, so
it cannot be used as the join key.

Every figure below is hard-asserted: any upstream drift fails the sync
loudly instead of silently reshaping the frozen pool.

Deterministic: no timestamps, no randomness; identical inputs give
byte-identical outputs.
"""

import argparse
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import core  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_manifest import load_items, ms_initial  # noqa: E402

DEFAULT_RELEASE = REPO.parent / "sair_dataset" / "release"
DATA_DIR = REPO / "build" / "data"
POOL_PATH = DATA_DIR / "scored_pool_source.jsonl"
SOURCES_PATH = DATA_DIR / "SOURCES.json"

# Fixed, not "now": the sync must be byte-for-byte reproducible.
SYNC_DATE = "2026-09-03"

# Upstream row counts (data rows, excluding TSV headers).
EXPECTED_MASTER_ROWS = 47236
EXPECTED_DRAW_ROWS = 10000
EXPECTED_ID_MAP_ROWS = 47236

# MS-1190 denominator, from reference/index.html (build_manifest.py).
EXPECTED_MS_STATUS = {"certified": 424, "uncertified": 216, "open": 550}

# draw n MS-1190, by MS status at freeze.
EXPECTED_OVERLAP = 618
EXPECTED_OVERLAP_BY_STATUS = {"open": 346, "uncertified": 183,
                              "certified": 89}
# open MS-1190 instances the draw missed and that we add back.
EXPECTED_ADDED_OPEN = 204

EXPECTED_POOL_ROWS = 10115
EXPECTED_TIERS = {"T0_warmup": 163, "T1_easy": 4366, "T2_medium": 1769,
                  "T3_hard_solvable": 1113, "T4_frontier": 1695,
                  "T5_moonshot": 1009}
EXPECTED_MAX_TOTAL_LENGTH = 40

# Quoted from sair_dataset/scripts/compile_master.py (upstream is itself
# deterministic; these seeds fix public ids and row order there).
UPSTREAM_SEEDS = {
    "PUBLIC_ID_SEED": 20260819,
    "NEW_ID_SEED": 20260820,
    "SHUFFLE_SEED": 20260819,
}

POOL_FIELDS = ("id", "public_id", "pool", "tier", "tier_basis", "relators",
               "relators_int", "total_length", "in_draw", "ms1190_status",
               "ms1190_seq")


def canon_word(word):
    """Lex-min over all rotations of ``word`` and of its inverse."""
    best = None
    for cand in (tuple(word), core.invert(tuple(word))):
        for i in range(len(cand)):
            rot = cand[i:] + cand[:i]
            if best is None or rot < best:
                best = rot
    return best


def canon_pair(relators):
    """Order-insensitive canonical key of a two-relator presentation.

    Matching only: any consistent total order works, and the key is
    deliberately NOT part of any hash or public artifact.
    """
    return tuple(sorted(canon_word(w) for w in relators))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def ms1190_reference():
    """``canonical pair -> (seq, status_at_freeze)`` for all 1190 MS rows."""
    ref = {}
    counts = collections.Counter()
    for seq, it in enumerate(load_items(), 1):
        status = {("trivial", True): "certified",
                  ("trivial", False): "uncertified",
                  ("unsolved", False): "open"}[
                      (it["status"], bool(it.get("path")))]
        key = canon_pair(ms_initial(it["n"], it["wv"]))
        assert key not in ref, "duplicate MS-1190 canonical pair at %d" % seq
        ref[key] = (seq, status)
        counts[status] += 1
    assert len(ref) == 1190, len(ref)
    assert dict(counts) == EXPECTED_MS_STATUS, dict(counts)
    return ref


def read_tsv_column(path, column, expected_rows):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    assert len(rows) == expected_rows, (path.name, len(rows))
    return rows, [r[column] for r in rows]


def load_upstream(release):
    """Stream master once, keeping only draw and MS-1190 rows."""
    draw_rows, draw_ids = read_tsv_column(
        release / "competition_10k_proposed.tsv", "master_id",
        EXPECTED_DRAW_ROWS)
    draw = set(draw_ids)
    assert len(draw) == EXPECTED_DRAW_ROWS, len(draw)

    map_rows, _ = read_tsv_column(release / "id_map_private.tsv",
                                  "master_id", EXPECTED_ID_MAP_ROWS)
    public_id = {r["master_id"]: r["public_id"] for r in map_rows}
    assert len(public_id) == EXPECTED_ID_MAP_ROWS, len(public_id)

    ref = ms1190_reference()
    kept = {}
    ms_match = {}
    total = 0
    with open(release / "master_private.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            total += 1
            row = json.loads(line)
            in_ms = bool(row["provenance"].get("in_ms1190"))
            if not in_ms and row["id"] not in draw:
                continue
            key = canon_pair(row["relators_int"])
            row["_key"] = key
            if in_ms:
                assert key in ref, "in_ms1190 row %s matches no MS-1190 " \
                    "canonical pair" % row["id"]
                assert key not in ms_match, "two in_ms1190 rows share a " \
                    "canonical pair: %s" % row["id"]
                ms_match[key] = row["id"]
            kept[row["id"]] = row
    assert total == EXPECTED_MASTER_ROWS, total
    assert len(ms_match) == 1190, len(ms_match)
    assert set(ms_match) == set(ref), "MS-1190 match is not 1:1"
    return draw, public_id, ref, ms_match, kept


def build_pool(draw, ref, ms_match, kept):
    """The 10115 scored rows: draw - certified overlap + missed open."""
    draw_pool = [kept[i] for i in sorted(draw)]

    overlap = [r for r in draw_pool if r["_key"] in ref]
    assert len(overlap) == EXPECTED_OVERLAP, len(overlap)
    by_status = collections.Counter(ref[r["_key"]][1] for r in overlap)
    assert dict(by_status) == EXPECTED_OVERLAP_BY_STATUS, dict(by_status)
    # Every draw row that hits an MS-1190 pair IS the MS-1190 row, so the
    # exclusion/addition below is unambiguous.
    for r in overlap:
        assert ms_match[r["_key"]] == r["id"], r["id"]

    drop = {r["id"] for r in overlap if ref[r["_key"]][1] == "certified"}
    assert len(drop) == EXPECTED_OVERLAP_BY_STATUS["certified"], len(drop)

    added = [kept[ms_match[k]] for k, (_, st) in sorted(
        ref.items(), key=lambda kv: kv[1][0])
        if st == "open" and ms_match[k] not in draw]
    assert len(added) == EXPECTED_ADDED_OPEN, len(added)

    pool = [r for r in draw_pool if r["id"] not in drop] + added
    pool.sort(key=lambda r: r["id"])
    assert len(pool) == EXPECTED_POOL_ROWS, len(pool)

    tiers = collections.Counter(r["tier"] for r in pool)
    assert dict(tiers) == EXPECTED_TIERS, dict(tiers)
    assert max(r["total_length"] for r in pool) == EXPECTED_MAX_TOTAL_LENGTH
    keys = [r["_key"] for r in pool]
    assert len(set(keys)) == len(keys), "duplicate canonical pair in pool"

    keyset = set(keys)
    open_keys = {k for k, (_, st) in ref.items() if st == "open"}
    cert_keys = {k for k, (_, st) in ref.items() if st == "certified"}
    unc_keys = {k for k, (_, st) in ref.items() if st == "uncertified"}
    assert open_keys <= keyset, "an open MS-1190 instance is unscored"
    assert not (cert_keys & keyset), "a certified MS-1190 instance is scored"
    assert len(unc_keys & keyset) == \
        EXPECTED_OVERLAP_BY_STATUS["uncertified"], len(unc_keys & keyset)

    for r in pool:
        for w in r["relators_int"]:
            assert list(core.free_reduce(w)) == w, r["id"]
            assert all(a in (-2, -1, 1, 2) for a in w), r["id"]
        assert sum(len(w) for w in r["relators_int"]) == r["total_length"], \
            r["id"]
    return pool, drop, [r["id"] for r in added]


def emit(pool, public_id, ref, draw):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for r in pool:
        seq, status = ref.get(r["_key"], ("", ""))
        lines.append(json.dumps({
            "id": r["id"],
            "public_id": public_id[r["id"]],
            "pool": r["pool"],
            "tier": r["tier"],
            "tier_basis": r["tier_basis"],
            "relators": r["relators"],
            "relators_int": r["relators_int"],
            "total_length": r["total_length"],
            "in_draw": r["id"] in draw,
            "ms1190_status": status,
            "ms1190_seq": seq,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    POOL_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d rows, %d bytes)"
          % (POOL_PATH.relative_to(REPO), len(lines), POOL_PATH.stat().st_size))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--release", default=str(DEFAULT_RELEASE),
                    help="path to the sair_dataset release directory "
                         "(default: %(default)s)")
    args = ap.parse_args()
    release = Path(args.release).resolve()

    draw, public_id, ref, ms_match, kept = load_upstream(release)
    pool, dropped, added = build_pool(draw, ref, ms_match, kept)
    emit(pool, public_id, ref, draw)

    sources = {
        "sync_date": SYNC_DATE,
        "release_dir": release.name,
        "note": ("Upstream is deterministic: sair_dataset/scripts/"
                 "compile_master.py fixes public ids and row order with "
                 "PUBLIC_ID_SEED / NEW_ID_SEED / SHUFFLE_SEED, so re-running "
                 "the upstream compiler reproduces these digests.  The pool "
                 "below is derived from them by build/sync_dataset.py and "
                 "consumed by build/build_manifest_v2.py; neither the master "
                 "ids nor the ACP public ids ever reach the public tree."),
        "upstream_seeds": UPSTREAM_SEEDS,
        "files": {
            "master_private.jsonl": {
                "sha256": sha256_file(release / "master_private.jsonl"),
                "rows": EXPECTED_MASTER_ROWS},
            "competition_10k_proposed.tsv": {
                "sha256": sha256_file(release / "competition_10k_proposed.tsv"),
                "rows": EXPECTED_DRAW_ROWS},
            "id_map_private.tsv": {
                "sha256": sha256_file(release / "id_map_private.tsv"),
                "rows": EXPECTED_ID_MAP_ROWS},
        },
        "ms1190_status_counts": EXPECTED_MS_STATUS,
        "draw_ms1190_overlap": EXPECTED_OVERLAP,
        "draw_ms1190_overlap_by_status": EXPECTED_OVERLAP_BY_STATUS,
        "excluded_certified_overlap": len(dropped),
        # The 89 dropped rows are by definition absent from the pool file,
        # so record them here for build/private/pool_stats.json.
        "excluded_certified_overlap_ids": sorted(dropped),
        "added_open_not_in_draw": len(added),
        "scored_pool_rows": EXPECTED_POOL_ROWS,
        "tier_counts": EXPECTED_TIERS,
        "max_total_relator_length": EXPECTED_MAX_TOTAL_LENGTH,
    }
    with open(SOURCES_PATH, "w", encoding="utf-8") as fh:
        json.dump(sources, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s" % SOURCES_PATH.relative_to(REPO))
    print("pool: %d rows = %d draw - %d certified overlap + %d open added"
          % (len(pool), EXPECTED_DRAW_ROWS, len(dropped), len(added)))


if __name__ == "__main__":
    main()
