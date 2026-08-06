# ACMS — Andrews–Curtis Competition, Miller–Schupp Phase (development repository)

Backend for the ACMS competition: trivializing Miller–Schupp
presentations with atomic Andrews–Curtis moves, plus a Lean 4
counterexample track. Structured after SAIR's IGP24 competition.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `competition/` | **The IGP24-aligned public tree** (single source of truth): `rules/`, frozen `challenges/` data + hashes, `examples/`, `tools/verifier/` (reference verifier), `tools/lean/`, `competition.yaml` | yes — exported verbatim by `build/release.py` |
| `spec/` | Internal design doc (`DESIGN.md`) + IGP24 rules reference | no |
| `build/` | `build_manifest.py` (regenerates the frozen data from `reference/index.html`), `release.py` (exports + verifies the public package), `checks/` (original verification scripts) | no |
| `tests/` | Verifier + frozen-data acceptance tests | no |
| `server/` | Scoring engine (P2); submission service pending decision O-1 | no |
| `lean/` | Formalization workspace (O-3 spike → P4) | no |
| `reference/` | Frozen prototype `index.html` — read-only, never a production dependency | no |

## Commands

```sh
# regenerate frozen data (asserts every [Verified] figure of DESIGN.md)
python3 build/build_manifest.py

# full test suite (verifier + data + scoring)
python3 -m unittest discover -s tests -t .
(cd server && python3 -m unittest discover -s tests)

# Lean spike
(cd lean/Competition && lake build)

# assemble + verify the public release package
python3 build/release.py            # -> dist/ACMS-public
```

**Freeze discipline** (DESIGN.md §9.3): before public launch, `git init`,
freeze `competition/challenges/manifest.json` + `move_spec.json` in a
commit, and record that commit hash in `competition/competition.yaml`.
