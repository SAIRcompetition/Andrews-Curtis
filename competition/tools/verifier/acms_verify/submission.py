"""Submission-layer parsing and verdicts (DESIGN.md §4.1, §4.2, O-5).

Structural errors (``E_MALFORMED``, ``E_DUPLICATE_CHALLENGE``,
``E_CLIENT_ASSERTED_RESULT``, body/count limits) reject the whole
submission and must not count against the daily quota.  Per-path errors
reject only that solution; the rest are processed normally.

Check priority (DESIGN.md O-5, frozen):
  body byte limit -> parse -> client-asserted-result scan -> shape
  -> solutions count -> duplicates -> per-solution verify
  (path length -> move id -> relator length -> work budget -> target).
"""

import json

from . import core

#: Structural limits (DESIGN.md §4.3).  These are the frozen v1
#: defaults; production overrides them per deployment via the
#: ``structural_limits`` argument of :func:`process_submission`
#: (requirements §6: all limits configurable, never hardcoded).
MAX_BODY_BYTES = 4 * 1024 * 1024
MAX_SOLUTIONS = 500
MAX_NOTES_CHARS = 2000
DEFAULT_STRUCTURAL_LIMITS = {
    "max_body_bytes": MAX_BODY_BYTES,
    "max_solutions": MAX_SOLUTIONS,
    "max_notes_chars": MAX_NOTES_CHARS,
}

#: Any of these keys anywhere in a submission triggers
#: ``E_CLIENT_ASSERTED_RESULT`` for the whole submission (§4.1): the
#: server accepts no client-claimed results, and such keys' only use is
#: probing.  Frozen list; part of the API contract.
FORBIDDEN_RESULT_KEYS = frozenset({
    "length", "score", "final_state", "peak", "peak_total_relator_length",
    "work", "ok", "verdict", "verified", "accepted", "result",
})

_ALLOWED_TOP_KEYS = frozenset({"method", "notes", "solutions"})
_ALLOWED_SOLUTION_KEYS = frozenset({"challenge_id", "move_spec_version", "moves"})


def _reject(code, **extra):
    out = {"accepted": False, "code": code, "counts_against_quota": False}
    out.update(extra)
    return out


def _find_forbidden_key(node, path):
    """Scan every dict key in the parsed JSON tree (iterative: immune
    to deeply nested input, which must yield a verdict, not a crash)."""
    stack = [(node, path)]
    while stack:
        node, path = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                if k in FORBIDDEN_RESULT_KEYS:
                    return path + "." + k if path else k
                stack.append((v, (path + "." if path else "") + str(k)))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                stack.append((v, "%s[%d]" % (path, i)))
    return None


def build_challenge_index(manifest):
    """``{challenge_id: challenge}`` from a parsed manifest."""
    return {c["challenge_id"]: c for c in manifest["challenges"]}


def process_submission(raw_bytes, manifest, challenge_index=None,
                       structural_limits=None):
    """Full pipeline: bytes in, structured verdict out.

    Returns either a whole-submission rejection
    (``{"accepted": False, "code": ..., ...}``) or
    ``{"accepted": True, "results": [...]}`` with one verdict per
    solution in input order.
    """
    if challenge_index is None:
        challenge_index = build_challenge_index(manifest)
    limits = manifest["limits"]
    slim = dict(DEFAULT_STRUCTURAL_LIMITS, **(structural_limits or {}))
    max_body = slim["max_body_bytes"]
    max_solutions = slim["max_solutions"]
    max_notes = slim["max_notes_chars"]

    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise TypeError("raw_bytes must be bytes")
    if len(raw_bytes) > max_body:
        return _reject("E_MALFORMED", detail="body_too_large",
                       body_bytes=len(raw_bytes), max_body_bytes=max_body)

    try:
        doc = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _reject("E_MALFORMED", detail="bad_json")
    except RecursionError:
        # Pathologically nested JSON is corrupt input, not a server
        # error: a structural E_MALFORMED like any other parse failure.
        return _reject("E_MALFORMED", detail="bad_json")

    hit = _find_forbidden_key(doc, "")
    if hit is not None:
        return _reject("E_CLIENT_ASSERTED_RESULT", key_path=hit)

    if not isinstance(doc, dict):
        return _reject("E_MALFORMED", detail="root_not_object")
    unknown = set(doc) - _ALLOWED_TOP_KEYS
    if unknown:
        return _reject("E_MALFORMED", detail="unknown_key",
                       key=sorted(unknown)[0])
    if "method" in doc and not isinstance(doc["method"], str):
        return _reject("E_MALFORMED", detail="bad_method")
    if "notes" in doc:
        if not isinstance(doc["notes"], str):
            return _reject("E_MALFORMED", detail="bad_notes")
        if len(doc["notes"]) > max_notes:
            return _reject("E_MALFORMED", detail="notes_too_long",
                           notes_chars=len(doc["notes"]),
                           max_notes_chars=max_notes)

    sols = doc.get("solutions")
    if not isinstance(sols, list) or not sols:
        return _reject("E_MALFORMED", detail="bad_solutions")
    if len(sols) > max_solutions:
        return _reject("E_MALFORMED", detail="too_many_solutions",
                       solutions=len(sols), max_solutions=max_solutions)

    seen_ids = set()
    for i, sol in enumerate(sols):
        if not isinstance(sol, dict):
            return _reject("E_MALFORMED", detail="solution_not_object", index=i)
        missing = _ALLOWED_SOLUTION_KEYS - set(sol)
        if missing:
            return _reject("E_MALFORMED", detail="solution_missing_key",
                           index=i, key=sorted(missing)[0])
        unknown = set(sol) - _ALLOWED_SOLUTION_KEYS
        if unknown:
            return _reject("E_MALFORMED", detail="unknown_key", index=i,
                           key=sorted(unknown)[0])
        if not isinstance(sol["challenge_id"], str):
            return _reject("E_MALFORMED", detail="bad_challenge_id", index=i)
        if not isinstance(sol["move_spec_version"], str):
            return _reject("E_MALFORMED", detail="bad_move_spec_version", index=i)
        if not isinstance(sol["moves"], list):
            return _reject("E_MALFORMED", detail="moves_not_array", index=i)
        if sol["challenge_id"] in seen_ids:
            return _reject("E_DUPLICATE_CHALLENGE",
                           challenge_id=sol["challenge_id"], index=i)
        seen_ids.add(sol["challenge_id"])

    results = []
    for sol in sols:
        cid = sol["challenge_id"]
        challenge = challenge_index.get(cid)
        if challenge is None:
            results.append({"challenge_id": cid, "ok": False,
                            "code": "E_UNKNOWN_CHALLENGE", "move_index": None})
            continue
        verdict = core.verify(challenge, sol["moves"],
                              sol["move_spec_version"], limits)
        verdict = dict(verdict)
        verdict["challenge_id"] = cid
        results.append(verdict)

    return {"accepted": True, "results": results}
