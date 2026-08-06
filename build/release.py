#!/usr/bin/env python3
"""Export and verify the ACMS-public release package (DESIGN.md §9, §10.1).

The public tree lives in-repo at ``competition/`` (single source of
truth, IGP24-public-aligned); this script only filters, verifies, and
stamps — it generates no content. Duties:

  1. verify the three hashes: recompute every instance_hash, the
     manifest_hash, and the move_spec_hash from the frozen move table,
     and check competition.yaml quotes the same values
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
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))

from acms_verify import canon, core  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "dist" / "ACMS-public"

ROOT_README = """\
# ACMS-public — Andrews–Curtis Competition, Miller–Schupp Phase

Public data, rules, and reference tools for the ACMS competition,
organized by **sairmath**: trivializing Miller–Schupp presentations
with atomic Andrews–Curtis moves, plus a Lean 4 counterexample track.

The public reference tools are intentionally small. The official
competition system runs the production evaluator, while this repository
exposes the core mathematical checks used for reproducibility.

## Start here

1. Read `competition/rules/overview.md` (the task and scoring), then
   `competition/rules/evaluation.md` (exact verifier semantics).
2. Explore `competition/challenges/` — the frozen 550-challenge
   manifest, the machine-readable move spec, the full MS-1190 metadata,
   and 424 known trivializations as training data.
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
    move_spec = json.loads((src / "challenges" / "move_spec.json").read_text())
    spec_hash = canon.move_spec_hash(core.MOVE_TABLE)
    assert manifest["move_spec_hash"] == spec_hash
    assert canon.move_spec_hash(move_spec["moves"]) == spec_hash
    recomputed = [
        canon.instance_hash(c["challenge_id"], c["generators"],
                            c["initial_relators"], c["target_relators"],
                            c["move_spec_version"], spec_hash)
        for c in manifest["challenges"]]
    assert recomputed == [c["instance_hash"] for c in manifest["challenges"]]
    assert canon.manifest_hash(recomputed) == manifest["manifest_hash"]
    assert len(manifest["challenges"]) == 550
    yaml_text = (src / "competition.yaml").read_text()
    assert 'move_spec_hash: "%s"' % spec_hash in yaml_text
    assert 'manifest_hash: "%s"' % manifest["manifest_hash"] in yaml_text
    assert "challenge_count: 550" in yaml_text

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
    env = {"PYTHONPATH": "", "PATH": "/usr/bin:/bin"}
    sh(sys.executable, "-m", "acms_verify",
       "--golden", comp / "challenges" / "golden_vectors.json",
       cwd=comp / "tools" / "verifier", env=env)
    sh(sys.executable, "-m", "acms_verify",
       "--manifest", comp / "challenges" / "manifest.json", "--check-hashes",
       cwd=comp / "tools" / "verifier", env=env)

    # 4. nothing from the internal directories may leak: the package
    # holds exactly {README.md, LICENSE, competition/}, no path segment
    # named "server", and no server-module basenames.
    top = sorted(q.name for q in OUT.iterdir())
    assert top == ["LICENSE", "NOTICE", "README.md", "competition"], top
    server_files = {p.name for p in (REPO / "server").rglob("*.py")
                    if "__pycache__" not in p.parts}
    for p in OUT.rglob("*"):
        assert "server" not in (q.lower() for q in p.relative_to(OUT).parts), p
        if p.is_file() and p.suffix == ".py":
            assert p.name not in server_files or p.name == "__init__.py", p

    files = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())
    print("\n".join(files))
    print(f"\nOK: ACMS-public exported to {OUT} ({len(files)} files), "
          f"all hashes verified, golden vectors green, no internal leakage")


if __name__ == "__main__":
    main()
