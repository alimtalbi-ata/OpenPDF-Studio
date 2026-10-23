"""Regression tests for source closure; no Windows execution is claimed."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "03-Sources"
spec = importlib.util.spec_from_file_location("source_closure", SRC / "openpdf_source_closure_v502.py")
closure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure)


class SourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = self.root / "03-Sources"
        self.sources.mkdir()
        (self.root / "VERSION.txt").write_text("50.2\n", encoding="utf-8")

    def put(self, name, content):
        (self.sources / (name + ".py")).write_text(content, encoding="utf-8")

    def check(self):
        return closure.audit_sources(self.root, ["openpdf_studio"])

    def test_simple_import_closure(self):
        self.put("openpdf_studio", "from openpdf_pages import run\n")
        self.put("openpdf_pages", "def run(): return 1\n")
        r = self.check()
        self.assertTrue(r["passed"])
        self.assertEqual(r["scanned_modules"], ["openpdf_pages", "openpdf_studio"])

    def test_missing_direct_dependency_is_failure(self):
        self.put("openpdf_studio", "import openpdf_missing\n")
        self.assertEqual(self.check()["missing_modules"], ["openpdf_missing"])
        self.assertFalse(self.check()["passed"])

    def test_missing_nested_dependency_is_failure(self):
        self.put("openpdf_studio", "import openpdf_first\n")
        self.put("openpdf_first", "from openpdf_missing import go\n")
        self.assertEqual(self.check()["missing_modules"], ["openpdf_missing"])

    def test_missing_entrypoint_is_failure(self):
        self.assertEqual(self.check()["missing_modules"], ["openpdf_studio"])

    def test_syntax_error_is_failure(self):
        self.put("openpdf_studio", "def invalid(: pass\n")
        r = self.check()
        self.assertFalse(r["passed"])
        self.assertIn("openpdf_studio", r["syntax_errors"])

    def test_external_packages_not_falsely_flagged(self):
        self.put("openpdf_studio", "import fitz\nfrom PIL import Image\nimport pathlib\n")
        self.assertTrue(self.check()["passed"])

    def test_literal_importlib_detected(self):
        self.put("openpdf_studio", 'import importlib\nimportlib.import_module("openpdf_extra")\n')
        self.assertEqual(self.check()["missing_modules"], ["openpdf_extra"])

    def test_literal_builtin_import_detected(self):
        self.put("openpdf_studio", '__import__("openpdf_extra")\n')
        self.assertEqual(self.check()["missing_modules"], ["openpdf_extra"])

    def test_cycles_terminate(self):
        self.put("openpdf_studio", "import openpdf_other\n")
        self.put("openpdf_other", "import openpdf_studio\n")
        self.assertEqual(len(self.check()["scanned_modules"]), 2)

    def test_import_inside_function_is_required(self):
        self.put("openpdf_studio", "def run():\n    import openpdf_later\n")
        self.assertEqual(self.check()["missing_modules"], ["openpdf_later"])

    def test_invalid_entrypoint_rejected(self):
        with self.assertRaises(ValueError):
            closure.audit_sources(self.root, ["../escape"])

    def test_empty_entrypoint_rejected(self):
        with self.assertRaises(ValueError):
            closure.audit_sources(self.root, [])

    def test_deterministic_report(self):
        self.put("openpdf_studio", "import openpdf_b, openpdf_a\n")
        self.put("openpdf_a", "")
        self.put("openpdf_b", "")
        self.assertEqual(json.dumps(self.check(), sort_keys=True), json.dumps(self.check(), sort_keys=True))

    def test_sources_are_not_executed(self):
        marker = self.root / "must-not-run"
        self.put("openpdf_studio", f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n")
        self.assertTrue(self.check()["passed"])
        self.assertFalse(marker.exists())

    def test_windows_build_invokes_fail_closed_gate(self):
        script = (SRC.parent / "02-Compilation" / "BUILD-WINDOWS-INSTALLER.cmd").read_text(encoding="utf-8")
        self.assertIn('openpdf_source_closure_v502.py --root "%ROOT%"', script)
        self.assertIn('|| goto fail', script.split('openpdf_source_closure_v502.py', 1)[1].splitlines()[0])
        self.assertIn('failed-source-closure-v%VERSION%.json', script)
        self.assertIn('source-closure-v%VERSION%.json', script)

    def test_cli_failure_writes_report(self):
        self.put("openpdf_studio", "import openpdf_missing\n")
        report = self.root / "report.json"
        p = subprocess.run([sys.executable, str(SRC / "openpdf_source_closure_v502.py"),
                            "--root", str(self.root), "--report", str(report)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertFalse(json.loads(report.read_text(encoding="utf-8"))["passed"])

    def test_cli_success_writes_report(self):
        self.put("openpdf_studio", "print('never executed')\n")
        report = self.root / "report.json"
        p = subprocess.run([sys.executable, str(SRC / "openpdf_source_closure_v502.py"),
                            "--root", str(self.root), "--report", str(report)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(json.loads(report.read_text(encoding="utf-8"))["passed"])

    @unittest.skipUnless(hasattr(Path, 'symlink_to'), 'symlinks unavailable')
    def test_symlinked_module_is_not_followed(self):
        self.put("openpdf_studio", "import openpdf_other\n")
        outside = self.root / "outside.py"
        outside.write_text("", encoding="utf-8")
        try:
            (self.sources / "openpdf_other.py").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        self.assertEqual(self.check()["missing_modules"], ["openpdf_other"])


if __name__ == "__main__":
    unittest.main()
