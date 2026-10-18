import unittest
from pathlib import Path
from unittest.mock import patch
import openpdf_qualification_v383
class V383(unittest.TestCase):
 def test_real_operations(self):
  from openpdf_functional_qualification import run_suite
  r=run_suite();self.assertEqual(r['passed'],r['total'],r)
  self.assertGreaterEqual(r['total'],5)
 def test_preview_debounce(self):
  s=(Path(__file__).parent/'openpdf_desktop.py').read_text()
  self.assertIn('after_cancel(self._preview_after_id)',s)
  self.assertIn('_dispatch_preview',s)
 def test_preview_result_cleans_pending(self):
  s=(Path(__file__).parent/'openpdf_desktop.py').read_text()
  self.assertIn('self._preview_pending.discard(event[3])',s)
 def test_version(self):
  s=(Path(__file__).parent/'openpdf_desktop.py').read_text()
  self.assertRegex(s,r'OpenPDF Studio V38\.\d+')
if __name__=='__main__':unittest.main()
