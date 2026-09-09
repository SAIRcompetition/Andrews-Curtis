"""Release readiness must be checked before an existing package is replaced."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests import util


module_spec = importlib.util.spec_from_file_location(
    "acc_release", util.REPO / "build/release.py")
release = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(release)


def copy_release_fixture(root):
    """Copy only the inputs needed for an export, with no local generated YAML."""
    (root / "build").mkdir(parents=True)
    for name in ("release.py", "build_manifest_v2.py", "build_manifest.py",
                 "sync_dataset.py", "build_examples.py", "build_problems.py", "competition_state.json"):
        shutil.copy2(util.REPO / "build" / name, root / "build" / name)
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(util.REPO / name, root / name)
    release.copy_public_tree(util.REPO / "competition", root / "competition")


class TestReleaseState(unittest.TestCase):
    def test_maintained_state_matches_public_metadata(self):
        state = util.load(util.REPO / "build/competition_state.json")
        manifest = util.load_manifest()
        release.validate_public_state(
            state, release.render_yaml(manifest, state), manifest)

    def test_two_tracks_route_both_problems_to_their_own_definitions(self):
        yaml_text = release.render_yaml(
            util.load_manifest(), util.load(util.REPO / "build/competition_state.json"))
        release.validate_track_structure(yaml_text)
        mutations = (
            yaml_text.replace("  - id: proof\n", "  - id: prove_ac\n"),
            yaml_text.replace("      - id: stable_ac\n", "      - id: ac\n", 1),
            yaml_text.replace("conjecture: AC.StableConjecture", "conjecture: AC.Conjecture"),
            yaml_text.replace("move_spec_version: sac-r8-v1", "move_spec_version: ac-r2-v1"),
            yaml_text.replace("leaderboards: independent_per_problem", "leaderboards: combined"),
            yaml_text.replace("file: problems/stable_ac.json", "file: problems/ac.json"),
            yaml_text.replace("    overview: rules/discovery.md", "    overview: rules/proof.md"),
            yaml_text.replace("    statement: rules/proof.md", "    statement: rules/overview.md"),
            yaml_text.replace("    opens_at:", "    unused_opens_at:", 1),
        )
        for mutation in mutations:
            with self.subTest(metadata=mutation), self.assertRaises(ValueError):
                release.validate_track_structure(mutation)

    def test_public_overview_and_track_guides_are_complete_and_consistent(self):
        release.validate_rule_documents(util.REPO / "competition")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "rules"
            rules.mkdir()
            for name in ("overview.md", "prelaunch.md", "discovery.md", "proof.md"):
                (rules / name).write_text("Shared overview\n")
            release.validate_rule_documents(root)
            (rules / "prelaunch.md").write_text("Stale overview\n")
            with self.assertRaisesRegex(ValueError, "same overview"):
                release.validate_rule_documents(root)
            (rules / "prelaunch.md").write_text("Shared overview\n")
            for name in ("discovery.md", "proof.md"):
                (rules / name).unlink()
                with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "missing competition guide"):
                    release.validate_rule_documents(root)
                (rules / name).write_text("Track guide\n")

    def test_missing_or_stale_problem_descriptions_are_rejected(self):
        manifest = util.load_manifest()
        release.validate_problem_files(util.REPO / "competition", manifest)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "problems").mkdir()
            for name in ("ac.json", "stable_ac.json"):
                shutil.copy2(util.PROBLEMS / name, root / "problems" / name)
            for name in ("ac.json", "stable_ac.json"):
                path = root / "problems" / name
                original = path.read_bytes()
                rows = json.loads(original)
                rows[0]["description"] = "Wrong presentation or target"
                path.write_text(json.dumps(rows))
                with self.subTest(stale=name), self.assertRaisesRegex(ValueError, "differs from manifest"):
                    release.validate_problem_files(root, manifest)
                path.unlink()
                with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "differs from manifest"):
                    release.validate_problem_files(root, manifest)
                path.write_bytes(original)

    def test_metadata_drift_is_rejected(self):
        state = dict.fromkeys(release.STATE_FIELDS)
        state["status"] = "prelaunch"
        yaml_text = "\n".join(k + ": " + json.dumps(v) for k, v in state.items())
        manifest = {"freeze_date": None, "challenges": [{"freeze_date": None}]}
        release.validate_public_state(state, yaml_text, manifest)
        with self.assertRaisesRegex(ValueError, "disagrees"):
            release.validate_public_state(state, yaml_text.replace('"prelaunch"', '"active"'),
                                          manifest)
        manifest["challenges"][0]["freeze_date"] = "2026-09-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "freeze dates disagree"):
            release.validate_public_state(state, yaml_text, manifest)

    def test_prelaunch_official_export_leaves_existing_package_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Use an explicit prelaunch fixture so this check remains valid
            # when the real competition later opens.
            fixture = Path(tmp) / "repo"
            copy_release_fixture(fixture)
            state = util.load(util.REPO / "build/competition_state.json")
            state["status"] = "prelaunch"
            (fixture / "build/competition_state.json").write_text(json.dumps(state))
            out = Path(tmp) / "package"
            out.mkdir()
            (out / "sentinel").write_text("previous package")
            result = subprocess.run(
                [sys.executable, str(fixture / "build/release.py"), str(out)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("use --preview", result.stderr)
            self.assertEqual((out / "sentinel").read_text(), "previous package")
            self.assertEqual([p.name for p in out.iterdir()], ["sentinel"])


class TestPublicSourceExport(unittest.TestCase):
    def test_preview_generates_metadata_without_trusting_a_local_yaml_file(self):
        for cached in (None, "stale: local metadata must not be exported\n"):
            with self.subTest(cached_yaml=cached), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "repo"
                copy_release_fixture(root)
                local_yaml = root / "competition/competition.yaml"
                self.assertFalse(local_yaml.exists())
                if cached is not None:
                    local_yaml.write_text(cached)
                out = Path(tmp) / "package"
                result = subprocess.run(
                    [sys.executable, str(root / "build/release.py"), "--preview", str(out)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                state = util.load(root / "build/competition_state.json")
                manifest = util.load(root / "competition/tools/verifier/data/manifest.json")
                self.assertFalse((out / "competition/challenges").exists())
                for name in ("ac.json", "stable_ac.json"):
                    self.assertEqual((out / "competition/problems" / name).read_bytes(),
                                     (root / "competition/problems" / name).read_bytes())
                exported = (out / "competition/competition.yaml").read_text()
                self.assertEqual(exported, release.render_yaml(manifest, state))
                release.validate_public_state(state, exported, manifest)
                release.validate_track_structure(exported)
                if cached is None:
                    self.assertFalse(local_yaml.exists())
                else:
                    self.assertEqual(local_yaml.read_text(), cached)

    def test_lean_sources_and_pins_ship_without_dependencies_or_build_products(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            destination = Path(tmp) / "package"
            lean = source / "tools/lean"
            public_files = {
                "AC.lean": "namespace AC\nend AC\n",
                "Check.lean": "import AC\n",
                "lakefile.toml": 'name = "ac_statement"\n',
                "lean-toolchain": "leanprover/lean4:v4.29.1\n",
                "lake-manifest.json": '{"packages": []}\n',
                "statement-lock.json": '{"schema_version": 1}\n',
                "README.md": "Build the official statement.\n",
            }
            local_files = (
                ".lake/packages/mathlib/Mathlib.lean",
                ".lake/packages/mathlib/.git/config",
                ".lake/build/lib/lean/AC.olean",
                "AC.olean", "AC.ilean",
                "AC.olean.private", "AC.olean.server",
                "__pycache__/local.cpython-313.pyc", ".DS_Store",
            )
            for relative, content in public_files.items():
                path = lean / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            for relative in local_files:
                path = lean / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("local artifact")

            release.copy_public_tree(source, destination)

            exported = destination / "tools/lean"
            self.assertEqual(
                {p.relative_to(exported).as_posix() for p in exported.rglob("*")
                 if p.is_file()},
                set(public_files),
            )
            for relative, content in public_files.items():
                self.assertEqual((exported / relative).read_text(), content)
            self.assertFalse((exported / ".lake").exists())


class TestFinalFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.repo = Path(cls.tmp.name)
        data = cls.repo / "competition/tools/verifier/data"
        data.mkdir(parents=True)
        for name in ("manifest.json", "move_spec.json", "stable_move_spec.json"):
            (data / name).write_text('{"frozen":true}\n')
        cls.git("init", "-q")
        cls.git("add", "competition")
        cls.git("-c", "user.name=Release Test", "-c", "user.email=release@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "Freeze test data")
        cls.state = {
            "status": "active", "freeze_commit": cls.git("rev-parse", "HEAD").strip(),
            "freeze_date": "2026-10-01T00:00:00Z",
            "registration_opens": "2026-10-02T00:00:00Z",
            "submissions_open": "2026-10-03T00:00:00Z",
            "prove_submissions_open": "2026-10-03T12:00:00Z",
            "submission_deadline": "2026-10-04T00:00:00Z",
        }

    @classmethod
    def git(cls, *args):
        return subprocess.run(["git", *args], cwd=cls.repo, check=True,
                              capture_output=True, text=True).stdout

    def test_complete_state_with_matching_git_snapshot_passes(self):
        release.validate_final_state(self.state, self.repo)

    def test_discovery_release_can_precede_the_exact_proof_opening_time(self):
        release.validate_final_state(
            dict(self.state, prove_submissions_open=None), self.repo)

    def test_finished_release_requires_the_proof_opening_time(self):
        release.validate_final_state(dict(self.state, status="finished"), self.repo)
        with self.assertRaisesRegex(ValueError, "prove_submissions_open"):
            release.validate_final_state(
                dict(self.state, status="finished", prove_submissions_open=None), self.repo)

    def test_announced_proof_time_must_be_a_valid_utc_timestamp(self):
        for invalid in ("TBD", "2026-10-03", "2026-10-03T12:00:00", "2026-13-03T12:00:00Z"):
            with self.subTest(proof_opening=invalid), self.assertRaises(ValueError):
                release.validate_final_state(
                    dict(self.state, prove_submissions_open=invalid), self.repo)

    def test_each_required_date_and_commit_is_enforced(self):
        for key in (*release.DATE_FIELDS, "freeze_commit"):
            for value in (None, "TBD"):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    release.validate_final_state(dict(self.state, **{key: value}), self.repo)

    def test_schedule_order_and_timezone_are_enforced(self):
        for change in (
            {"submissions_open": "2026-10-02T00:00:00"},
            {"submission_deadline": "2026-10-02T00:00:00Z"},
            {"freeze_date": "2026-10-04T00:00:00Z"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                release.validate_final_state(dict(self.state, **change), self.repo)

    def test_missing_commit_and_changed_frozen_files_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "not an available Git commit"):
            release.validate_final_state(dict(self.state, freeze_commit="f" * 40), self.repo)
        for name in ("manifest.json", "move_spec.json", "stable_move_spec.json"):
            path = self.repo / "competition/tools/verifier/data" / name
            original = path.read_bytes()
            try:
                path.write_text('{"frozen":false}\n')
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "does not match"):
                    release.validate_final_state(self.state, self.repo)
            finally:
                path.write_bytes(original)
    def test_prove_opening_must_follow_discovery_and_precede_deadline(self):
        for invalid in ("2026-10-02T12:00:00Z", self.state["submission_deadline"]):
            with self.subTest(prove_opening=invalid), self.assertRaisesRegex(
                    ValueError, "competition dates must follow"):
                release.validate_final_state(
                    dict(self.state, prove_submissions_open=invalid), self.repo)



if __name__ == "__main__":
    unittest.main()
