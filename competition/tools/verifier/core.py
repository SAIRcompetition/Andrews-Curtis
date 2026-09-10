"""Deterministic verifier core for AC, move spec ``ac-r2-v1``.

Single authoritative implementation (decision D-10): pure integer
arithmetic, standard library only, no floats, no concurrency, no
randomness.  Words are tuples of nonzero ints: 1 = x, -1 = x^-1,
2 = y, -2 = y^-1.  A presentation state is an ordered pair
``(r0, r1)`` of freely reduced words.

Frozen semantics — see DESIGN.md §1.3 (move table), §4.2 (verify loop).
Move ids must never change once frozen.
"""

from . import canon

MOVE_SPEC_VERSION = "ac-r2-v1"

#: Conjugator letters for moves 6..9 (r0) and 10..13 (r1), in id order.
GENS = (1, -1, 2, -2)

NUM_MOVES = 14

#: The frozen 14-row move table (DESIGN.md §1.3).  This exact structure —
#: id / category / parameters / inverse — is what ``move_spec_hash``
#: covers (§3.3), serialized with :func:`verifier.canon.jcs`.
MOVE_TABLE = (
    {"id": 0, "category": "inversion", "relator": 0, "inverse": 0},
    {"id": 1, "category": "inversion", "relator": 1, "inverse": 1},
    {"id": 2, "category": "multiplication", "relator": 0, "other": 1,
     "invert_other": False, "inverse": 3},
    {"id": 3, "category": "multiplication", "relator": 0, "other": 1,
     "invert_other": True, "inverse": 2},
    {"id": 4, "category": "multiplication", "relator": 1, "other": 0,
     "invert_other": False, "inverse": 5},
    {"id": 5, "category": "multiplication", "relator": 1, "other": 0,
     "invert_other": True, "inverse": 4},
    {"id": 6, "category": "conjugation", "relator": 0, "conjugator": 1, "inverse": 7},
    {"id": 7, "category": "conjugation", "relator": 0, "conjugator": -1, "inverse": 6},
    {"id": 8, "category": "conjugation", "relator": 0, "conjugator": 2, "inverse": 9},
    {"id": 9, "category": "conjugation", "relator": 0, "conjugator": -2, "inverse": 8},
    {"id": 10, "category": "conjugation", "relator": 1, "conjugator": 1, "inverse": 11},
    {"id": 11, "category": "conjugation", "relator": 1, "conjugator": -1, "inverse": 10},
    {"id": 12, "category": "conjugation", "relator": 1, "conjugator": 2, "inverse": 13},
    {"id": 13, "category": "conjugation", "relator": 1, "conjugator": -2, "inverse": 12},
)

#: ``INVERSE_MOVE[m]`` undoes move ``m`` (the move set is closed under
#: inversion, DESIGN.md §1.3).
INVERSE_MOVE = tuple(row["inverse"] for row in MOVE_TABLE)


def free_reduce(word):
    """Single left-fold stack cancellation (DESIGN.md §3.2 note, §4.2).

    Deterministic and idempotent; equals full reduction for any input.
    Returns a tuple.
    """
    out = []
    for a in word:
        if out and out[-1] == -a:
            out.pop()
        else:
            out.append(a)
    return tuple(out)


def invert(word):
    """Formal inverse of a word; preserves free reduction."""
    return tuple(-a for a in reversed(word))


def apply_move(state, m):
    """Apply frozen atomic move ``m`` (0..13) and freely reduce.

    ``state`` is a pair of freely reduced tuples; the result is too.
    Raises ``ValueError`` on an out-of-range id — callers that face
    untrusted input must range-check first (E_BAD_MOVE_ID).
    """
    r0, r1 = state
    if m == 0:
        return (invert(r0), r1)
    if m == 1:
        return (r0, invert(r1))
    if m == 2:
        return (free_reduce(r0 + r1), r1)
    if m == 3:
        return (free_reduce(r0 + invert(r1)), r1)
    if m == 4:
        return (r0, free_reduce(r1 + r0))
    if m == 5:
        return (r0, free_reduce(r1 + invert(r0)))
    if 6 <= m <= 9:
        g = GENS[m - 6]
        return (free_reduce((g,) + r0 + (-g,)), r1)
    if 10 <= m <= 13:
        g = GENS[m - 10]
        return (r0, free_reduce((g,) + r1 + (-g,)))
    raise ValueError("bad move id: %r" % (m,))


def _err(code, move_index=None, **extra):
    out = {"ok": False, "code": code, "move_index": move_index}
    out.update(extra)
    return out


def verify(challenge, moves, move_spec_version, limits):
    """Replay ``moves`` on ``challenge`` under ``limits`` (DESIGN.md §4.2).

    ``challenge`` needs keys ``challenge_id``, ``move_spec_version``,
    ``initial_relators``, ``target_relators``.  ``moves`` is the parsed
    JSON value from the submission (may be arbitrarily malformed).
    ``limits`` needs ``max_path_length``, ``max_total_relator_length``,
    ``max_work``.

    Per-move error results carry ``move_index`` (0-based); pre-loop
    errors carry ``move_index: None``.  Error-code priority follows
    DESIGN.md O-5: path length -> per-move id -> relator length -> work.
    """
    if move_spec_version != challenge["move_spec_version"]:
        return _err("E_SPEC_MISMATCH",
                    expected=challenge["move_spec_version"],
                    got=move_spec_version)
    if not isinstance(moves, list):
        return _err("E_MALFORMED", detail="moves_not_array")
    if len(moves) > limits["max_path_length"]:
        return _err("E_PATH_TOO_LONG", path_length=len(moves),
                    max_path_length=limits["max_path_length"])

    r0, r1 = challenge["initial_relators"]
    state = (tuple(r0), tuple(r1))
    if (free_reduce(state[0]) != state[0]
            or free_reduce(state[1]) != state[1]):
        # Manifest guarantees reduced initial relators (§3.1); a violation
        # is an organizer-side data bug, not a contestant error.
        raise ValueError("initial_relators not freely reduced: %s"
                         % (challenge["challenge_id"],))

    max_total = limits["max_total_relator_length"]
    max_work = limits["max_work"]
    tot = len(state[0]) + len(state[1])
    peak = tot
    work = tot
    for k, m in enumerate(moves):
        # bool is an int subclass in Python; true/false are not move ids.
        if type(m) is not int or not (0 <= m < NUM_MOVES):
            return _err("E_BAD_MOVE_ID", move_index=k, move=m)
        state = apply_move(state, m)
        tot = len(state[0]) + len(state[1])
        if tot > max_total:
            return _err("E_LENGTH_LIMIT", move_index=k,
                        total_relator_length=tot,
                        max_total_relator_length=max_total)
        if tot > peak:
            peak = tot
        work += tot
        if work > max_work:
            return _err("E_WORK_BUDGET", move_index=k, work=work,
                        max_work=max_work)

    target = tuple(tuple(r) for r in challenge["target_relators"])
    if state != target:
        return _err("E_NOT_TARGET", move_index=None,
                    final_shape=[len(state[0]), len(state[1])])

    return {
        "ok": True,
        "length": len(moves),
        "peak_total_relator_length": peak,
        "work": work,
        "certificate_hash": canon.certificate_hash(
            challenge["challenge_id"], move_spec_version, moves),
    }
