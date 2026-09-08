"""Deterministic verifier core for ACMS stable AC, move spec ``sac-r8-v1``.

The stable Andrews-Curtis track asks for a *stable* trivialization: the
same balanced presentations as the ``ac-r2-v1`` track, but the target is
the EMPTY presentation and the move set additionally allows stabilization
(add a fresh generator with the relator that names it) and its inverse,
destabilization, up to rank :data:`MAX_RANK`.

Same engineering contract as :mod:`acms_verify.core` (decision D-10):
pure integer arithmetic, standard library only, no floats, no
concurrency, no randomness.  Words are tuples of nonzero ints with
``g`` meaning the generator ``g`` and ``-g`` its inverse; at rank ``k``
the alphabet is exactly ``+-1 .. +-k``.  Generator 1 is ``x``,
generator 2 is ``y``, generators 3..8 are ``g3``..``g8``.

A state is a tuple of ``k`` freely reduced words, ``k`` = the current
rank; the presentation stays balanced (``k`` generators, ``k``
relators) after every move.  The target is the empty tuple ``()``.

Frozen semantics.  Move ids must never change once frozen; ids 0..13
are byte-identical to :data:`acms_verify.core.MOVE_TABLE`, so an
``ac-r2-v1`` certificate is a legal ``sac-r8-v1`` prefix.
"""

from . import canon, core

MOVE_SPEC_VERSION = "sac-r8-v1"

#: Highest rank reachable by stabilization.  Rank starts at 2 for every
#: published challenge; repeated additions and deletions are allowed,
#: provided the current rank never exceeds this bound.
MAX_RANK = 8

NUM_MOVES = 257

#: The target of every stable challenge: the empty presentation.
TARGET = ()

#: Generator display names, index = generator number - 1.
GENERATOR_NAMES = ("x", "y", "g3", "g4", "g5", "g6", "g7", "g8")

#: The four ``E_MOVE_NOT_APPLICABLE`` reasons (frozen vocabulary).
NOT_APPLICABLE_REASONS = ("relator_out_of_rank", "generator_out_of_rank",
                          "max_rank_exceeded", "destabilize_precondition")


def _build_move_table():
    """Deterministically enumerate the frozen 257-row table.

    Layout (ids are frozen; the enumeration order below defines them):

      0..13    the ``ac-r2-v1`` table verbatim
      14       stabilize
      15..22   destabilize r_i, i = 0..7
      23..28   invert r_i, i = 2..7
      29..136  r_i <- r_i r_j^(+-1), i = 0..7, j = 0..7 (j != i),
               sign +1 then -1, skipping the four rows already in 0..13
      137..256 r_i <- c r_i c^-1, c = +-g, i = 0..7, g = 1..8,
               sign +1 then -1, skipping the eight rows already in 0..13
    """
    rows = [dict(r) for r in core.MOVE_TABLE]
    assert len(rows) == core.NUM_MOVES == 14, len(rows)

    rows.append({"id": 14, "category": "stabilize", "inverse": None})

    for i in range(MAX_RANK):
        rows.append({"id": 15 + i, "category": "destabilize",
                     "relator": i, "inverse": None})

    for i in range(2, MAX_RANK):
        mid = 23 + (i - 2)
        rows.append({"id": mid, "category": "inversion",
                     "relator": i, "inverse": mid})

    mid = 29
    for i in range(MAX_RANK):
        for j in range(MAX_RANK):
            if j == i or (i in (0, 1) and j in (0, 1)):
                continue
            rows.append({"id": mid, "category": "multiplication",
                         "relator": i, "other": j, "invert_other": False,
                         "inverse": mid + 1})
            rows.append({"id": mid + 1, "category": "multiplication",
                         "relator": i, "other": j, "invert_other": True,
                         "inverse": mid})
            mid += 2
    assert mid == 137, mid

    for i in range(MAX_RANK):
        for g in range(1, MAX_RANK + 1):
            if i in (0, 1) and g in (1, 2):
                continue
            rows.append({"id": mid, "category": "conjugation",
                         "relator": i, "conjugator": g, "inverse": mid + 1})
            rows.append({"id": mid + 1, "category": "conjugation",
                         "relator": i, "conjugator": -g, "inverse": mid})
            mid += 2
    assert mid == NUM_MOVES == 257, mid

    assert [r["id"] for r in rows] == list(range(NUM_MOVES))
    assert tuple(rows[:core.NUM_MOVES]) == core.MOVE_TABLE, \
        "ids 0..13 must be byte-identical to the frozen ac-r2-v1 table"
    return tuple(rows)


#: The frozen 257-row move table.  This exact structure — id / category /
#: parameters / inverse — is what ``move_spec_hash`` covers, serialized
#: with :func:`acms_verify.canon.jcs`.
MOVE_TABLE = _build_move_table()

#: ``INVERSE_MOVE[m]`` undoes move ``m``, or ``None`` for the two moves
#: that change the rank: stabilize and destabilize are inverse to each
#: other only up to relabeling, so neither has a fixed partner id.
INVERSE_MOVE = tuple(row["inverse"] for row in MOVE_TABLE)


def generator_name(g):
    """``1 -> "x"``, ``2 -> "y"``, ``3..8 -> "g3".."g8"``."""
    return GENERATOR_NAMES[abs(g) - 1]


def _relabel_after(word, g):
    """Shift every letter above ``g`` down by one (``g`` itself is gone)."""
    return tuple(a - 1 if a > g else (a + 1 if a < -g else a) for a in word)


def apply_move(state, m):
    """Apply frozen atomic move ``m`` (0..256) and freely reduce.

    ``state`` is a tuple of freely reduced tuples; the result is too.
    Returns ``(new_state, None)`` on success or ``(None, reason)`` when
    the move is not applicable at the current rank, where ``reason`` is
    one of :data:`NOT_APPLICABLE_REASONS`.

    Raises ``ValueError`` on an out-of-range id — callers that face
    untrusted input must range-check first (E_BAD_MOVE_ID).
    """
    if type(m) is not int or not (0 <= m < NUM_MOVES):
        raise ValueError("bad move id: %r" % (m,))
    row = MOVE_TABLE[m]
    cat = row["category"]
    k = len(state)

    if cat == "stabilize":
        if k >= MAX_RANK:
            return None, "max_rank_exceeded"
        return state + ((k + 1,),), None

    i = row["relator"]
    if i >= k:
        return None, "relator_out_of_rank"

    if cat == "destabilize":
        word = state[i]
        if len(word) != 1 or word[0] <= 0:
            return None, "destabilize_precondition"
        g = word[0]
        for j, other in enumerate(state):
            if j == i:
                continue
            for a in other:
                if a == g or a == -g:
                    return None, "destabilize_precondition"
        rest = state[:i] + state[i + 1:]
        return tuple(_relabel_after(w, g) for w in rest), None

    if cat == "inversion":
        return state[:i] + (core.invert(state[i]),) + state[i + 1:], None

    if cat == "multiplication":
        j = row["other"]
        if j >= k:
            return None, "relator_out_of_rank"
        other = state[j]
        if row["invert_other"]:
            other = core.invert(other)
        new = core.free_reduce(state[i] + other)
        return state[:i] + (new,) + state[i + 1:], None

    # conjugation
    c = row["conjugator"]
    if abs(c) > k:
        return None, "generator_out_of_rank"
    new = core.free_reduce((c,) + state[i] + (-c,))
    return state[:i] + (new,) + state[i + 1:], None


def _err(code, move_index=None, **extra):
    out = {"ok": False, "code": code, "move_index": move_index}
    out.update(extra)
    return out


def verify(challenge, moves, move_spec_version, limits):
    """Replay ``moves`` on a ``sac-r8-v1`` ``challenge`` under ``limits``.

    Mirrors :func:`acms_verify.core.verify` check for check.  The only
    addition is ``E_MOVE_NOT_APPLICABLE``, raised inside the per-move
    loop immediately after the move-id range check and before the
    relator-length check, carrying ``move``, ``move_index`` and
    ``reason``.

    ``challenge`` needs keys ``challenge_id``, ``move_spec_version``,
    ``initial_relators``, ``target_relators``.  ``moves`` is the parsed
    JSON value from the submission (may be arbitrarily malformed).
    ``limits`` needs ``max_path_length``, ``max_total_relator_length``,
    ``max_work``.
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

    state = tuple(tuple(w) for w in challenge["initial_relators"])
    rank = len(state)
    # The manifest guarantees a balanced, freely reduced, in-alphabet
    # start; a violation is an organizer-side data bug, not a contestant
    # error, so it raises instead of producing a verdict.
    if not 1 <= rank <= MAX_RANK:
        raise ValueError("initial rank %d outside 1..%d: %s"
                         % (rank, MAX_RANK, challenge["challenge_id"]))
    for w in state:
        if core.free_reduce(w) != w:
            raise ValueError("initial_relators not freely reduced: %s"
                             % (challenge["challenge_id"],))
        for a in w:
            if a == 0 or abs(a) > rank:
                raise ValueError(
                    "initial_relators letter %r outside +-1..+-%d: %s"
                    % (a, rank, challenge["challenge_id"]))

    max_total = limits["max_total_relator_length"]
    max_work = limits["max_work"]
    tot = sum(len(w) for w in state)
    peak = tot
    work = tot
    for k, m in enumerate(moves):
        # bool is an int subclass in Python; true/false are not move ids.
        if type(m) is not int or not (0 <= m < NUM_MOVES):
            return _err("E_BAD_MOVE_ID", move_index=k, move=m)
        state, reason = apply_move(state, m)
        if reason is not None:
            return _err("E_MOVE_NOT_APPLICABLE", move_index=k, move=m,
                        reason=reason)
        tot = sum(len(w) for w in state)
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
                    final_shape=[len(w) for w in state])

    return {
        "ok": True,
        "length": len(moves),
        "peak_total_relator_length": peak,
        "work": work,
        "certificate_hash": canon.certificate_hash(
            challenge["challenge_id"], move_spec_version, moves),
    }
