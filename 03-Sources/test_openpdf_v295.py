import unittest, tempfile
from pathlib import Path
import ui_audit_v295 as audit
from verify_release_v295 import check_source,check_portable
class TestV295(unittest.TestCase):
 def test_source(self):self.assertTrue(check_source())
 def test_portable_missing(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(AssertionError):check_portable(Path(d))
 def test_audit_exports(self):self.assertTrue(callable(audit.inventory))
 def test_portable_qualification_exists(self):
  self.assertTrue((Path(__file__).parent/'qualify_portable_v295.py').exists())
 def test_entrypoint_no_new_subclass(self):
  s=(Path(__file__).parent/'openpdf_windows_v297.py').read_text()
  self.assertNotIn('class OpenPDFStudio(',s)
if __name__=='__main__':unittest.main()
