import unittest
from pathlib import Path
from openpdf_build_preflight import inspect_release

class TestPackaging(unittest.TestCase):
    def test_release(self):
        report=inspect_release(Path(__file__).resolve().parent.parent)
        self.assertTrue(report["passed"],report["checks"])
    def test_mode_switches(self):
        cmd=(Path(__file__).resolve().parent.parent/"02-Compilation"/"BUILD-WINDOWS-INSTALLER.cmd").read_text()
        for arg in ("--portable-only","--installer-only"):
            self.assertIn(arg,cmd)
    def test_build_fails_closed(self):
        cmd=(Path(__file__).resolve().parent.parent/"02-Compilation"/"BUILD-WINDOWS-INSTALLER.cmd").read_text()
        self.assertIn('goto fail',cmd)
        self.assertIn('exit /b 1',cmd)
    def test_ui_version(self):
        text=(Path(__file__).resolve().parent/"openpdf_desktop.py").read_text()
        self.assertIn('V37.9',text)
        self.assertNotIn('OpenPDF Studio V37.0',text)

if __name__=="__main__":unittest.main()
