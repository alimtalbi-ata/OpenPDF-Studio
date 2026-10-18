import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_quality_metrics_v356 import compare_structure,save_metrics
from openpdf_roundtrip_v356 import qualify
class QualityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.a=Path(self.tmp.name)/'a.pdf';self.b=Path(self.tmp.name)/'b.pdf'
  for path,text,pages in [(self.a,'alpha beta beta',1),(self.b,'alpha',2)]:
   with fitz.open() as doc:
    for i in range(pages):doc.new_page().insert_text((70,70),text)
    doc.save(path)
 def test_identical(self):
  x=compare_structure(self.a,self.a);self.assertEqual(x.word_recall,1);self.assertEqual(x.page_delta,0)
 def test_different(self):
  x=compare_structure(self.a,self.b);self.assertEqual(x.page_delta,1);self.assertLess(x.word_recall,1)
 def test_page_limit(self):self.assertTrue(compare_structure(self.b,self.a,max_pages=1).warnings)
 def test_bad_limit(self):
  with self.assertRaises(ValueError):compare_structure(self.a,self.b,max_pages=0)
 def test_missing(self):
  with self.assertRaises(FileNotFoundError):compare_structure(self.a,self.b.with_name('absent.pdf'))
 def test_export(self):
  p=Path(self.tmp.name)/'report.json';save_metrics(compare_structure(self.a,self.b),p);self.assertIn('word_recall',p.read_text())
 def test_bad_format(self):
  with self.assertRaises(ValueError):qualify(self.a,office_format='txt')
 def test_roundtrip_docx(self):
  import shutil
  if not (shutil.which('libreoffice') or shutil.which('soffice')):self.skipTest('LibreOffice absent')
  x=qualify(self.a,max_pages=2);self.assertEqual(x.office_format,'docx');self.assertIn('word_recall',x.structure)
if __name__=='__main__':unittest.main()
