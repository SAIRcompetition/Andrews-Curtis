"""sac-r8-v1 core semantics: the generated 257-row move table, rank-aware
applicability, destabilization relabeling, and the canonicalization law.

Everything is recomputed from the move table itself — no builder import,
no hardcoded row dumps — so a change to the generator that produced the
table fails here rather than silently reshaping the frozen spec.
"""

import collections
import itertools
import random
import unittest
from collections import deque

from acms_verify import canon, core, stable_core
from tests import util

TARGET = ()

#: Category -> row count.  14 rows come from the ac-r2-v1 table
#: (2 inversion, 4 multiplication, 8 conjugation) and the rest are new.
EXPECTED_CATEGORY_COUNTS = {
    "inversion": 2 + 6,
    "multiplication": 4 + 108,
    "conjugation": 8 + 120,
    "stabilize": 1,
    "destabilize": 8,
}
EXPECTED_NEW_COUNTS = {"stabilize": 1, "destabilize": 8, "inversion": 6,
                       "multiplication": 108, "conjugation": 120}


class TestMoveTableShape(unittest.TestCase):
    def test_row_count_and_ids(self):
        self.assertEqual(stable_core.NUM_MOVES, 257)
        self.assertEqual(len(stable_core.MOVE_TABLE), 257)
        self.assertEqual([r["id"] for r in stable_core.MOVE_TABLE],
                         list(range(257)))

    def test_first_fourteen_rows_are_the_ac_table(self):
        self.assertEqual(tuple(stable_core.MOVE_TABLE[:14]), core.MOVE_TABLE)
        # ...and the ac-r2-v1 spec hash is therefore unaffected.
        self.assertNotEqual(canon.move_spec_hash(stable_core.MOVE_TABLE),
                            canon.move_spec_hash(core.MOVE_TABLE))

    def test_category_counts(self):
        counts = collections.Counter(r["category"]
                                     for r in stable_core.MOVE_TABLE)
        self.assertEqual(dict(counts), EXPECTED_CATEGORY_COUNTS)
        new = collections.Counter(r["category"]
                                  for r in stable_core.MOVE_TABLE[14:])
        self.assertEqual(dict(new), EXPECTED_NEW_COUNTS)

    def test_id_blocks(self):
        by_cat = collections.defaultdict(list)
        for r in stable_core.MOVE_TABLE[14:]:
            by_cat[r["category"]].append(r["id"])
        self.assertEqual(by_cat["stabilize"], [14])
        self.assertEqual(by_cat["destabilize"], list(range(15, 23)))
        self.assertEqual(by_cat["inversion"], list(range(23, 29)))
        self.assertEqual(by_cat["multiplication"], list(range(29, 137)))
        self.assertEqual(by_cat["conjugation"], list(range(137, 257)))

    def test_every_row_is_reachable_and_unique(self):
        keys = set()
        for r in stable_core.MOVE_TABLE:
            key = tuple(sorted((k, v) for k, v in r.items() if k != "id"))
            self.assertNotIn(key, keys, r)
            keys.add(key)

    def test_destabilize_and_stabilize_have_no_inverse_id(self):
        for r in stable_core.MOVE_TABLE:
            if r["category"] in ("stabilize", "destabilize"):
                self.assertIsNone(r["inverse"], r)
                self.assertIsNone(stable_core.INVERSE_MOVE[r["id"]], r)
            else:
                self.assertIsInstance(r["inverse"], int, r)

    def test_inverse_column_is_an_involution_on_the_ac_type_rows(self):
        inv = stable_core.INVERSE_MOVE
        rank_preserving = [r["id"] for r in stable_core.MOVE_TABLE
                           if r["category"] not in ("stabilize",
                                                    "destabilize")]
        self.assertEqual(len(rank_preserving), 248)
        self.assertEqual(sorted(inv[m] for m in rank_preserving),
                         rank_preserving)
        for m in rank_preserving:
            self.assertEqual(inv[inv[m]], m, m)

    def test_relator_and_generator_indices_in_range(self):
        for r in stable_core.MOVE_TABLE:
            if "relator" in r:
                self.assertIn(r["relator"], range(stable_core.MAX_RANK), r)
            if "other" in r:
                self.assertIn(r["other"], range(stable_core.MAX_RANK), r)
                self.assertNotEqual(r["other"], r["relator"], r)
            if "conjugator" in r:
                self.assertTrue(1 <= abs(r["conjugator"])
                                <= stable_core.MAX_RANK, r)

    def test_generator_names(self):
        self.assertEqual(stable_core.GENERATOR_NAMES,
                         ("x", "y", "g3", "g4", "g5", "g6", "g7", "g8"))
        self.assertEqual(stable_core.generator_name(-1), "x")
        self.assertEqual(stable_core.generator_name(8), "g8")


class TestApplyMove(unittest.TestCase):
    """apply_move must do exactly what the declarative row says."""

    def reference(self, state, row):
        """Independent re-implementation from the row's parameters."""
        cat = row["category"]
        k = len(state)
        if cat == "stabilize":
            return state + ((k + 1,),) if k < stable_core.MAX_RANK else None
        i = row["relator"]
        if i >= k:
            return None
        words = list(state)
        if cat == "destabilize":
            w = words[i]
            if len(w) != 1 or w[0] <= 0:
                return None
            g = w[0]
            rest = words[:i] + words[i + 1:]
            if any(abs(a) == g for other in rest for a in other):
                return None
            out = []
            for other in rest:
                out.append(tuple(
                    (abs(a) - 1) * (1 if a > 0 else -1) if abs(a) > g else a
                    for a in other))
            return tuple(out)
        if cat == "inversion":
            words[i] = core.invert(words[i])
        elif cat == "multiplication":
            j = row["other"]
            if j >= k:
                return None
            other = state[j]
            if row["invert_other"]:
                other = core.invert(other)
            words[i] = core.free_reduce(words[i] + other)
        else:
            c = row["conjugator"]
            if abs(c) > k:
                return None
            words[i] = core.free_reduce((c,) + words[i] + (-c,))
        return tuple(words)

    def random_states(self, seed=20260911, count=40):
        rng = random.Random(seed)
        out = []
        for _ in range(count):
            k = rng.choice((1, 2, 3, 4))
            state = []
            for _ in range(k):
                n = rng.randint(0, 4)
                word = core.free_reduce(
                    [rng.choice([g for g in range(-k, k + 1) if g])
                     for _ in range(n)])
                state.append(word)
            out.append(tuple(state))
        return out

    def test_apply_matches_the_table_row(self):
        states = self.random_states() + [
            ((1,), (2,)), ((2,), (1,)), ((1, 2), (1, 1, 2)),
            ((1,), (2,), (3,)), ((1, 2, -1), (2,), (3, 1), (4,)),
            ((-1,), (-2,), (3, -3)),
        ]
        for state in states:
            for row in stable_core.MOVE_TABLE:
                got, reason = stable_core.apply_move(state, row["id"])
                want = self.reference(state, row)
                if want is None:
                    self.assertIsNone(got, (state, row))
                    self.assertIn(reason, stable_core.NOT_APPLICABLE_REASONS)
                else:
                    self.assertIsNone(reason, (state, row))
                    self.assertEqual(got, want, (state, row))

    def test_results_stay_freely_reduced(self):
        for state in self.random_states(seed=7, count=25):
            for m in range(stable_core.NUM_MOVES):
                got, reason = stable_core.apply_move(state, m)
                if reason is None:
                    for w in got:
                        self.assertEqual(core.free_reduce(w), w, (state, m))

    def test_inverse_move_undoes_rank_preserving_moves(self):
        states = [((1, 2, 1), (2, -1, 2)), ((1,), (2,), (3, 1, -3)),
                  ((1, 2), (3,), (2, -1), (4, 4))]
        for state in states:
            for row in stable_core.MOVE_TABLE:
                if row["inverse"] is None:
                    continue
                mid = stable_core.apply_move(state, row["id"])
                if mid[1] is not None:
                    continue
                back, reason = stable_core.apply_move(mid[0], row["inverse"])
                self.assertIsNone(reason, (state, row))
                self.assertEqual(back, state, (state, row))

    def test_bad_move_id_raises(self):
        for bad in (-1, 257, 1000, 1.5, "3", None, True):
            with self.assertRaises(ValueError):
                stable_core.apply_move(((1,), (2,)), bad)


class TestDestabilize(unittest.TestCase):
    def destab(self, state, i):
        return stable_core.apply_move(state, 15 + i)

    def test_relabels_larger_generators_down_by_one(self):
        # rank 4, drop g2: g3 -> g2 and g4 -> g3, signs preserved.
        state = ((1, 3, -4), (2,), (-3, 4, 1), (4, -3))
        got, reason = self.destab(state, 1)
        self.assertIsNone(reason)
        self.assertEqual(got, ((1, 2, -3), (-2, 3, 1), (3, -2)))
        self.assertEqual(len(got), 3)

    def test_dropping_the_highest_generator_relabels_nothing(self):
        state = ((1, 2), (2, -1), (3,))
        got, reason = self.destab(state, 2)
        self.assertIsNone(reason)
        self.assertEqual(got, ((1, 2), (2, -1)))

    def test_dropping_the_only_relator_gives_the_empty_presentation(self):
        state, reason = self.destab(((1,),), 0)
        self.assertIsNone(reason)
        self.assertEqual(state, ())

    def test_relator_out_of_rank(self):
        self.assertEqual(self.destab(((1,), (2,)), 2),
                         (None, "relator_out_of_rank"))

    def test_precondition_rejects_non_single_letters(self):
        for state, i in ((((1, 2), (2,)), 0), (((), (2,)), 0),
                         (((1, 1), (2,)), 0)):
            self.assertEqual(self.destab(state, i),
                             (None, "destabilize_precondition"), (state, i))

    def test_precondition_rejects_inverted_letters(self):
        self.assertEqual(self.destab(((-1,), (2,)), 0),
                         (None, "destabilize_precondition"))

    def test_precondition_rejects_a_shared_generator(self):
        for other in ((2, 1), (2, -1), (1,)):
            self.assertEqual(self.destab(((1,), other), 0),
                             (None, "destabilize_precondition"), other)

    def test_max_rank_exceeded(self):
        state = tuple((g,) for g in range(1, stable_core.MAX_RANK + 1))
        self.assertEqual(len(state), stable_core.MAX_RANK)
        self.assertEqual(stable_core.apply_move(state, 14),
                         (None, "max_rank_exceeded"))
        smaller = state[:-1]
        got, reason = stable_core.apply_move(smaller, 14)
        self.assertIsNone(reason)
        self.assertEqual(got, state)

    def test_generator_out_of_rank(self):
        # conjugating r0 by y at rank 1.
        self.assertEqual(stable_core.apply_move(((1,),), 8),
                         (None, "generator_out_of_rank"))
        # ...and by g3 at rank 2 (id 137 = r0 <- g3 r0 g3^-1).
        row = next(r for r in stable_core.MOVE_TABLE
                   if r["category"] == "conjugation" and r["relator"] == 0
                   and r["conjugator"] == 3)
        self.assertEqual(stable_core.apply_move(((1,), (2,)), row["id"]),
                         (None, "generator_out_of_rank"))

    def test_every_reason_is_reachable(self):
        seen = set()
        cases = [(((1,), (2,)), 2 + 15), (((1,),), 8),
                 (tuple((g,) for g in range(1, 9)), 14),
                 (((1, 2), (2,)), 15)]
        for state, m in cases:
            seen.add(stable_core.apply_move(state, m)[1])
        self.assertEqual(seen, set(stable_core.NOT_APPLICABLE_REASONS))


def law(state):
    return len(state) + sum(1 for w in state if w[0] < 0)


def bfs_cost(start, cap=None, extra_length=3, extra_rank=1):
    """Shortest applicable-move path to the empty presentation inside a
    bounded envelope (see build/checks/stable_canon.py)."""
    if start == TARGET:
        return 0, []
    cap = law(start) if cap is None else cap
    max_total = sum(len(w) for w in start) + extra_length
    max_rank = min(len(start) + extra_rank, stable_core.MAX_RANK)
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
    out = []
    for perm in itertools.permutations(range(1, k + 1)):
        for signs in itertools.product((1, -1), repeat=k):
            out.append(tuple((s * g,) for g, s in zip(perm, signs)))
    return out


class TestCanonicalization(unittest.TestCase):
    """The k + negatives law, re-derived by breadth-first search."""

    def test_rank2_loose_trivial_states(self):
        states = single_letter_states(2)
        self.assertEqual(len(states), 8)
        costs = {}
        for state in states:
            cost, path = bfs_cost(state)
            self.assertEqual(cost, law(state), state)
            costs[state] = cost
        self.assertEqual(costs[((1,), (2,))], 2)
        self.assertEqual(costs[((2,), (1,))], 2)
        self.assertEqual(sorted(costs.values()), [2, 2, 3, 3, 3, 3, 4, 4])

    def test_both_two_move_suffixes_work_from_xy_and_yx(self):
        for start in (((1,), (2,)), ((2,), (1,))):
            for suffix in ([16, 15], [15, 15]):
                state = start
                for m in suffix:
                    state, reason = stable_core.apply_move(state, m)
                    self.assertIsNone(reason, (start, suffix, m))
                self.assertEqual(state, TARGET, (start, suffix))

    def test_rank3_law_on_a_deterministic_subset(self):
        # The full 48-state sweep lives in build/checks/stable_canon.py
        # (~10 s); here a fixed, representative twelve.
        states = single_letter_states(3)
        subset = [states[i] for i in range(0, len(states), 4)]
        self.assertEqual(len(subset), 12)
        for state in subset:
            self.assertEqual(bfs_cost(state)[0], law(state), state)

    def test_published_canonicalization_table_matches(self):
        spec = util.load(util.STABLE_MOVE_SPEC_PATH)
        table = spec["canonicalization_table"]
        self.assertIn("rule", table)
        rows = table["rows"]
        self.assertEqual(len(rows), 8)
        seen = set()
        for row in rows:
            start = tuple(tuple(w) for w in row["final_state"])
            seen.add(start)
            self.assertEqual(row["cost"], len(row["path"]))
            self.assertEqual(row["cost"], law(start), start)
            state = start
            for m in row["path"]:
                state, reason = stable_core.apply_move(state, m)
                self.assertIsNone(reason, row)
            self.assertEqual(state, TARGET, row)
            self.assertEqual(bfs_cost(start)[0], row["cost"], row)
        self.assertEqual(seen, set(single_letter_states(2)))


class TestStableMoveSpecFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = util.load(util.STABLE_MOVE_SPEC_PATH)

    def test_headers(self):
        self.assertEqual(self.spec["move_spec_version"], "sac-r8-v1")
        self.assertEqual(self.spec["move_spec_hash"],
                         canon.move_spec_hash(stable_core.MOVE_TABLE))
        self.assertEqual(self.spec["hash_covers"], "moves")
        self.assertEqual(self.spec["max_rank"], 8)
        self.assertEqual(self.spec["target_relators"], [])
        self.assertEqual(self.spec["generators"], ["x", "y"])
        self.assertEqual(self.spec["extra_generators"],
                         ["g3", "g4", "g5", "g6", "g7", "g8"])

    def test_moves_array_is_the_frozen_table(self):
        self.assertEqual(len(self.spec["moves"]), 257)
        for published, frozen in zip(self.spec["moves"],
                                     stable_core.MOVE_TABLE):
            self.assertEqual(published, dict(frozen))

    def test_letter_encoding_covers_every_generator(self):
        enc = self.spec["letter_encoding"]
        self.assertEqual(len(enc), 16)
        for g, name in enumerate(stable_core.GENERATOR_NAMES, 1):
            self.assertEqual(enc[name], g)
            self.assertEqual(enc[name + "^-1"], -g)

    def test_one_description_per_move_id(self):
        desc = self.spec["descriptions"]
        self.assertEqual(sorted(int(k) for k in desc), list(range(257)))
        ac_spec = util.load(util.MOVE_SPEC_PATH)
        for k, v in ac_spec["descriptions"].items():
            self.assertEqual(desc[k], v, k)
        for v in desc.values():
            self.assertTrue(v.strip())

    def test_notes_state_the_load_bearing_facts(self):
        notes = " ".join(self.spec["notes"])
        for token in ("0-13", "[16, 15]", "inverse: null", "EXACTLY",
                      "E_MOVE_NOT_APPLICABLE", "relabeling"):
            self.assertIn(token, notes, token)


if __name__ == "__main__":
    unittest.main()
