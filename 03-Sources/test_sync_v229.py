import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class SyncV229(unittest.TestCase):
 def test_filter_predicate(self):
  html=build_dashboard({});self.assertIn('matchChart',html);self.assertIn('openpdf:findings-filtered',html)
 def test_export_and_version(self):
  html=build_dashboard({});self.assertIn('Diagnostic V25.4',html);self.assertIn('openpdf-diagnostic-v25.4.csv',html)
 def test_charts_synced(self):
  script=Path(__file__).with_name('qualification_charts.js').read_text();self.assertIn('!rows[i].hidden',script);self.assertIn('requestFilter',script)
if __name__=='__main__':unittest.main()
