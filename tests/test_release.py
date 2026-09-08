"""Release readiness must be checked before an existing package is replaced."""

import importlib.util
import json
from pathlib import Path
import re
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


class TestReleaseState(unittest.TestCase):
    def test_maintained_state_matches_public_metadata(self):
        state = util.load(util.REPO / "build/competition_state.json")
        release.validate_public_state(
            state, (util.REPO / "competition/competition.yaml").read_text(),
            util.load_manifest())

    def test_two_tracks_route_both_problems_to_their_own_definitions(self):
        yaml_text = (util.REPO / "competition/competition.yaml").read_text()
        release.validate_track_structure(yaml_text)
        mutations = (
            yaml_text.replace("  - id: proof\n", "  - id: prove_ac\n"),
            yaml_text.replace("      - id: stable_ac\n", "      - id: ac\n", 1),
            yaml_text.replace("conjecture: AC.StableConjecture", "conjecture: AC.Conjecture"),
            yaml_text.replace("move_spec_version: sac-r8-v1", "move_spec_version: ac-r2-v1"),
            yaml_text.replace("leaderboards: independent_per_problem", "leaderboards: combined"),
        )
        for mutation in mutations:
            with self.subTest(metadata=mutation), self.assertRaises(ValueError):
                release.validate_track_structure(mutation)

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
            (fixture / "build").mkdir(parents=True)
            shutil.copy2(util.REPO / "build/release.py", fixture / "build/release.py")
            release.copy_public_tree(util.REPO / "competition", fixture / "competition")
            state = util.load(util.REPO / "build/competition_state.json")
            state["status"] = "prelaunch"
            (fixture / "build/competition_state.json").write_text(json.dumps(state))
            yaml_path = fixture / "competition/competition.yaml"
            yaml_path.write_text(re.sub(r"^status:.*$", "status: prelaunch",
                                        yaml_path.read_text(), flags=re.MULTILINE))
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
        data = cls.repo / "competition/challenges"
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
            "certificate_release": "2026-10-05T00:00:00Z",
        }

    @classmethod
    def git(cls, *args):
        return subprocess.run(["git", *args], cwd=cls.repo, check=True,
                              capture_output=True, text=True).stdout

    def test_complete_state_with_matching_git_snapshot_passes(self):
        release.validate_final_state(self.state, self.repo)

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
            path = self.repo / "competition/challenges" / name
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
