import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class TestBuild(unittest.TestCase):
 def test_staging(self):
  s=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertIn('.staging-v39.8',s)
  self.assertIn('openpdf_publish_binary.py',s)
 def test_inno_stage(self):
  s=(ROOT/'03-Sources/OpenPDF-Studio-V39.8.iss').read_text()
  self.assertIn('OutputDir=..\\01-Application\\binary\\.staging-v39.8',s)
 def test_no_early_delete(self):
  s=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertNotIn('del /q "%BINARY%',s)
if __name__=="__main__":unittest.main()
