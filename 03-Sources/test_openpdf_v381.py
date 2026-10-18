import unittest
from pathlib import Path
from openpdf_build_preflight import inspect_release

class PackagingTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(__file__).resolve().parent.parent
 def test_preflight(self):
  r=inspect_release(self.root);self.assertTrue(r['passed'],r)
 def test_powershell_modes(self):
  p=(self.root/'02-Compilation'/'TEST-WINDOWS-BINARIES.ps1').read_text(encoding='utf-8');self.assertIn("ValidateSet('installer','portable')",p)
 def test_smoke_checks_marker(self):
  p=(self.root/'02-Compilation'/'TEST-WINDOWS-BINARIES.ps1').read_text(encoding='utf-8');self.assertIn('OPENPDF_SELF_TEST_OK',p)
 def test_build_fail_closed(self):
  p=(self.root/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8');self.assertIn('|| goto fail',p);self.assertIn('windows-smoke-portable.json',p)
 def test_inno_version(self):
  p=(self.root/'03-Sources'/'OpenPDF-Studio-V38.1.iss').read_text(encoding='utf-8');self.assertIn('#define AppVersion "38.1"',p)
if __name__=='__main__':unittest.main()
