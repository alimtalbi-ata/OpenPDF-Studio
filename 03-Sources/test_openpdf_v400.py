import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV400(unittest.TestCase):
 def test_smoke_portable_stage_derived_from_report(self):
  s=(ROOT/'02-Compilation/TEST-WINDOWS-BINARIES.ps1').read_text()
  self.assertIn('Split-Path -Parent $ReportPath',s)
  self.assertIn('OpenPDF-Studio-Portable-V40.0.exe',s)
  self.assertNotIn('.staging-v39.8',s)
 def test_smoke_report_version(self):
  self.assertIn("version='40.0'",(ROOT/'02-Compilation/TEST-WINDOWS-BINARIES.ps1').read_text())
 def test_inno_exists(self):
  self.assertTrue((ROOT/'03-Sources/OpenPDF-Studio-V40.0.iss').is_file())
 def test_build_references_current_iss(self):
  self.assertIn('OpenPDF-Studio-V40.0.iss',(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text())
 def test_workflow_release_name(self):
  self.assertIn('OpenPDF-Studio-V40.0-Windows-binary',(ROOT/'.github/workflows/windows-release.yml').read_text())
if __name__=='__main__': unittest.main()
