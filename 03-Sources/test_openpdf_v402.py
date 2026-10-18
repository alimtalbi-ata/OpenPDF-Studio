import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
class WindowsBuildContract(unittest.TestCase):
 def test_inno_config_exists(self):
  script=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
  self.assertIn('OpenPDF-Studio-V40.2.iss',script)
  self.assertTrue((ROOT/'03-Sources/OpenPDF-Studio-V40.2.iss').exists())
 def test_installer_stage_path(self):
  config=(ROOT/'03-Sources/OpenPDF-Studio-V40.2.iss').read_text(encoding='utf-8')
  self.assertIn('binary\\.staging-v40.2',config)
  self.assertIn('OpenPDF-Studio-V40.2-Setup',config)
 def test_windows_runner_contract(self):
  flow=(ROOT/'.github/workflows/windows-release.yml').read_text(encoding='utf-8')
  self.assertIn('windows-2022',flow)
  self.assertIn('OpenPDF-Studio-V40.2-Setup.exe',flow)
  self.assertIn('OpenPDF-Studio-Portable-V40.2.exe',flow)
 def test_install_test_no_stale_temp_prefix(self):
  script=(ROOT/'02-Compilation/TEST-WINDOWS-INSTALLATION.ps1').read_text(encoding='utf-8')
  self.assertNotIn('OpenPDF-V398-',script)
  self.assertIn('OpenPDF-V402-',script)
 def test_build_validates_before_publish(self):
  s=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text(encoding='utf-8')
  self.assertLess(s.index('openpdf_release_gate.py "%STAGE%"'),s.index('openpdf_publish_binary.py'))
if __name__=='__main__':unittest.main()
