import unittest
from pathlib import Path
from openpdf_release_gate import VERSION
ROOT=Path(__file__).resolve().parent.parent
class TestWindowsInstallationWiring(unittest.TestCase):
 def test_integration_script_present(self):
  self.assertTrue((ROOT/'02-Compilation'/'TEST-WINDOWS-INSTALLATION.ps1').is_file())
 def test_installer_checked_before_publish(self):
  s=(ROOT/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertLess(s.index('TEST-WINDOWS-INSTALLATION.ps1'),s.index(':publish'))
 def test_silent_install_uninstall(self):
  s=(ROOT/'02-Compilation'/'TEST-WINDOWS-INSTALLATION.ps1').read_text()
  for token in ('/VERYSILENT','unins000.exe','OPENPDF_SELF_TEST_OK','WaitForExit','silent_install_pass'):self.assertIn(token,s)
 def test_version(self):
  self.assertEqual((ROOT/'VERSION.txt').read_text().strip(),VERSION)
if __name__=='__main__':unittest.main()
