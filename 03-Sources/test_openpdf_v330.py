import unittest,tempfile
from pathlib import Path
from openpdf_quality_dashboard_v330 import build_summary,format_summary
class QualityDashboardTests(unittest.TestCase):
 def test_reduction(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'a',Path(d)/'b';a.write_bytes(b'a'*100);b.write_bytes(b'b'*60)
   r=build_summary(a,b);self.assertEqual(r['gain_pct'],40.0);self.assertIn('40.00 %',format_summary(r))
 def test_increase_warns(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'a',Path(d)/'b';a.write_bytes(b'a'*40);b.write_bytes(b'b'*80)
   r=build_summary(a,b);self.assertEqual(r['gain_pct'],-100.0);self.assertTrue(r['warnings'])
 def test_equal(self):
  with tempfile.TemporaryDirectory() as d:
   a,b=Path(d)/'a',Path(d)/'b';a.write_bytes(b'123');b.write_bytes(b'abc')
   self.assertIn('Taille inchangée',format_summary(build_summary(a,b)))
 def test_invalid(self):
  with self.assertRaises(TypeError):format_summary(None)
if __name__=='__main__':unittest.main()
