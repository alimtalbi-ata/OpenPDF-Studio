import unittest,tempfile
from pathlib import Path
from verify_release_v341 import check_source,check_exe,check_portable,check_installer
class TestRelease(unittest.TestCase):
 def test_sources(self):self.assertTrue(check_source())
 def test_missing_exe_rejected(self):
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(AssertionError):check_exe(Path(p))
 def test_missing_portable_rejected(self):
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(AssertionError):check_portable(Path(p))
 def test_missing_installer_rejected(self):
  with tempfile.TemporaryDirectory() as p:
   with self.assertRaises(AssertionError):check_installer(Path(p))
if __name__=='__main__':unittest.main()
