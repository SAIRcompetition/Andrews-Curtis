"""Core semantics: free reduction, move table, canonicalization table.

Covers DESIGN.md §1.2 (exhaustive canonicalization costs), §1.3
(involution / closure under inversion), §3.2 and §4.2 (incremental
reduction == full reduction).
"""

import itertools
import unittest
from collections import deque

from acms_verify import core


def full_reduce(word):
    """Reduce by repeated full passes — the naive reference."""
    w = list(word)
    changed = True
    while changed:
        changed = False
        for i in range(len(w) - 1):
            if w[i] == -w[i + 1]:
                del w[i:i + 2]
                changed = True
                break
    return tuple(w)


def det_words(alphabet=(1, -1, 2, -2), max_len=5):
    for n in range(max_len + 1):
        for tup in itertools.product(alphabet, repeat=n):
            yield tup


class TestFreeReduce(unittest.TestCase):
    def test_left_fold_equals_full_reduction(self):
        for w in det_words(max_len=5):
            self.assertEqual(core.free_reduce(w), full_reduce(w), w)

    def test_idempotent(self):
        for w in det_words(max_len=4):
            r = core.free_reduce(w)
            self.assertEqual(core.free_reduce(r), r)

    def test_incremental_equals_whole_word(self):
        """After each atomic move the state equals full reduction of the
        unreduced concatenation (required by DESIGN.md §4.2)."""
        states = [((1, 2, 1), (2, -1, 2)), ((-1, 2, 2, 1, -2, -2, -2), (1, 2)),
                  ((2, 1, -2), (-2, -1, 2, 1))]
        for s in states:
            for m in range(core.NUM_MOVES):
                got = core.apply_move(s, m)
                r0, r1 = s
                raw = {
                    0: (core.invert(r0), r1), 1: (r0, core.invert(r1)),
                    2: (r0 + r1, r1), 3: (r0 + core.invert(r1), r1),
                    4: (r0, r1 + r0), 5: (r0, r1 + core.invert(r0)),
                }
                if m in raw:
                    expect = tuple(full_reduce(w) for w in raw[m])
                elif m <= 9:
                    g = core.GENS[m - 6]
                    expect = (full_reduce((g,) + r0 + (-g,)), r1)
                else:
                    g = core.GENS[m - 10]
                    expect = (r0, full_reduce((g,) + r1 + (-g,)))
                self.assertEqual(got, expect, (s, m))


class TestMoveTable(unittest.TestCase):
    def test_inverse_column_is_involution(self):
        inv = core.INVERSE_MOVE
        self.assertEqual(sorted(inv), list(range(14)))
        for m in range(14):
            self.assertEqual(inv[inv[m]], m)

    def test_inverse_move_undoes(self):
        states = [((1, 2, 1), (2, -1, 2)), ((-1, 2, 2, 1, -2, -2, -2), (1, 2)),
                  ((2,), (1,)), ((1, 2, -1, -2), (2, 2, 1))]
        for s in states:
            for m in range(14):
                back = core.apply_move(core.apply_move(s, m),
                                       core.INVERSE_MOVE[m])
                self.assertEqual(back, s, (s, m))

    def test_move_table_matches_apply(self):
        """The declarative MOVE_TABLE rows describe exactly what
        apply_move does."""
        s = ((1, 2, 1), (2, -1, 2))
        for row in core.MOVE_TABLE:
            got = core.apply_move(s, row["id"])
            r = [s[0], s[1]]
            i = row["relator"]
            if row["category"] == "inversion":
                r[i] = core.invert(r[i])
            elif row["category"] == "multiplication":
                other = s[row["other"]]
                if row["invert_other"]:
                    other = core.invert(other)
                r[i] = core.free_reduce(r[i] + other)
            else:
                g = row["conjugator"]
                r[i] = core.free_reduce((g,) + r[i] + (-g,))
            self.assertEqual(got, (r[0], r[1]), row)


class TestCanonicalizationTable(unittest.TestCase):
    """DESIGN.md §1.2: exhaustively re-verify the frozen suffix table."""

    TABLE = {
        ((1,), (2,)): 0, ((1,), (-2,)): 1, ((-1,), (2,)): 1,
        ((-1,), (-2,)): 2, ((-2,), (1,)): 4, ((2,), (-1,)): 4,
        ((-2,), (-1,)): 4, ((2,), (1,)): 5,
    }
    TARGET = ((1,), (2,))

    def bfs_cost(self, start, cap=6, maxlen=12):
        if start == self.TARGET:
            return 0
        seen = {start}
        q = deque([(start, 0)])
        while q:
            s, d = q.popleft()
            if d >= cap:
                continue
            for m in range(14):
                t = core.apply_move(s, m)
                if len(t[0]) + len(t[1]) > maxlen or t in seen:
                    continue
                if t == self.TARGET:
                    return d + 1
                seen.add(t)
                q.append((t, d + 1))
        return None

    def test_costs_match_frozen_table(self):
        for state, cost in self.TABLE.items():
            self.assertEqual(self.bfs_cost(state), cost, state)

    def test_loose_trivial_states_are_exactly_eight(self):
        loose = [((a,), (b,)) for a in (1, -1, 2, -2) for b in (1, -1, 2, -2)
                 if abs(a) != abs(b)]
        self.assertEqual(len(loose), 8)
        self.assertEqual(set(loose), set(self.TABLE))


if __name__ == "__main__":
    unittest.main()
