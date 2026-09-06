"""The published Lean target must match its reviewed sources and dependency pins."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from tests import util


module_spec = importlib.util.spec_from_file_location(
    "acc_formalization_release", util.REPO / "build/release.py")
release = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(release)

LEAN = util.REPO / "competition/tools/lean"


class TestFormalizationLock(unittest.TestCase):
    def copy_project(self, root):
        copied = root / "lean"
        release.copy_public_tree(LEAN, copied)
        self.assertFalse((copied / ".lake").exists())
        return copied

    def test_published_source_matches_lock_without_lean_installed(self):
        release.verify_lean_statement(LEAN)

    def test_exported_project_matches_lock_without_local_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = self.copy_project(Path(tmp))
            release.verify_lean_statement(copied)

    def test_statement_or_dependency_pin_drift_is_rejected(self):
        for relative in ("AC.lean", "lake-manifest.json"):
            with self.subTest(file=relative), tempfile.TemporaryDirectory() as tmp:
                copied = self.copy_project(Path(tmp))
                path = copied / relative
                # Even a syntactically harmless edit changes the reviewed
                # snapshot and requires an explicit lock update after audit.
                path.write_bytes(path.read_bytes() + b"\n")
                with self.assertRaisesRegex(ValueError, "statement lock mismatch"):
                    release.verify_lean_statement(copied)

    def test_independent_contestant_file_does_not_change_official_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = self.copy_project(Path(tmp))
            (copied / "Submission.lean").write_text("import AC\n#check AC.Conjecture\n")
            release.verify_lean_statement(copied)

    def test_optional_checks_are_not_part_of_the_official_statement_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = self.copy_project(Path(tmp))
            (copied / "Check.lean").unlink()
            release.verify_lean_statement(copied)

    def test_missing_statement_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = self.copy_project(Path(tmp))
            (copied / "statement-lock.json").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "statement-lock.json"):
                release.verify_lean_statement(copied)


if __name__ == "__main__":
    unittest.main()
