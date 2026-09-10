#!/usr/bin/env python3
"""RETIRED GENERATOR — builders only, kept for import.

This module built the v1 (``acms-ms-v1``) artifacts: a 550-challenge
manifest whose pool was exactly the open half of MS-1190, parsed out of
``reference/index.html``.  The scored pool is now the 10115-row SAIR
draw distilled into ``build/data/`` — see ``build/sync_dataset.py`` —
and ``build/build_manifest_v2.py`` is the sole generator.

Running this file is a hard error.  What survives is the set of
builders that ``build_manifest_v2`` imports and reuses unchanged, so
that the frozen artifacts they produce stay byte-identical:

  load_items / ms_initial      reference/index.html + the D-2 encoding
  build_training               training_424.json (FROZEN)
  build_move_spec              move_spec.json (FROZEN)
  build_golden                 golden_vectors.json
  replay, dump, FREEZE_DATE, LIMITS, GENERATORS, TARGET

Every [Verified] figure from DESIGN.md (§1.5, §2.1, §2.3) is still
hard-asserted inside those builders, so drift in the prototype data or
the conversion recipe fails loudly instead of silently changing the
frozen artifacts.

Deterministic: no timestamps, no randomness; identical inputs give
byte-identical outputs.
"""

import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import canon, core  # noqa: E402

MANIFEST_VERSION = "acms-ms-v1"
COMPETITION = "acms"
GENERATORS = ["x", "y"]
TARGET = [[1], [2]]
# D-9 pending: placeholder per DESIGN.md §3.1 example.  freeze_date is
# deliberately outside instance_hash (§3.2), so fixing D-9 later does
# not invalidate certificates.
FREEZE_DATE = "2026-09-01T00:00:00Z"
LIMITS = {"max_path_length": 100000,
          "max_total_relator_length": 10000,
          "max_work": 5000000}
SOURCE_PRESENTATION_SET = "Shehper et al. 2025, MS-1190"
SOURCE_STATUS = "Fagan et al., The Two-Hump Problem, ICML 2026"

# Prototype 12-move id -> ac-r2-v1 id (DESIGN.md §1.5).
REMAP = {0: 0, 1: 1, 2: 2, 3: 4, 4: 6, 5: 7, 6: 8, 7: 9,
         8: 10, 9: 11, 10: 12, 11: 13}
# Loose-trivial final state -> canonicalization suffix (DESIGN.md §1.2).
CANON_SUFFIX = {
    ((1,), (2,)): [], ((1,), (-2,)): [1],
    ((-1,), (2,)): [0], ((-1,), (-2,)): [0, 1],
    ((-2,), (1,)): [2, 5, 2, 8], ((2,), (-1,)): [3, 4, 3, 10],
    ((-2,), (-1,)): [2, 0, 4, 3], ((2,), (1,)): [0, 2, 5, 2, 8],
}

# [Verified] figures from DESIGN.md, asserted after conversion.
EXPECTED_STATUS_COUNTS = {("trivial", True): 424, ("trivial", False): 216,
                          ("unsolved", False): 550}
EXPECTED_LEN_STATS = (7, 26, 159, 33.6)
EXPECTED_PEAK_STATS = (7, 14, 25, 14.7)
EXPECTED_WORK_STATS = (43, 229, 2161, 347.0)
EXPECTED_SUFFIX_COUNTS = {0: 38, 1: 80, 2: 43, 4: 187, 5: 76}
EXPECTED_CLASS_HISTOGRAM = {1: 193, 2: 16, 3: 19, 4: 10, 5: 8, 6: 5,
                            8: 4, 9: 2, 16: 1, 22: 1, 34: 1, 36: 1}

MOVE_DESCRIPTIONS = {
    0: "r0 <- r0^-1", 1: "r1 <- r1^-1",
    2: "r0 <- r0 r1", 3: "r0 <- r0 r1^-1",
    4: "r1 <- r1 r0", 5: "r1 <- r1 r0^-1",
    6: "r0 <- x r0 x^-1", 7: "r0 <- x^-1 r0 x",
    8: "r0 <- y r0 y^-1", 9: "r0 <- y^-1 r0 y",
    10: "r1 <- x r1 x^-1", 11: "r1 <- x^-1 r1 x",
    12: "r1 <- y r1 y^-1", 13: "r1 <- y^-1 r1 y",
}


def load_items():
    src = REPO / "reference" / "index.html"
    line = [l for l in src.read_text().split("\n")
            if l.startswith("const DATA")][0]
    return json.loads(line[len("const DATA = "):].rstrip(";"))["items"]


def ms_initial(n, wv):
    """MS(n, w) initial relators under the frozen D-2 convention
    r1 = x w^-1 (DESIGN.md §1.1)."""
    r0 = core.free_reduce([-1] + [2] * n + [1] + [-2] * (n + 1))
    r1 = core.free_reduce((1,) + core.invert(tuple(wv)))
    return [list(r0), list(r1)]


def stats(values):
    xs = sorted(values)
    return xs[0], xs[len(xs) // 2], xs[-1], round(sum(xs) / len(xs), 1)


def replay(initial, moves):
    state = (tuple(initial[0]), tuple(initial[1]))
    tot = len(state[0]) + len(state[1])
    peak = work = tot
    for m in moves:
        state = core.apply_move(state, m)
        tot = len(state[0]) + len(state[1])
        peak = max(peak, tot)
        work += tot
    return state, peak, work


def build_training(items, move_spec_hash):
    entries = []
    lens, peaks, works = [], [], []
    suffix_counts = collections.Counter()
    seq = 0
    for it in items:
        proto_path = it.get("path")
        if not proto_path:
            continue
        seq += 1
        tid = "ms-train-%04d" % seq
        initial = ms_initial(it["n"], it["wv"])
        mid = [REMAP[m] for m in proto_path]
        state, _, _ = replay(initial, mid)
        suffix = CANON_SUFFIX[state]
        suffix_counts[len(suffix)] += 1
        moves = mid + suffix
        state, peak, work = replay(initial, moves)
        assert state == ((1,), (2,)), tid
        lens.append(len(moves)); peaks.append(peak); works.append(work)
        entries.append({
            "training_id": tid,
            "family": "miller-schupp",
            "n": it["n"], "w": it["w"], "w_vector": it["wv"],
            "generators": GENERATORS,
            "initial_relators": initial,
            "target_relators": TARGET,
            "move_spec_version": core.MOVE_SPEC_VERSION,
            "moves": moves,
            "length": len(moves),
            "peak_total_relator_length": peak,
            "work": work,
            "certificate_hash": canon.certificate_hash(
                tid, core.MOVE_SPEC_VERSION, moves),
            "prototype_path_length": len(proto_path),
        })
    assert len(entries) == 424, len(entries)
    assert stats(lens) == EXPECTED_LEN_STATS, stats(lens)
    assert stats(peaks) == EXPECTED_PEAK_STATS, stats(peaks)
    assert stats(works) == EXPECTED_WORK_STATS, stats(works)
    assert dict(suffix_counts) == EXPECTED_SUFFIX_COUNTS, dict(suffix_counts)
    return {
        "format": "acms-training-v1",
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "note": ("424 known trivializations of MS instances, converted from "
                 "the prototype 12-move ids to ac-r2-v1 and canonicalized to "
                 "the exact ordered target (x, y).  These instances are NOT "
                 "scored challenges; they are published training data "
                 "(DESIGN.md §1.5, O-2)."),
        "length_stats": dict(zip(("min", "median", "max", "mean"), EXPECTED_LEN_STATS)),
        "instances": entries,
    }


def build_manifest(items, move_spec_hash):
    open_items = [it for it in items if it["status"] == "unsolved"]
    assert len(open_items) == 550, len(open_items)
    class_sizes = collections.Counter(it["cls"] for it in open_items)
    hist = collections.Counter(class_sizes.values())
    assert dict(hist) == EXPECTED_CLASS_HISTOGRAM, dict(hist)

    challenges = []
    for seq, it in enumerate(open_items, 1):
        cid = "ms-v1-%04d" % seq
        wv = it["wv"]
        assert sum(1 if a == 1 else -1 for a in wv if abs(a) == 1) == 0, \
            "sigma_x(w) != 0 for %s" % cid
        initial = ms_initial(it["n"], wv)
        for r in initial:
            assert list(core.free_reduce(r)) == r, cid
        challenges.append({
            "challenge_id": cid,
            "family": "miller-schupp",
            "n": it["n"], "w": it["w"], "w_vector": wv,
            "generators": GENERATORS,
            "initial_relators": initial,
            "target_relators": TARGET,
            "move_spec_version": core.MOVE_SPEC_VERSION,
            "status_at_freeze": "open",
            "scored": True,
            "base_score": 1,
            "instance_hash": canon.instance_hash(
                cid, GENERATORS, initial, TARGET,
                core.MOVE_SPEC_VERSION, move_spec_hash),
            "source": {
                "presentation_set": SOURCE_PRESENTATION_SET,
                "status_source": SOURCE_STATUS,
                "reported_class": it["cls"],
                "reported_class_size": class_sizes[it["cls"]],
                "reported_class_normative": False,
            },
            "freeze_date": FREEZE_DATE,
        })
    return {
        "manifest_version": MANIFEST_VERSION,
        "competition": COMPETITION,
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "manifest_hash": canon.manifest_hash(
            [c["instance_hash"] for c in challenges]),
        "freeze_date": FREEZE_DATE,
        "generators": GENERATORS,
        "target_relators": TARGET,
        "limits": LIMITS,
        "challenges": challenges,
    }


def build_move_spec(move_spec_hash):
    canon_rows = []
    for st, suffix in CANON_SUFFIX.items():
        state, _, _ = replay([list(st[0]), list(st[1])], suffix)
        assert state == ((1,), (2,))
        canon_rows.append({"final_state": [list(st[0]), list(st[1])],
                           "cost": len(suffix), "path": suffix})
    canon_rows.sort(key=lambda r: (r["cost"], r["final_state"]))
    return {
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "hash_covers": "moves",
        "generators": GENERATORS,
        "letter_encoding": {"x": 1, "x^-1": -1, "y": 2, "y^-1": -2},
        "target_relators": TARGET,
        "moves": list(core.MOVE_TABLE),
        "descriptions": {str(k): v for k, v in MOVE_DESCRIPTIONS.items()},
        "canonicalization_table": canon_rows,
        "notes": [
            "Words are freely reduced after every move (single left-fold "
            "stack cancellation).",
            "The move set is closed under inversion: the 'inverse' column "
            "is an involution, so AC-reachability is symmetric.",
            "The target is the EXACT ordered pair (x, y) = [[1],[2]].  The "
            "canonicalization_table shows the (exhaustively verified) "
            "shortest suffixes from every loose trivial state; the exact-"
            "target rule adds at most 5 moves to any path.",
            "move_spec_hash = sha256 of the canonical JSON (RFC 8785 "
            "compatible: sorted keys, no whitespace, ASCII) of the "
            "'moves' array only.",
        ],
    }


def build_metadata_rows(items, challenge_ids, training_ids):
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
            "scored": "true" if status == "open" else "false",
            "challenge_id": challenge_ids.get(seq, ""),
            "training_id": training_ids.get(seq, ""),
            "prototype_path_length": len(it["path"]) if has_path else "",
        })
    return rows


def build_golden(manifest, training, move_spec_hash):
    tr = training["instances"]
    by_len = sorted(tr, key=lambda e: (e["length"], e["training_id"]))
    picks = [by_len[0], by_len[len(by_len) // 2], by_len[-1]]

    def as_challenge(entry):
        return {"challenge_id": entry["training_id"],
                "move_spec_version": entry["move_spec_version"],
                "generators": GENERATORS,
                "initial_relators": entry["initial_relators"],
                "target_relators": entry["target_relators"]}

    challenges = {e["training_id"]: as_challenge(e) for e in picks}
    challenges["golden-yx"] = {
        "challenge_id": "golden-yx",
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "generators": GENERATORS,
        "initial_relators": [[2], [1]],
        "target_relators": TARGET,
    }
    challenges["golden-pump"] = {
        "challenge_id": "golden-pump",
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "generators": GENERATORS,
        "initial_relators": [[1, 2], [1, 1, 2]],
        "target_relators": TARGET,
    }

    vectors = []

    def ok_expected(entry):
        return {"ok": True, "length": entry["length"],
                "peak_total_relator_length": entry["peak_total_relator_length"],
                "work": entry["work"],
                "certificate_hash": entry["certificate_hash"]}

    for tag, entry in zip(("shortest", "median", "longest"), picks):
        vectors.append({"name": "accept-%s-%s" % (tag, entry["training_id"]),
                        "challenge_id": entry["training_id"],
                        "moves": entry["moves"],
                        "expected": ok_expected(entry)})

    short = picks[0]
    vectors += [
        {"name": "spec-mismatch", "challenge_id": short["training_id"],
         "move_spec_version": "ac-r1-v0", "moves": short["moves"],
         "expected": {"ok": False, "code": "E_SPEC_MISMATCH",
                      "move_index": None}},
        {"name": "bad-move-id-negative", "challenge_id": short["training_id"],
         "moves": [0, -1],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 1,
                      "move": -1}},
        {"name": "bad-move-id-14", "challenge_id": short["training_id"],
         "moves": [14],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}},
        {"name": "bad-move-id-float", "challenge_id": short["training_id"],
         "moves": [0, 1.5],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 1}},
        {"name": "bad-move-id-string", "challenge_id": short["training_id"],
         "moves": ["3"],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}},
        {"name": "bad-move-id-null", "challenge_id": short["training_id"],
         "moves": [None],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}},
        {"name": "bad-move-id-bool", "challenge_id": short["training_id"],
         "moves": [True],
         "expected": {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}},
        {"name": "path-too-long", "challenge_id": short["training_id"],
         "moves": [6, 7, 6, 7, 6],
         "limits": dict(LIMITS, max_path_length=4),
         "expected": {"ok": False, "code": "E_PATH_TOO_LONG",
                      "move_index": None, "path_length": 5}},
        {"name": "not-target-truncated", "challenge_id": short["training_id"],
         "moves": short["moves"][:-1],
         "expected": {"ok": False, "code": "E_NOT_TARGET",
                      "move_index": None}},
        {"name": "not-target-empty-path", "challenge_id": short["training_id"],
         "moves": [],
         "expected": {"ok": False, "code": "E_NOT_TARGET",
                      "move_index": None}},
        {"name": "not-target-wrong-order", "challenge_id": "golden-yx",
         "moves": [],
         "expected": {"ok": False, "code": "E_NOT_TARGET", "move_index": None,
                      "final_shape": [1, 1]}},
    ]

    pump = challenges["golden-pump"]
    lim_len = dict(LIMITS, max_total_relator_length=20)
    verdict = core.verify(pump, [2] * 10, core.MOVE_SPEC_VERSION, lim_len)
    assert verdict["code"] == "E_LENGTH_LIMIT", verdict
    vectors.append({"name": "length-limit", "challenge_id": "golden-pump",
                    "moves": [2] * 10, "limits": lim_len,
                    "expected": {"ok": False, "code": "E_LENGTH_LIMIT",
                                 "move_index": verdict["move_index"]}})
    lim_work = dict(LIMITS, max_work=200)
    verdict = core.verify(pump, [6, 7] * 20, core.MOVE_SPEC_VERSION, lim_work)
    assert verdict["code"] == "E_WORK_BUDGET", verdict
    vectors.append({"name": "work-budget", "challenge_id": "golden-pump",
                    "moves": [6, 7] * 20, "limits": lim_work,
                    "expected": {"ok": False, "code": "E_WORK_BUDGET",
                                 "move_index": verdict["move_index"]}})

    sid = short["training_id"]
    line = sid + ": " + json.dumps(short["moves"])
    success = {"accepted": True,
               "results": [{"ok": True, "challenge_id": sid,
                            "certificate_hash": short["certificate_hash"]}]}
    skipped = {"challenge_id": sid, "ok": False, "skipped": True,
               "reason": "already_verified"}
    longer_moves = [0, 0] + short["moves"]
    longer = core.verify(challenges[sid], longer_moves, core.MOVE_SPEC_VERSION, LIMITS)
    assert longer["ok"] and longer["length"] == short["length"] + 2, longer
    submission_vectors = [
        {"name": "sub-accept-one",
         "raw": line + "\n",
         "expected": success},
        {"name": "sub-accept-comments-and-blank-lines",
         "raw": "\n# Method: search; score: 100 is only a comment.\n\n" + line
                + " # Notes: thanks to the training data.\n# End.\n",
         "expected": success},
        {"name": "sub-accept-crlf-whitespace",
         "raw": "\t# Method notes\r\n\r\n\t" + sid + " \t: \t"
                + json.dumps(short["moves"]) + " \t# End\r\n",
         "expected": success},
        {"name": "sub-accept-utf8-bom",
         "raw": "\ufeff" + line + "\n",
         "expected": success},
        {"name": "sub-accept-long-unicode-comment",
         "raw": "# " + "λ" * 2001 + "\n" + line + " # " + "a" * 2001,
         "expected": success},
        {"name": "sub-malformed-truncated",
         "raw": sid + ": [6, 4",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_moves_json", "line_number": 1}},
        {"name": "sub-malformed-missing-colon",
         "raw": sid + " [6, 4]",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_solution_line", "line_number": 1}},
        {"name": "sub-malformed-missing-id",
         "raw": ": [6, 4]",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_solution_line", "line_number": 1}},
        {"name": "sub-malformed-missing-moves",
         "raw": sid + ": # No move list",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "moves_not_array", "line_number": 1}},
        {"name": "sub-malformed-moves-without-brackets",
         "raw": sid + ": 6, 4, 2",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "moves_not_array", "line_number": 1}},
        {"name": "sub-malformed-trailing-comma",
         "raw": sid + ": [6, 4,]",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_moves_json", "line_number": 1}},
        {"name": "sub-noninteger-move-id",
         "raw": sid + ": [6, 1.5]",
         "expected": {"accepted": True, "results": [
             {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 1}]}},
        {"name": "sub-malformed-trailing-text",
         "raw": line + " notes without a comment marker",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_moves_json", "line_number": 1}},
        {"name": "sub-malformed-multiline-moves",
         "raw": sid + ": [6,\n4]",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_moves_json", "line_number": 1}},
        {"name": "sub-malformed-comments-only",
         "raw": "\n# No solutions\n \t# Still no solutions\n",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "no_solutions"}},
        {"name": "sub-duplicate-after-success-skipped",
         "raw": line + "\n# These later candidates are not replayed.\n"
                + sid + ": [14]\n" + sid + ": [true]\n",
         "expected": {"accepted": True,
                      "results": [success["results"][0], skipped, skipped]}},
        {"name": "sub-duplicate-first-valid-wins-before-shorter",
         "raw": sid + ": " + json.dumps(longer_moves) + "\n" + line + "\n",
         "expected": {"accepted": True, "results": [
             {"ok": True, "challenge_id": sid, "length": longer["length"],
              "certificate_hash": longer["certificate_hash"]}, skipped]}},
        {"name": "sub-duplicate-failures-then-success",
         "raw": sid + ": []\n" + sid + ": [14]\n" + line + "\n",
         "expected": {"accepted": True, "results": [
             {"ok": False, "challenge_id": sid, "code": "E_NOT_TARGET"},
             {"ok": False, "challenge_id": sid, "code": "E_BAD_MOVE_ID",
              "move_index": 0}, success["results"][0]]}},
        {"name": "sub-duplicate-unknown-challenge-retried",
         "raw": "ac-99999: []\nac-99999: []\n",
         "expected": {"accepted": True, "results": [
             {"ok": False, "challenge_id": "ac-99999", "code": "E_UNKNOWN_CHALLENGE"},
             {"ok": False, "challenge_id": "ac-99999", "code": "E_UNKNOWN_CHALLENGE"}]}},
        {"name": "sub-duplicate-malformed-later-line-rejects-whole-file",
         "raw": line + "\n# A successful earlier path does not bypass parsing.\n"
                + sid + ": [1,]\n",
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "bad_moves_json", "line_number": 3,
                      "counts_against_quota": False}},
        {"name": "sub-duplicate-all-records-count-toward-limit",
         "raw": (line + "\n") * 501,
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "too_many_solutions", "solutions": 501,
                      "max_solutions": 500, "counts_against_quota": False}},
        {"name": "sub-unknown-challenge",
         "raw": "ac-99999: []\ngolden-pump: [14]\n" + line + "\n",
         "expected": {"accepted": True,
                      "results": [{"ok": False,
                                   "code": "E_UNKNOWN_CHALLENGE"},
                                  {"ok": False, "code": "E_BAD_MOVE_ID",
                                   "move_index": 0},
                                  {"ok": True, "challenge_id": sid,
                                   "certificate_hash": short["certificate_hash"]}]}},
        {"name": "sub-negative-move-id",
         "raw": sid + ": [-1]\n",
         "expected": {"accepted": True, "results": [
             {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}]}},
        {"name": "sub-too-many-solutions",
         "raw": "".join("ac-%05d: []\n" % (i + 1) for i in range(501)),
         "expected": {"accepted": False, "code": "E_MALFORMED",
                      "detail": "too_many_solutions"}},
    ]
    for name, token in (("bool", "true"), ("string", '"3"'), ("null", "null")):
        submission_vectors.append({
            "name": "sub-bad-move-id-" + name,
            "raw": sid + ": [" + token + "]\n",
            "expected": {"accepted": True, "results": [
                {"ok": False, "code": "E_BAD_MOVE_ID", "move_index": 0}]},
        })

    return {
        "format": "acms-golden-v1",
        "move_spec_version": core.MOVE_SPEC_VERSION,
        "move_spec_hash": move_spec_hash,
        "manifest_hash": manifest["manifest_hash"],
        "default_limits": LIMITS,
        "note": ("Self-contained conformance vectors.  'expected' is a "
                 "subset: every key it contains must match the verifier "
                 "output exactly.  Run with: "
                 "python3 -m acms_verify --golden golden_vectors.json"),
        "challenges": challenges,
        "verify_vectors": vectors,
        "submission_vectors": submission_vectors,
    }


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")
    print("wrote %s (%d bytes)" % (path.relative_to(REPO), path.stat().st_size))


def main():
    sys.exit(
        "build/build_manifest.py is the retired v1 generator (550 MS-only\n"
        "challenges).  The frozen artifacts are now produced by:\n"
        "\n"
        "    python3 build/sync_dataset.py --release ../sair_dataset/release\n"
        "    python3 build/build_manifest_v2.py\n"
        "\n"
        "This module is kept only so build_manifest_v2 can import its\n"
        "builders (build_training, build_move_spec, build_golden, ...)\n"
        "unchanged, which is what keeps move_spec.json and training_424.json\n"
        "byte-identical across the v2 rebuild.")


if __name__ == "__main__":
    main()
