import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_visual_quality_v328 import sample_pages,visual_report,visual_summary
class TestV328(unittest.TestCase):
 def pdf(self,path,text='Test',pages=1):
  d=fitz.open()
  for _ in range(pages):d.new_page().insert_text((70,70),text)
  d.save(path);d.close()
 def test_sampling(self):
  self.assertEqual(sample_pages(1),[0]);self.assertEqual(sample_pages(10,3),[0,4,9]);self.assertEqual(sample_pages(2),[0,1])
 def test_identical(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a,pages=3);b.write_bytes(a.read_bytes())
   r=visual_report(a,b);self.assertEqual(r['difference_moyenne_pct'],0);self.assertEqual(r['pages_total'],3)
   self.assertIn('indicatif',visual_summary(r))
 def test_changed(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a,'AAAA');self.pdf(b,'BBBB')
   self.assertGreater(visual_report(a,b)['difference_moyenne_pct'],0)
 def test_page_mismatch(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a);self.pdf(b,pages=2)
   with self.assertRaises(ValueError):visual_report(a,b)
 def test_invalid_dpi(self):
  with self.assertRaises(ValueError):visual_report('a','b',dpi=20)
if __name__=='__main__':unittest.main()
