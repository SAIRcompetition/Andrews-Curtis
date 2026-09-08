#!/usr/bin/env python3
"""Independent BFS check of the sac-r8-v1 canonicalization law.

Same role for the stable track that ``build/checks/acheck.py`` plays for
ac-r2-v1: a breadth-first search written against the move table, not
against the builder, establishing the costs the builder then transcribes
into ``STABLE_CANON_SUFFIX`` and publishes in ``stable_move_spec.json``.

  Q1  cost to the EMPTY presentation from each of the 8 loose-trivial
      rank-2 states, with one shortest path each
  Q2  the same for all 48 rank-3 single-letter states, checked against
      the general law: cost = k + (number of inverted letters)
  Q3  the suffix table the builder uses, re-verified move by move

The law asserts a *minimum*, so the search must be exhaustive to be
worth anything.  It is exhaustive inside a stated envelope: paths that
never let the summed relator length exceed ``k + 3`` and never stabilize
past rank ``k + 1``.  Nothing outside that envelope can help — every
path must spend at least k destabilizations to reach rank 0. Each
initially inverted single-letter relator must also be changed before it
can be deleted; a non-destabilization move changes at most one such
relator. These lower bounds already account for the whole cost — but the
envelope is what the search actually proves, so it is named here rather
than implied.

Run:  python3 build/checks/stable_canon.py     (~15 s)
"""

import itertools
import sys
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))
sys.path.insert(0, str(REPO / "build"))

from acms_verify import stable_core  # noqa: E402

TARGET = ()

#: Search envelope, relative to the starting rank k.
EXTRA_LENGTH = 3
EXTRA_RANK = 1


def law(state):
    """k + (number of inverted letters)."""
    return len(state) + sum(1 for w in state if w[0] < 0)


def bfs(start, cap=None):
    """Shortest applicable-move path from ``start`` to the empty
    presentation inside the envelope; ``(None, None)`` if there is none
    at depth <= ``cap``."""
    if start == TARGET:
        return 0, []
    k = len(start)
    cap = law(start) if cap is None else cap
    max_total = sum(len(w) for w in start) + EXTRA_LENGTH
    max_rank = min(k + EXTRA_RANK, stable_core.MAX_RANK)
    seen = {start}
    queue = deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        if len(path) >= cap:
            continue
        for m in range(stable_core.NUM_MOVES):
            nxt, reason = stable_core.apply_move(state, m)
            if reason is not None:
                continue
            if nxt == TARGET:
                return len(path) + 1, path + [m]
            if (len(nxt) > max_rank
                    or sum(len(w) for w in nxt) > max_total
                    or nxt in seen):
                continue
            seen.add(nxt)
            queue.append((nxt, path + [m]))
    return None, None


def single_letter_states(k):
    """Every state whose k relators are the k generators, each exactly
    once, in some order and with some signs."""
    out = []
    for perm in itertools.permutations(range(1, k + 1)):
        for signs in itertools.product((1, -1), repeat=k):
            out.append(tuple((s * g,) for g, s in zip(perm, signs)))
    return out


def sweep(k, verbose):
    """Return the number of states whose BFS cost differs from the law."""
    failures = 0
    histogram = {}
    for state in single_letter_states(k):
        expect = law(state)
        cost, path = bfs(state)
        # bfs caps at the law, so cost == expect proves "no shorter path
        # inside the envelope" as well as "this path exists".
        if cost != expect:
            failures += 1
            print("  MISMATCH %s: bfs %s, law %d" % (state, cost, expect))
        elif verbose:
            print("  %-24s cost %d   path %s" % (state, cost, path))
        histogram[expect] = histogram.get(expect, 0) + 1
    print("  cost histogram (= k + negatives): %s"
          % dict(sorted(histogram.items())))
    return failures


def main():
    failures = 0
    print("=== Q1: rank-2 loose-trivial states -> () under sac-r8-v1 "
          "(%d moves, max_rank %d) ==="
          % (stable_core.NUM_MOVES, stable_core.MAX_RANK))
    failures += sweep(2, verbose=True)

    print()
    print("=== Q2: the k + negatives law at rank 3 (all %d states) ==="
          % len(single_letter_states(3)))
    failures += sweep(3, verbose=False)

    print()
    print("=== Q3: the suffix table transcribed by "
          "build/build_manifest_v2.py ===")
    from build_manifest_v2 import STABLE_CANON_SUFFIX  # noqa: E402
    assert len(STABLE_CANON_SUFFIX) == 8, len(STABLE_CANON_SUFFIX)
    assert set(STABLE_CANON_SUFFIX) == set(single_letter_states(2))
    for state, suffix in sorted(STABLE_CANON_SUFFIX.items()):
        cur = state
        for m in suffix:
            cur, reason = stable_core.apply_move(cur, m)
            assert reason is None, (state, m, reason)
        cost, _ = bfs(state)
        ok = cur == TARGET and len(suffix) == cost == law(state)
        failures += not ok
        print("  %-24s suffix %-14s cost %d  minimal %s  reaches () %s"
              % (state, suffix, len(suffix),
                 cost == len(suffix), cur == TARGET))

    print()
    print("FAILURES: %d" % failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
