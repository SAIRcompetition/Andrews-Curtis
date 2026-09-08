#!/usr/bin/env python3
"""Export and verify the ACMS-public release package (DESIGN.md §9, §10.1).

The public tree lives in-repo at ``competition/`` (single source of
truth, IGP24-public-aligned); this script only filters, verifies, and
stamps — it generates no content. Duties:

  1. verify every hash: recompute each instance_hash under the move
     spec ITS challenge names, the manifest_hash, and both
     move_spec_hash values from the frozen move tables, and check
     competition.yaml quotes the same values
  2. copy LICENSE + competition/ verbatim into the output directory and
     write the public root README
  3. run the golden vectors and the hash check FROM THE COPIED PACKAGE
     in an isolated environment; abort on any failure
  4. assert the package contains nothing from server/ or any other
     internal directory

Aborts loudly on any check failure; a partial tree is left for
inspection but must never be published.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import canon, specs  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "dist" / "ACMS-public"

#: 10115 presentations x 2 trivialization tracks.
PRESENTATION_COUNT = 10115
CHALLENGE_COUNT = 2 * PRESENTATION_COUNT

#: Directories that hold organizer-only material and must never appear
#: in the export, at any depth.
INTERNAL_DIRS = ("server", "build", "spec", "reference", "tests", "private")

#: Provenance/difficulty vocabulary that must not survive into the
#: exported manifest (mirrors build/build_manifest_v2.py leak_check).
BANNED_TOKENS = ("tier", "pool", "family", "provenance", "w_vector",
                 "status_at_freeze", "MS-", "AUTH-", "INTL", "ACP-") + tuple(
                     "T%d_" % i for i in range(6))

#: The subset of the above that the move specs and the training files
#: must also pass.  ``family`` and ``w_vector`` are legitimate,
#: published metadata field names in training_424.json (and therefore in
#: stable_training_424.json), so they are not private vocabulary there;
#: everything else — private id prefixes and difficulty vocabulary — is
#: still forbidden.  :func:`main` proves the rule is exactly "what
#: training_424.json passes" by running it on training_424.json and
#: move_spec.json too.
AUX_BANNED_TOKENS = tuple(t for t in BANNED_TOKENS
                          if t not in ("family", "w_vector"))

#: Files scanned with AUX_BANNED_TOKENS: the frozen pair first, so a
#: rule that would reject them fails the release instead of silently
#: passing the new pair.
AUX_SCANNED = ("move_spec.json", "training_424.json",
               "stable_move_spec.json", "stable_training_424.json")

ROOT_README = """\
# ACC — The Andrews–Curtis Conjecture Competition (public package)

Public data, rules, and reference tools for ACC, co-organized by
Lucas Fagan, Sergei Gukov, and Terence Tao: trivializing balanced
presentations of the trivial group with atomic Andrews–Curtis moves,
plus expert-reviewed proof-or-disproof tracks.

Four tracks over one frozen pool of 10,115 presentations:

| Track | Challenge ids | Move spec | Target |
|---|---|---|---|
| AC trivialization | `ac-v1-NNNNN` | `ac-r2-v1` (14 moves, rank 2) | the ordered pair (x, y) |
| Stable AC trivialization | `sac-v1-NNNNN` | `sac-r8-v1` (257 moves, rank ≤ 8) | the empty presentation |
| AC proof or disproof | — | — | PDF + expert review |
| Stable AC proof or disproof | — | — | PDF + expert review |

`sac-v1-N` is the same presentation as `ac-v1-N`; the two trivialization
tracks are scored independently, 20,230 challenges in all.

The public reference tools are intentionally small. The official
competition system runs the production evaluator, while this repository
exposes the core mathematical checks used for reproducibility.

## Start here

1. Read `competition/rules/overview.md` (the task and scoring), then
   `competition/rules/evaluation.md` (exact verifier semantics).
2. Explore `competition/challenges/` — the frozen 20,230-challenge
   manifest, the two machine-readable move specs, the full MS-1190
   metadata, and 424 known trivializations per track as training data.
3. Self-check with the reference verifier:
   `cd competition/tools/verifier && python3 -m acms_verify --golden
   ../../challenges/golden_vectors.json`

## Layout

    competition/
      competition.yaml        machine-readable metadata
      rules/                  overview.md, evaluation.md
      challenges/             frozen data + hashes (see its README)
      examples/               sample submission
      tools/verifier/         Python reference verifier (stdlib only)
      tools/lean/             Lean counterexample track (toolchain frozen at P4)
"""


def sh(*args, **kw):
    print("  $", " ".join(str(a) for a in args))
    return subprocess.run([str(a) for a in args], check=True, **kw)


def main():
    src = REPO / "competition"

    # 1. hash verification against the in-repo source of truth
    manifest = json.loads((src / "challenges" / "manifest.json").read_text())
    problems = specs.check_move_specs(manifest.get("move_specs"))
    assert not problems, problems
    spec_hashes = specs.move_spec_hashes()
    # Every declared spec file on disk must carry the same table.
    for entry in manifest["move_specs"]:
        version = entry["move_spec_version"]
        on_disk = json.loads(
            (src / "challenges" / entry["file"]).read_text())
        assert on_disk["move_spec_version"] == version, entry["file"]
        assert on_disk["move_spec_hash"] == spec_hashes[version], entry["file"]
        assert canon.move_spec_hash(on_disk["moves"]) == spec_hashes[version], \
            entry["file"]
        assert on_disk["target_relators"] == entry["target_relators"]

    recomputed = [
        canon.instance_hash(c["challenge_id"], c["generators"],
                            c["initial_relators"], c["target_relators"],
                            c["move_spec_version"],
                            spec_hashes[c["move_spec_version"]])
        for c in manifest["challenges"]]
    assert recomputed == [c["instance_hash"] for c in manifest["challenges"]]
    assert canon.manifest_hash(recomputed) == manifest["manifest_hash"]
    assert len(manifest["challenges"]) == CHALLENGE_COUNT, \
        len(manifest["challenges"])
    assert manifest["challenge_count"] == CHALLENGE_COUNT
    assert manifest["presentation_count"] == PRESENTATION_COUNT

    # Each presentation appears once per track, with identical inputs.
    by_prefix = {}
    for c in manifest["challenges"]:
        prefix, _, number = c["challenge_id"].rpartition("-")
        by_prefix.setdefault(prefix + "-", {})[number] = c
    assert sorted(by_prefix) == ["ac-v1-", "sac-v1-"], sorted(by_prefix)
    ac, sac = by_prefix["ac-v1-"], by_prefix["sac-v1-"]
    assert len(ac) == len(sac) == PRESENTATION_COUNT
    assert set(ac) == set(sac)
    for number, a in ac.items():
        s_ = sac[number]
        assert a["generators"] == s_["generators"], number
        assert a["initial_relators"] == s_["initial_relators"], number
        assert a["target_relators"] == [[1], [2]], number
        assert s_["target_relators"] == [], number
        assert a["move_spec_version"] == "ac-r2-v1", number
        assert s_["move_spec_version"] == "sac-r8-v1", number

    yaml_text = (src / "competition.yaml").read_text()
    for entry in manifest["move_specs"]:
        assert "  - version: %s\n" % entry["move_spec_version"] in yaml_text
        assert '    hash: "%s"\n' % entry["move_spec_hash"] in yaml_text
        assert "    file: challenges/%s\n" % entry["file"] in yaml_text
        assert "    max_rank: %d\n" % entry["max_rank"] in yaml_text
        assert "    id_prefix: %s\n" % entry["id_prefix"] in yaml_text
    assert 'manifest_hash: "%s"' % manifest["manifest_hash"] in yaml_text
    assert "challenge_count: %d" % CHALLENGE_COUNT in yaml_text
    assert "presentation_count: %d" % PRESENTATION_COUNT in yaml_text
    for track in ("ac_trivialization", "stable_ac_trivialization",
                  "ac_proof_or_disproof", "stable_ac_proof_or_disproof"):
        assert "  %s:\n" % track in yaml_text, track

    # 2. verbatim export
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(src, OUT / "competition",
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    shutil.copy2(REPO / "LICENSE", OUT / "LICENSE")
    shutil.copy2(REPO / "NOTICE", OUT / "NOTICE")
    (OUT / "README.md").write_text(ROOT_README)

    # 3. golden vectors + hash check, executed from the copied package only
    comp = OUT / "competition"
    # PYTHONDONTWRITEBYTECODE: the two runs below import acms_verify from
    # inside the copied tree, and without it CPython leaves __pycache__
    # directories in the package that is about to ship.
    env = {"PYTHONPATH": "", "PATH": "/usr/bin:/bin",
           "PYTHONDONTWRITEBYTECODE": "1"}
    sh(sys.executable, "-m", "acms_verify",
       "--golden", comp / "challenges" / "golden_vectors.json",
       cwd=comp / "tools" / "verifier", env=env)
    sh(sys.executable, "-m", "acms_verify",
       "--manifest", comp / "challenges" / "manifest.json", "--check-hashes",
       cwd=comp / "tools" / "verifier", env=env)

    # 4. nothing from the internal directories may leak: the package
    # holds exactly {README.md, LICENSE, NOTICE, competition/}, no path
    # segment named server/build/spec/reference/tests/private, and no
    # server-module or builder basenames.
    top = sorted(q.name for q in OUT.iterdir())
    assert top == ["LICENSE", "NOTICE", "README.md", "competition"], top
    internal_files = {p.name for p in (REPO / "server").rglob("*.py")
                      if "__pycache__" not in p.parts}
    internal_files |= {p.name for p in (REPO / "build").rglob("*.py")
                       if "__pycache__" not in p.parts}
    for p in OUT.rglob("*"):
        parts = [q.lower() for q in p.relative_to(OUT).parts]
        for bad in INTERNAL_DIRS:
            assert bad not in parts, (bad, p)
        if p.is_file() and p.suffix == ".py":
            assert p.name not in internal_files or p.name == "__init__.py", p
        assert p.name not in ("scored_pool_source.jsonl", "SOURCES.json",
                              "challenge_map_private.tsv",
                              "pool_stats.json"), p

    # 5. the exported manifest still carries no provenance vocabulary and
    # no private identifier (re-run of build_manifest_v2.leak_check on the
    # bytes that actually ship).
    exported = (comp / "challenges" / "manifest.json").read_text(
        encoding="utf-8")
    for token in BANNED_TOKENS:
        assert token not in exported, "banned token %r in exported manifest" \
            % (token,)
    freeze = json.loads(exported)["freeze_date"]
    hit = re.search(r"[A-Z]", exported.replace(freeze, ""))
    assert hit is None, "unexpected uppercase in exported manifest at %d" % (
        hit.start() if hit else -1)

    # 5b. the move specs and the training files carry published metadata
    # vocabulary but must still carry no private identifier.  The frozen
    # ac-r2-v1 pair is scanned first, so the rule is demonstrably the one
    # training_424.json already passes.
    for name in AUX_SCANNED:
        text = (comp / "challenges" / name).read_text(encoding="utf-8")
        for token in AUX_BANNED_TOKENS:
            assert token not in text, "banned token %r in %s" % (token, name)
    print("leak check: %s clean (%d tokens each)"
          % (", ".join(AUX_SCANNED), len(AUX_BANNED_TOKENS)))

    files = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())
    print("\n".join(files))
    print(f"\nOK: ACMS-public exported to {OUT} ({len(files)} files), "
          f"{CHALLENGE_COUNT} challenges over {PRESENTATION_COUNT} "
          f"presentations x {len(manifest['move_specs'])} trivialization "
          f"tracks, all hashes verified, golden vectors green, no internal "
          f"leakage")


if __name__ == "__main__":
    main()
