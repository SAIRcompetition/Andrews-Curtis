"""Parse TXT submissions and dispatch paths to the official move verifier.

One record per line: ``challenge_id: [0, 2, 6]``.  Blank lines and all
text from the first ``#`` to the end of a line are ignored.  Only the
challenge ID and moves affect verification; comments never affect hashes.

Structural errors reject the whole submission without consuming quota.
Priority: body byte limit -> UTF-8 decoding -> all line syntax/JSON checks
-> nonempty/count limits -> duplicate IDs -> per-solution verification.
The unchanged per-path priority is path length -> move ID -> relator
length -> work budget -> target (with Stable AC applicability checks).
"""

import json
import math
import re

from . import specs

MAX_BODY_BYTES = 10_000_000  # 10 MB, including comments.
MAX_SOLUTIONS = 500
DEFAULT_STRUCTURAL_LIMITS = {
    "max_body_bytes": MAX_BODY_BYTES,
    "max_solutions": MAX_SOLUTIONS,
}

_CHALLENGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def _reject(code, **extra):
    out = {"accepted": False, "code": code, "counts_against_quota": False}
    out.update(extra)
    return out


def _parse_int(value):
    # Bound decimal conversion on older Python versions too.  This is a
    # JSON parser safeguard; legitimate move IDs have at most three digits.
    if len(value.lstrip("-")) > 4300:
        raise ValueError("integer too long")
    return int(value)


def _parse_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite number")
    return number


def _reject_constant(value):
    # The stdlib otherwise accepts NaN/Infinity, which are not JSON values.
    raise ValueError("non-JSON numeric constant")


def _check_nesting(value):
    """Bound JSON nesting before parsing, ignoring brackets inside strings.

    Limiting nested invalid move values keeps both JSON decoding and later
    verdict serialization safe, independent of Python's recursion limit.
    """
    depth = 0
    in_string = escaped = False
    for char in value:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > 64:
                raise ValueError("JSON nesting too deep")
        elif char in "]}":
            depth -= 1


def build_challenge_index(manifest):
    """``{challenge_id: challenge}`` from a parsed manifest."""
    return {c["challenge_id"]: c for c in manifest["challenges"]}


def process_submission(raw_bytes, manifest, challenge_index=None,
                       structural_limits=None):
    """Accept UTF-8 TXT bytes (optional BOM; LF or CRLF), returning a verdict.

    A non-comment line must contain an ID, a colon, and one JSON array on
    the same line.  Parse errors include the one-based physical line number
    without echoing the input.  The optional ``structural_limits`` mapping
    overrides the byte and solution-count limits for a deployment.

    Whole-submission errors return ``accepted: false``.  Otherwise results
    appear in record order, each using the official challenge's move spec
    for replay and certificate hashing.  Legacy JSON submissions are not
    accepted or automatically converted.
    """
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise TypeError("raw_bytes must be bytes")
    slim = dict(DEFAULT_STRUCTURAL_LIMITS, **(structural_limits or {}))
    max_body = slim["max_body_bytes"]
    max_solutions = slim["max_solutions"]
    if len(raw_bytes) > max_body:
        return _reject("E_MALFORMED", detail="body_too_large",
                       body_bytes=len(raw_bytes), max_body_bytes=max_body)
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _reject("E_MALFORMED", detail="bad_utf8")

    sols = []
    # Split only on LF: CRLF is handled by strip(), while an unescaped
    # Unicode line separator inside a JSON string remains part of that string.
    for line_number, line in enumerate(text.split("\n"), 1):
        content = line.partition("#")[0].strip()
        if not content:
            continue
        cid, colon, payload = content.partition(":")
        cid, payload = cid.strip(), payload.strip()
        if not colon or _CHALLENGE_ID.fullmatch(cid) is None:
            return _reject("E_MALFORMED", detail="bad_solution_line",
                           line_number=line_number)
        if not payload.startswith("["):
            return _reject("E_MALFORMED", detail="moves_not_array",
                           line_number=line_number)
        try:
            _check_nesting(payload)
            moves = json.loads(payload, parse_int=_parse_int,
                               parse_float=_parse_float,
                               parse_constant=_reject_constant)
        except (ValueError, RecursionError):
            return _reject("E_MALFORMED", detail="bad_moves_json",
                           line_number=line_number)
        sols.append({"challenge_id": cid, "moves": moves,
                     "line_number": line_number})

    if not sols:
        return _reject("E_MALFORMED", detail="no_solutions")
    if len(sols) > max_solutions:
        return _reject("E_MALFORMED", detail="too_many_solutions",
                       solutions=len(sols), max_solutions=max_solutions)
    seen_ids = set()
    for index, sol in enumerate(sols):
        if sol["challenge_id"] in seen_ids:
            return _reject("E_DUPLICATE_CHALLENGE",
                           challenge_id=sol["challenge_id"], index=index,
                           line_number=sol["line_number"])
        seen_ids.add(sol["challenge_id"])

    if challenge_index is None:
        challenge_index = build_challenge_index(manifest)
    limits = manifest["limits"]

    results = []
    for sol in sols:
        cid = sol["challenge_id"]
        challenge = challenge_index.get(cid)
        if challenge is None:
            results.append({"challenge_id": cid, "ok": False,
                            "code": "E_UNKNOWN_CHALLENGE", "move_index": None})
            continue
        verdict = specs.verify_challenge(challenge, sol["moves"],
                                         challenge["move_spec_version"], limits)
        verdict = dict(verdict)
        verdict.pop("peak_total_relator_length", None)
        verdict["challenge_id"] = cid
        results.append(verdict)

    return {"accepted": True, "results": results}
