"""V28.1 build consistency tests. Author: Abdelhalim Talbi."""
import unittest
from pathlib import Path
from openpdf_build_audit_v281 import audit

class TestBuildAudit(unittest.TestCase):
    def test_all_build_contracts(self):
        checks=audit(Path(__file__).resolve().parent)
        self.assertTrue(all(checks.values()),checks)
    def test_entrypoint_exists(self):
        self.assertTrue((Path(__file__).parent/'openpdf_windows_v281.py').is_file())
    def test_no_legacy_entrypoint_in_exe_wrapper(self):
        self.assertNotIn('v267.py',(Path(__file__).parent/'BUILD-WINDOWS-EXE.cmd').read_text())

if __name__=='__main__': unittest.main()
