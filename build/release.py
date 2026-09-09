#!/usr/bin/env python3
"""Export and verify the ACMS-public release package (DESIGN.md §9).

The public tree lives in-repo at ``competition/`` (single source of
truth, IGP24-public-aligned). Official exports require announced dates
and a matching Git data freeze; ``--preview`` creates a marked preview.
Duties:

  1. verify the three hashes: recompute every instance_hash, the
     manifest_hash, and the move_spec_hash from the frozen move table,
     and generate competition.yaml with the same values
  2. copy LICENSE + competition/ source files into the output directory,
     excluding local caches and Lean build products, and write the public
     root README
  3. run golden vectors, hash checks, the official Lean source lock check,
     and documented examples FROM THE COPIED PACKAGE in an isolated
     environment; abort on any failure
  4. assert the package contains nothing from server/ or any other
     internal directory

Builds in a temporary directory and replaces the previous output only
after every check passes.
"""

import argparse
from datetime import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "competition" / "tools" / "verifier"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from acms_verify import canon, specs  # noqa: E402
from build_problems import render_problems, serialize as serialize_problems  # noqa: E402
from build_manifest_v2 import render_yaml  # noqa: E402

PRESENTATION_COUNT = 10115
CHALLENGE_COUNT = 2 * PRESENTATION_COUNT
STATE_FIELDS = ("announced_dates", "status", "freeze_date", "freeze_commit", "registration_opens",
                "submissions_open", "prove_submissions_open", "submission_deadline")
DATE_FIELDS = ("freeze_date", "registration_opens", "submissions_open",
               "submission_deadline")

#: Directories that hold organizer-only material and must never appear
#: in the export, at any depth.
INTERNAL_DIRS = ("server", "build", "spec", "reference", "tests", "private")

# Lake dependencies and build products are local state, not public source.
# In particular, exporting .lake/packages would copy complete dependency
# repositories (including their internal directories) into the package.
PUBLIC_COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__", ".DS_Store", ".lake", "*.olean", "*.ilean",
    "*.olean.private", "*.olean.server", "competition.yaml",
)

#: Provenance/difficulty vocabulary that must not survive into the
#: exported manifest (mirrors build/build_manifest_v2.py leak_check).
BANNED_TOKENS = ("tier", "pool", "family", "provenance", "w_vector",
                 "status_at_freeze", "MS-", "AUTH-", "INTL") + tuple(
                     "T%d_" % i for i in range(6))

AUX_BANNED_TOKENS = tuple(t for t in BANNED_TOKENS
                          if t not in ("family", "w_vector"))

#: Files scanned with AUX_BANNED_TOKENS: the frozen pair first, so a
#: rule that would reject them fails the release instead of silently
#: passing the new pair.
AUX_SCANNED = ("tools/verifier/data/move_spec.json", "examples/training_424.json",
               "tools/verifier/data/stable_move_spec.json", "examples/stable_training_424.json")

ROOT_README = """\
# The Andrews–Curtis Conjecture (ACC) Challenge — public package

RELEASE_NOTICE

Co-organized by Caltech and the SAIR Foundation, with Lucas Fagan, Sergei
Gukov, and Terence Tao. [Register on SAIR](https://competition.sair.foundation/competitions/acc).

ACC launches with **Discovery Track on September 11, 2026 at 16:00 UTC**,
followed by **Proof Track on September 20, 2026**. Both tracks cover
**AC** and **Stable AC**. The submission deadline is November 30, 2026.

## Start here

- [Overview](competition/rules/overview.md): background, tracks, schedule,
  registration, and common rules. The prelaunch page contains the same overview.
- [Discovery Track](competition/rules/discovery.md): the 10,115-presentation
  pool, moves, submission format, verifier semantics, and separate AC and
  Stable AC leaderboards.
- [Proof Track](competition/rules/proof.md): full conjecture statements,
  proof/disproof materials, Lean, public versions, and community peer review.

## Discovery Track resources

- [Official problems](competition/problems/README.md): AC and Stable AC
  problem files, each with 10,115 IDs and descriptions.
- [Training data and examples](competition/examples/README.md): 424 separate,
  unscored presentations, runnable submissions, and expected receipts.
- [Python verifier](competition/tools/verifier/README.md): local verification
  instructions and supporting data.

## Proof Track resources

- [Formal definitions](competition/tools/lean/AC.lean): both full conjectures.
- [Lean guide](competition/tools/lean/README.md): instructions for using the
  definitions and optional checks. Using Lean is optional.

The package contains reference mathematical checks. Official submission
handling, leaderboard updates, and public Proof versions and comments are
provided by SAIR. See `competition/competition.yaml` for the recorded
schedule and release metadata. Submission-release status does not indicate
whether registration is open.
"""


def sh(*args, **kw):
    print("  $", " ".join(str(a) for a in args))
    return subprocess.run([str(a) for a in args], check=True, **kw)


def copy_public_tree(src, dst):
    """Copy public sources, including the standalone Lean project, without caches."""
    shutil.copytree(src, dst, ignore=PUBLIC_COPY_IGNORE)


def lean_statement_snapshot(root):
    """Identify the official Lean sources and pinned dependency files."""
    files = ("AC.lean", "lakefile.toml", "lean-toolchain",
             "lake-manifest.json")
    return {
        "schema_version": 1, "conjecture": "AC.Conjecture",
        "disproof": "Not AC.Conjecture", "counterexample": "AC.Counterexample",
        "stable_conjecture": "AC.StableConjecture",
        "stable_disproof": "Not AC.StableConjecture",
        "stable_counterexample": "AC.StableCounterexample",
        "lean_toolchain": "leanprover/lean4:v4.29.1",
        "lean_revision": "f72c35b3f637c8c6571d353742168ab66cc22c00",
        "mathlib_revision": "5e932f97dd25535344f80f9dd8da3aab83df0fe6",
        "files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in sorted(files)},
    }


def verify_lean_statement(root):
    """Reject an export whose official statement differs from its reviewed lock."""
    if json.loads((root / "statement-lock.json").read_text()) != lean_statement_snapshot(root):
        raise ValueError("statement lock mismatch: a source or dependency pin changed")


def validate_public_state(state, yaml_text, manifest):
    """Require the maintained lifecycle state and exported metadata to agree."""
    if set(state) != set(STATE_FIELDS):
        raise ValueError("competition_state.json must contain exactly: "
                         + ", ".join(STATE_FIELDS))
    if state["status"] not in ("prelaunch", "active", "finished"):
        raise ValueError("unsupported competition status")
    for key in STATE_FIELDS:
        match = re.search(r"^" + key + r":\s*(.*?)\s*$", yaml_text, re.MULTILINE)
        if match is None:
            raise ValueError("competition.yaml is missing " + key)
        raw = match.group(1)
        try:
            public_value = json.loads(raw)
        except json.JSONDecodeError:
            public_value = raw
        if public_value != state[key]:
            raise ValueError("competition.yaml disagrees with competition_state.json: " + key)
    if manifest.get("freeze_date") != state["freeze_date"] or any(
            c.get("freeze_date") != state["freeze_date"]
            for c in manifest["challenges"]):
        raise ValueError("manifest freeze dates disagree with competition_state.json")


def validate_track_structure(yaml_text):
    """Check the published two-track/two-problem routing without a YAML dependency."""
    match = re.search(r"^tracks:\n(.*?)(?=^\S|\Z)", yaml_text, re.MULTILINE | re.DOTALL)
    if match is None:
        raise ValueError("competition.yaml is missing tracks")
    blocks = re.findall(r"^  - id: ([a-z_]+)\n(.*?)(?=^  - id: |\Z)",
                        match.group(1), re.MULTILINE | re.DOTALL)
    if [track for track, _ in blocks] != ["discovery", "proof"]:
        raise ValueError("tracks must be Discovery Track and Proof Track, in that order")
    announced_dates = json.loads(re.search(
        r"^announced_dates: (.+)$", yaml_text, re.MULTILINE).group(1))
    expected = {
        "discovery": {
            "ac": {"file": "problems/ac.json", "id_prefix": "ac-v1-", "move_spec_version": "ac-r2-v1"},
            "stable_ac": {"file": "problems/stable_ac.json", "id_prefix": "sac-v1-", "move_spec_version": "sac-r8-v1"},
        },
        "proof": {
            "ac": {"conjecture": "AC.Conjecture", "claims": "[proof, disproof]"},
            "stable_ac": {"conjecture": "AC.StableConjecture", "claims": "[proof, disproof]"},
        },
    }
    for track, block in blocks:
        name = "Discovery Track" if track == "discovery" else "Proof Track"
        if "    name: " + name + "\n" not in block or "    problems:\n" not in block:
            raise ValueError("track metadata missing name or problems: " + track)
        if "    overview: rules/" + track + ".md\n" not in block:
            raise ValueError("track guide mismatch: " + track)
        if track == "proof" and "    statement: rules/proof.md\n" not in block:
            raise ValueError("Proof statement must be included in its track guide")
        date_key = "discovery" if track == "discovery" else "prove"
        time_key = "submissions_open" if track == "discovery" else "prove_submissions_open"
        timestamp = json.loads(re.search(
            r"^" + time_key + r": (.+)$", yaml_text, re.MULTILINE).group(1))
        for key, value in (("opens", announced_dates[date_key]), ("opens_at", timestamp)):
            if "    " + key + ": " + json.dumps(value) + "\n" not in block:
                raise ValueError("track opening disagrees with maintained schedule: " + track)
        problems = re.findall(r"^      - id: ([a-z_]+)\n(.*?)(?=^      - id: |\Z)",
                              block, re.MULTILINE | re.DOTALL)
        if [problem for problem, _ in problems] != ["ac", "stable_ac"]:
            raise ValueError("each track must contain AC and Stable AC problems: " + track)
        for problem, details in problems:
            for field, value in expected[track][problem].items():
                if "        " + field + ": " + value + "\n" not in details:
                    raise ValueError("problem routing mismatch: " + track + "." + problem + "." + field)
        if track == "discovery" and "    leaderboards: independent_per_problem\n" not in block:
            raise ValueError("Discovery requires independent problem leaderboards")


def validate_rule_documents(root):
    """Prevent exporting missing track guides or competing overview versions."""
    rules = root / "rules"
    for name in ("overview.md", "prelaunch.md", "discovery.md", "proof.md"):
        if not (rules / name).is_file():
            raise ValueError("missing competition guide: " + name)
    if (rules / "overview.md").read_bytes() != (rules / "prelaunch.md").read_bytes():
        raise ValueError("overview.md and prelaunch.md must contain the same overview")


def validate_final_state(state, repo=REPO):
    """Fail before touching the output if dates or the Git data freeze are missing."""
    if state["status"] not in ("active", "finished"):
        raise ValueError("official release requires active or finished status; "
                         "use --preview for the prelaunch package")
    dates = {}
    date_fields = DATE_FIELDS
    if state.get("prove_submissions_open") is not None or state["status"] == "finished":
        date_fields += ("prove_submissions_open",)
    for key in date_fields:
        value = state[key]
        if not isinstance(value, str):
            raise ValueError("official release requires an announced " + key)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
            raise ValueError(key + " must be a UTC timestamp in YYYY-MM-DDTHH:MM:SSZ form")
        try:
            dates[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(key + " must be an ISO-8601 timestamp") from exc
        if dates[key].utcoffset() is None:
            raise ValueError(key + " must include a timezone")
    if not (dates["registration_opens"] <= dates["submissions_open"]
            < dates["submission_deadline"]):
        raise ValueError("competition dates must follow registration, Discovery opening, "
                         "and deadline order")
    if "prove_submissions_open" in dates and not (
            dates["submissions_open"] <= dates["prove_submissions_open"]
            < dates["submission_deadline"]):
        raise ValueError("competition dates must follow Discovery opening, Proof opening, "
                         "and deadline order")
    if dates["freeze_date"] > dates["submissions_open"]:
        raise ValueError("data must be frozen no later than submissions open")
    commit = state["freeze_commit"]
    if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise ValueError("official release requires a full Git freeze_commit, not a placeholder")
    resolved = subprocess.run(["git", "rev-parse", "--verify", commit + "^{commit}"],
                              cwd=repo, capture_output=True, text=True)
    if resolved.returncode or resolved.stdout.strip() != commit:
        raise ValueError("freeze_commit is not an available Git commit")
    for name in ("manifest.json", "move_spec.json", "stable_move_spec.json"):
        relative = "competition/tools/verifier/data/" + name
        frozen = subprocess.run(["git", "show", commit + ":" + relative],
                                cwd=repo, capture_output=True)
        if frozen.returncode or frozen.stdout != (repo / relative).read_bytes():
            raise ValueError(name + " does not match freeze_commit; freeze the current data first")


def check_packaged_examples(comp, env):
    """Run the documented CLI from the exported package and compare its receipt."""
    base = [sys.executable, "-m", "acms_verify"]
    examples = comp / "examples"
    expected = json.loads((examples / "sample_verdict.json").read_text())
    cases = [
        (examples / "training_manifest.json", examples / "sample_submission.json", 0, None),
        (comp / "tools/verifier/data/manifest.json", examples / "sample_submission.json", 1,
         "E_UNKNOWN_CHALLENGE"),
        (comp / "tools/verifier/data/manifest.json", examples / "invalid_submission.json", 1,
         "E_NOT_TARGET"),
    ]
    for manifest_path, submission_path, exit_code, error in cases:
        result = subprocess.run(base + ["--manifest", str(manifest_path), "--submission",
                                       str(submission_path), "--pretty"],
                                cwd=comp / "tools/verifier", env=env,
                                capture_output=True, text=True)
        if result.returncode != exit_code:
            raise ValueError("packaged example returned unexpected exit code: " + result.stderr)
        verdict = json.loads(result.stdout)
        if error is None:
            if (verdict != expected or not verdict["accepted"] or len(verdict["results"]) != 2
                    or not all(v["ok"] for v in verdict["results"])):
                raise ValueError("packaged success example disagrees with sample_verdict.json")
        elif not verdict["accepted"] or not all(v.get("code") == error for v in verdict["results"]):
            raise ValueError("packaged negative example did not return " + error)
    sh(sys.executable, "-m", "acms_verify", "--manifest",
       examples / "training_manifest.json", "--check-hashes",
       cwd=comp / "tools/verifier", env=env)
    print("OK: packaged success receipt, negative example, and training/scored separation")


def validate_problem_files(comp, manifest):
    """Keep the readable problem lists identical to the verifier's mathematical inputs."""
    for name, rows in render_problems(manifest).items():
        path = comp / "problems" / name
        if not path.is_file() or path.read_bytes() != serialize_problems(rows).encode("utf-8"):
            raise ValueError("problem list differs from manifest: " + name +
                             "; run python3 build/build_problems.py")


def export_package(out, preview=False):
    src = REPO / "competition"

    # 1. hash verification against the in-repo source of truth
    manifest = json.loads((src / "tools/verifier/data" / "manifest.json").read_text())
    problems = specs.check_move_specs(manifest.get("move_specs"))
    assert not problems, problems
    spec_hashes = specs.move_spec_hashes()
    # Every declared spec file on disk must carry the same table.
    for entry in manifest["move_specs"]:
        version = entry["move_spec_version"]
        on_disk = json.loads(
            (src / "tools/verifier/data" / entry["file"]).read_text())
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

    # Each presentation appears once per Discovery problem, with identical inputs.
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

    validate_problem_files(src, manifest)

    state = json.loads((REPO / "build/competition_state.json").read_text())
    yaml_text = render_yaml(manifest, state)
    validate_public_state(state, yaml_text, manifest)
    if not preview:
        validate_final_state(state)
    for entry in manifest["move_specs"]:
        assert "  - version: %s\n" % entry["move_spec_version"] in yaml_text
        assert '    hash: "%s"\n' % entry["move_spec_hash"] in yaml_text
        assert "    file: tools/verifier/data/%s\n" % entry["file"] in yaml_text
    validate_track_structure(yaml_text)
    validate_rule_documents(src)
    assert 'manifest_hash: "%s"' % manifest["manifest_hash"] in yaml_text
    assert "challenge_count: %d" % CHALLENGE_COUNT in yaml_text
    sh(sys.executable, REPO / "build/build_examples.py", "--check")

    # 2. source export (without local caches or Lean build products)
    out.mkdir(parents=True)
    copy_public_tree(src, out / "competition")
    (out / "competition/competition.yaml").write_text(yaml_text, encoding="utf-8")
    shutil.copy2(REPO / "LICENSE", out / "LICENSE")
    shutil.copy2(REPO / "NOTICE", out / "NOTICE")
    if preview:
        notice = ("**PREVIEW — not an official competition release.**\n\n"
                  "Competition status: `" + state["status"] + "`. "
                  "See `competition/competition.yaml` for the schedule and freeze metadata; "
                  "`null` means not yet announced or recorded.")
    else:
        notice = "Official data release. Competition status: `" + state["status"] + "`."
    (out / "README.md").write_text(ROOT_README.replace("RELEASE_NOTICE", notice))

    # 3. source lock, golden vectors, and hashes from the copied package only.
    # This verifies the published statement snapshot without copying or
    # downloading Lean dependencies; the Lean build/audit is run separately.
    comp = out / "competition"
    validate_problem_files(comp, manifest)
    env = {"PYTHONPATH": "", "PATH": "/usr/bin:/bin",
           "PYTHONDONTWRITEBYTECODE": "1"}
    verify_lean_statement(comp / "tools/lean")
    print("OK: packaged Lean sources and dependency lock match statement-lock.json")
    sh(sys.executable, "-m", "acms_verify",
       "--golden", comp / "tools/verifier/data" / "golden_vectors.json",
       cwd=comp / "tools" / "verifier", env=env)
    check_packaged_examples(comp, env)
    sh(sys.executable, "-m", "acms_verify",
       "--manifest", comp / "tools/verifier/data" / "manifest.json", "--check-hashes",
       cwd=comp / "tools" / "verifier", env=env)

    # 4. nothing from the internal directories may leak: the package
    # holds exactly {README.md, LICENSE, NOTICE, competition/}, no path
    # segment named server/build/spec/reference/tests/private, and no
    # server-module or builder basenames.
    top = sorted(q.name for q in out.iterdir())
    assert top == ["LICENSE", "NOTICE", "README.md", "competition"], top
    internal_files = {p.name for p in (REPO / "server").rglob("*.py")
                      if "__pycache__" not in p.parts}
    internal_files |= {p.name for p in (REPO / "build").rglob("*.py")
                       if "__pycache__" not in p.parts}
    for p in out.rglob("*"):
        parts = [q.lower() for q in p.relative_to(out).parts]
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
    exported = (comp / "tools/verifier/data" / "manifest.json").read_text(
        encoding="utf-8")
    for token in BANNED_TOKENS:
        assert token not in exported, "banned token %r in exported manifest" \
            % (token,)
    freeze = json.loads(exported)["freeze_date"]
    hit = re.search(r"[A-Z]", exported.replace(freeze, "") if freeze else exported)
    assert hit is None, "unexpected uppercase in exported manifest at %d" % (
        hit.start() if hit else -1)

    # 5b. the move specs and the training files carry published metadata
    # vocabulary but must still carry no private identifier.  The frozen
    # ac-r2-v1 pair is scanned first, so the rule is demonstrably the one
    # training_424.json already passes.
    for name in AUX_SCANNED:
        text = (comp / name).read_text(encoding="utf-8")
        for token in AUX_BANNED_TOKENS:
            assert token not in text, "banned token %r in %s" % (token, name)
    print("leak check: %s clean (%d tokens each)"
          % (", ".join(AUX_SCANNED), len(AUX_BANNED_TOKENS)))

    return sum(1 for p in out.rglob("*") if p.is_file())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path,
                        default=REPO / "dist/ACMS-public")
    parser.add_argument("--preview", action="store_true",
                        help="build a clearly marked preview without requiring a final freeze")
    args = parser.parse_args(argv)
    out = args.output.resolve()
    if out == REPO or out in REPO.parents or REPO / "competition" in (out, *out.parents):
        parser.error("output must not replace the repository or its public source tree")
    if REPO in out.parents and REPO / "dist" not in out.parents:
        parser.error("outputs inside the repository must be placed under dist/")
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".acms-export-", dir=out.parent) as tmp:
            stage = Path(tmp) / "package"
            file_count = export_package(stage, preview=args.preview)
            # Keep the previous package until installation succeeds, and
            # restore it if the final rename fails.
            previous = Path(tmp) / "previous"
            if out.exists():
                out.rename(previous)
            try:
                stage.rename(out)
            except BaseException:
                if previous.exists():
                    previous.rename(out)
                raise
    except (ValueError, AssertionError, OSError, subprocess.CalledProcessError) as exc:
        print("Release refused: " + str(exc), file=sys.stderr)
        return 1
    mode = "PREVIEW" if args.preview else "OFFICIAL"
    print(f"\nOK: {mode} ACMS-public exported to {out} ({file_count} files), "
          f"{CHALLENGE_COUNT} challenges; hashes, Lean source lock, golden vectors, "
          "and examples verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
