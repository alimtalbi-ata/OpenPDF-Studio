import unittest
from pathlib import Path
from openpdf_release_gate import VERSION
ROOT=Path(__file__).resolve().parent.parent
class TestBuild(unittest.TestCase):
 def test_staging(self):
  s=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertIn(f'.staging-v{VERSION}',s)
  self.assertIn('openpdf_publish_binary.py',s)
 def test_inno_stage(self):
  s=(ROOT/f'03-Sources/OpenPDF-Studio-V{VERSION}.iss').read_text()
  self.assertIn(f'OutputDir=..\\01-Application\\binary\\.staging-v{VERSION}',s)
 def test_no_early_delete(self):
  s=(ROOT/'02-Compilation/BUILD-WINDOWS-INSTALLER.cmd').read_text()
  self.assertNotIn('del /q "%BINARY%',s)
if __name__=="__main__":unittest.main()
