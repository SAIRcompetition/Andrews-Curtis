"""ACMS scoring engine (DESIGN.md §5).

The only mutable state is ``best[(team, challenge)]`` — the minimal
accepted atomic path length — plus the immutable First Solver registry.
The leaderboard is a pure function of that state, recomputed in full
after every accepted solution (§5.2); no incremental patching.

All scores are exact rationals (``fractions.Fraction``, §5.5): floats
are forbidden because different machines or summation orders would
otherwise produce different totals.  Display rounding is
round-half-even to 4 decimal places, applied only at serialization.
"""

from fractions import Fraction


def display_score(value):
    """Exact rational -> display string, round-half-even, 4 decimals.

    Pure integer arithmetic on the exact value — a Decimal division
    would round once at context precision and once at quantize, which
    can misround exact near-tie rationals (§5.5 forbids that).
    """
    num, den = value.numerator, value.denominator
    sign = "-" if num < 0 else ""
    q, r = divmod(abs(num) * 10000, den)
    if 2 * r > den or (2 * r == den and q % 2 == 1):
        q += 1
    return "%s%d.%04d" % (sign, q // 10000, q % 10000)


class ScoringEngine:
    def __init__(self, manifest, verifier_version):
        self.manifest_hash = manifest["manifest_hash"]
        self.verifier_version = verifier_version
        # V_i is read from the manifest and multiplied through, never
        # assumed uniform (D-8).
        self.base_score = {c["challenge_id"]: Fraction(c["base_score"])
                           for c in manifest["challenges"] if c["scored"]}
        self.best = {}          # (team, challenge_id) -> min length
        self.best_since = {}    # (team, challenge_id) -> (received_at, submission_id)
        self.first_solver = {}  # challenge_id -> frozen dict (§5.3)
        self._last_totals = {}
        self._total_since = {}  # team -> event key when current total was reached
        self.scoring_runs = []

    # -- ingest ----------------------------------------------------------
    def record_accepted(self, team, challenge_id, length,
                        received_at, submission_id):
        """Register one accepted solution and recompute.

        ``(received_at, submission_id)`` totally orders events;
        ``submission_id`` is monotonically increasing and breaks
        same-millisecond ties (§5.3).  Returns the new scoring run.
        """
        if challenge_id not in self.base_score:
            raise KeyError("not a scored challenge: %r" % (challenge_id,))
        if type(length) is not int or length < 0:
            raise ValueError("length must be a non-negative int")

        # First Solver: argmin over accepted solutions of
        # (received_at, submission_id) — robust to out-of-order
        # ingestion — and never changed by later, shorter paths
        # (§5.3, acceptance row 9).
        fs = self.first_solver.get(challenge_id)
        if fs is None or ((received_at, submission_id)
                          < (fs["received_at"], fs["submission_id"])):
            self.first_solver[challenge_id] = {
                "team": team, "received_at": received_at,
                "submission_id": submission_id,
            }

        key = (team, challenge_id)
        if key not in self.best or length < self.best[key]:
            self.best[key] = length
            self.best_since[key] = (received_at, submission_id)
        return self.recompute((received_at, submission_id))

    # -- pure recomputation (§5.2) --------------------------------------
    def recompute(self, event_key):
        by_challenge = {}
        for (team, cid), length in self.best.items():
            by_challenge.setdefault(cid, {})[team] = length

        points = {}   # team -> {cid: Fraction}
        for cid, table in by_challenge.items():
            lstar = min(table.values())
            holders = [t for t, length in table.items() if length == lstar]
            k = len(holders)
            share = self.base_score[cid] / (1 << (k - 1))  # V_i * 2^(1-k)
            for t in holders:
                points.setdefault(t, {})[cid] = share

        teams = {t for t, _ in self.best}
        totals = {t: sum(points.get(t, {}).values(), Fraction(0))
                  for t in teams}

        # Tie-break: earliest time-of-current-total.  A team's clock
        # resets whenever recomputation changes its total (others'
        # submissions can change it too).
        for t in teams:
            if self._last_totals.get(t) != totals[t]:
                self._total_since[t] = event_key
        self._last_totals = dict(totals)

        ranked = sorted(teams,
                        key=lambda t: (-totals[t], self._total_since[t], t))
        run = {
            "scoring_run_id": len(self.scoring_runs) + 1,
            "manifest_hash": self.manifest_hash,
            "verifier_version": self.verifier_version,
            "event": {"received_at": event_key[0],
                      "submission_id": event_key[1]},
            "leaderboard": [
                {"rank": i + 1, "team": t,
                 "total": totals[t],
                 "total_display": display_score(totals[t]),
                 "solved": len(points.get(t, {}))}
                for i, t in enumerate(ranked)
            ],
            "points": points,
        }
        self.scoring_runs.append(run)
        return run

    # -- public read API helpers (§5.6 obligations, §8) ------------------
    def challenge_view(self, challenge_id, for_team=None):
        """The scoring fields of ``GET /challenges/:id`` — enough for a
        frontend to show 'how far am I from being zeroed'."""
        table = {t: length for (t, c), length in self.best.items()
                 if c == challenge_id}
        view = {
            "challenge_id": challenge_id,
            "base_score": self.base_score[challenge_id],
            "current_best_length": None,
            "current_best_solver": None,
            "k_teams": 0,
            "first_solver": None,
            "first_solved_at": None,
        }
        fs = self.first_solver.get(challenge_id)
        if fs:
            view["first_solver"] = fs["team"]
            view["first_solved_at"] = fs["received_at"]
        if table:
            lstar = min(table.values())
            holders = sorted(t for t, length in table.items()
                             if length == lstar)
            best_holder = min(holders,
                              key=lambda t: self.best_since[(t, challenge_id)])
            view["current_best_length"] = lstar
            view["current_best_solver"] = best_holder
            view["k_teams"] = len(holders)
        if for_team is not None:
            view["my_best_length"] = table.get(for_team)
        return view
