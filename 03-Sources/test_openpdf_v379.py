import unittest, pathlib, ast
ROOT=pathlib.Path(__file__).resolve().parent
class ReleaseTests(unittest.TestCase):
 def test_ui_syntax(self): ast.parse((ROOT/'openpdf_desktop.py').read_text())
 def test_version(self): self.assertIn('V37.9',(ROOT/'openpdf_desktop.py').read_text())
 def test_destination_reset(self): self.assertIn("self.destination.set('')",(ROOT/'openpdf_desktop.py').read_text())
 def test_cache_eviction(self): self.assertIn('self._preview_cache.pop(next(iter', (ROOT/'openpdf_desktop.py').read_text())
 def test_build(self): self.assertIn('OpenPDF-Studio-V37.9.iss',(ROOT.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text())
 def test_preflight(self):
  from openpdf_build_preflight import inspect_release
  self.assertTrue(inspect_release(ROOT.parent)['passed'])
if __name__=='__main__':unittest.main()
