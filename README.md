# ACC — The Andrews–Curtis Conjecture Competition (development repository)

Backend for ACC: trivializing balanced presentations of the trivial
group with atomic Andrews–Curtis moves over a frozen 10,115-instance
pool, plus a counterexample track for purported disproofs of the
conjecture. Structured after SAIR's IGP24 competition.

ACC is co-organized by (in alphabetical order by surname): Lucas Fagan,
Sergei Gukov, Terence Tao.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `competition/` | **The IGP24-aligned public tree** (single source of truth): `rules/`, frozen `challenges/` data + hashes, `examples/`, `tools/verifier/` (reference verifier), `tools/lean/`, `competition.yaml` | yes — exported verbatim by `build/release.py` |
| `spec/` | Internal design doc (`DESIGN.md`) | no |
| `build/` | `sync_dataset.py` + `build_manifest_v2.py` (regenerate the frozen data from the SAIR dataset release), `build_manifest.py` (v1 manifest library), `release.py` (exports + verifies the public package), `checks/` (original verification scripts) | no |
| `tests/` | Verifier + frozen-data acceptance tests | no |
| `server/` | Scoring engine (P2); submission service pending decision O-1 | no |
| `lean/` | Formalization workspace (O-3 spike → P4) | no |
| `reference/` | Frozen prototype `index.html` — read-only, never a production dependency | no |

## Commands

```sh
# regenerate frozen data from the SAIR dataset release
python3 build/sync_dataset.py --release ../sair_dataset/release
python3 build/build_manifest_v2.py

# full test suite (verifier + data + scoring)
python3 -m unittest discover -s tests -t .
(cd server && python3 -m unittest discover -s tests)

# Lean spike
(cd lean/Competition && lake build)

# assemble + verify the public release package
python3 build/release.py            # -> dist/ACMS-public
```

**Freeze discipline** (DESIGN.md §9.3): before public launch, freeze
`competition/challenges/manifest.json` + `move_spec.json` in a commit,
and record that commit hash in `competition/competition.yaml`.
