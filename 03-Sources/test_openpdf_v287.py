"""V28.7 release regression and packaging checks. Author: Abdelhalim Talbi."""
import unittest
from pathlib import Path
from verify_release_v287 import check_source
ROOT=Path(__file__).resolve().parent
class Release287Tests(unittest.TestCase):
 def test_current_source(self): self.assertTrue(check_source(ROOT))
 def test_exe_only_delegates(self):
  s=(ROOT/'BUILD-WINDOWS-EXE.cmd').read_text()
  self.assertIn('--exe-only',s)
 def test_build_fails_closed(self):
  s=(ROOT/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertIn('goto fail',s)
  self.assertIn('if not exist "dist\\OpenPDF-Studio\\OpenPDF-Studio.exe" goto fail',s)
 def test_inno_installs_all_dependencies(self):
  s=(ROOT/'OpenPDF-Studio-V28.7.iss').read_text()
  self.assertIn('recursesubdirs createallsubdirs',s)
  self.assertIn('UninstallDisplayIcon',s)
 def test_qualifier_runs_current_smoke(self):
  s=(ROOT/'QUALIFY-WINDOWS-V28.7.cmd').read_text()
  self.assertIn('smoke_windows_v287.py --launch',s)
if __name__=='__main__':unittest.main()
