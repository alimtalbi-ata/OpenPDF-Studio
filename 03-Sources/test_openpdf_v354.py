import unittest, tempfile
from pathlib import Path
import fitz
from openpdf_visual_fidelity_v354 import compare_pdf_renders,write_visual_report
class VisualTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.a=Path(self.temp.name)/'a.pdf';self.b=Path(self.temp.name)/'b.pdf'
 def pdf(self,path,text='Hello',pages=1):
  with fitz.open() as doc:
   for _ in range(pages):doc.new_page().insert_text((72,72),text)
   doc.save(path)
 def test_identical(self):
  self.pdf(self.a);self.b.write_bytes(self.a.read_bytes());self.assertEqual(compare_pdf_renders(self.a,self.b).mean_absolute_error,0)
 def test_changed(self):
  self.pdf(self.a,'Hello');self.pdf(self.b,'Different');self.assertGreater(compare_pdf_renders(self.a,self.b).mean_absolute_error,0)
 def test_page_count(self):
  self.pdf(self.a,pages=2);self.pdf(self.b);self.assertIn('Nombre de pages différent',compare_pdf_renders(self.a,self.b).warnings)
 def test_missing(self):
  with self.assertRaises(FileNotFoundError):compare_pdf_renders(self.a,self.b)
 def test_dpi(self):
  self.pdf(self.a);self.pdf(self.b)
  with self.assertRaises(ValueError):compare_pdf_renders(self.a,self.b,dpi=5)
 def test_report(self):
  self.pdf(self.a);self.pdf(self.b);out=Path(self.temp.name)/'report.json';write_visual_report(compare_pdf_renders(self.a,self.b),out);self.assertIn('mean_absolute_error',out.read_text())
 def test_partial(self):
  self.pdf(self.a,pages=3);self.pdf(self.b,pages=3);self.assertIn('Comparaison partielle: limite max_pages',compare_pdf_renders(self.a,self.b,max_pages=1).warnings)
if __name__=='__main__':unittest.main()
