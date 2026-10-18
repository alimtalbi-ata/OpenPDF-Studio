import unittest
from openpdf_quality_report_v329 import quality_dashboard
class TestReport(unittest.TestCase):
 def test_measured(self):
  s=quality_dashboard({'gain_pct':22.57,'difference_moyenne_pct':1.2,'pages_analysees':5,'avertissements':['vérifier petits caractères']})
  self.assertIn('22.57 %',s);self.assertIn('1.20 %',s);self.assertIn('vérifier petits caractères',s)
 def test_missing(self):
  s=quality_dashboard({});self.assertIn('non mesuré',s);self.assertIn('validation humaine',s)
 def test_bad(self):
  with self.assertRaises(TypeError):quality_dashboard(None)
if __name__=='__main__':unittest.main()
