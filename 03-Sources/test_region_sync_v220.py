import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
ROOT=Path(__file__).parent
class RegionSyncV220(unittest.TestCase):
 def test_script_exists(self):
  self.assertIn('openpdf:correlation-page',(ROOT/'region_sync.js').read_text())
 def test_region_emits_event(self):
  self.assertIn('openpdf:region-selected',(ROOT/'region_overlay.js').read_text())
 def test_navigation_emits_event(self):
  self.assertIn('openpdf:correlation-page',(ROOT/'correlation_navigation.js').read_text())
 def test_html_embeds_script(self):
  html=build_dashboard({});self.assertIn('Corrélation au niveau page',html)
 def test_page_context_exists(self):
  self.assertIn('id="region-page-context"',build_dashboard({}))
 def test_version(self):
  self.assertIn('Diagnostic V25.4',build_dashboard({}))
 def test_export_name(self):
  self.assertIn('openpdf-diagnostic-v25.4.csv',build_dashboard({}))
if __name__=='__main__':unittest.main()
