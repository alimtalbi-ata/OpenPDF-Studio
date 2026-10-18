import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class Regions218(unittest.TestCase):
 def test_script_exists(self):
  self.assertIn('is-selected',Path(__file__).with_name('region_overlay.js').read_text())
 def test_selection_keyboard(self):
  self.assertIn("e.key==='Enter'||e.key===' '",Path(__file__).with_name('region_overlay.js').read_text())
 def test_selection_cleared(self):
  self.assertIn("clear.addEventListener('click',deselect)",Path(__file__).with_name('region_overlay.js').read_text())
 def test_dashboard_controls(self):
  html=build_dashboard({})
  self.assertIn('region-selection-status',html)
  self.assertIn('region-selection-clear',html)
 def test_dashboard_version(self):
  self.assertIn('Diagnostic V25.4',build_dashboard({}))
if __name__=='__main__':unittest.main()
