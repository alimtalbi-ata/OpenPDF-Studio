import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parent.parent
class BuildV401(unittest.TestCase):
 def test_inno_source_present(self):
  self.assertTrue((ROOT/'03-Sources/OpenPDF-Studio-V40.2.iss').is_file())
 def test_ci_provisions_python_and_inno(self):
  y=(ROOT/'.github/workflows/windows-release.yml').read_text()
  self.assertIn('actions/setup-python@v5',y)
  self.assertIn('choco install innosetup',y)
  self.assertIn('if: always()',y)
 def test_build_stages_before_publish(self):
  b=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertLess(b.index('openpdf_release_gate.py "%STAGE%"'),b.index('openpdf_publish_binary.py'))
  self.assertIn('if defined CI goto missing_inno',b)
 def test_versioned_artifact_names(self):
  y=(ROOT/'.github/workflows/windows-release.yml').read_text()
  self.assertIn('OpenPDF-Studio-V40.2-Setup.exe',y)
  self.assertIn('OpenPDF-Studio-Portable-V40.2.exe',y)
if __name__=='__main__':unittest.main()
