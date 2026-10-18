import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_quality_v327 import assess_candidate,quality_summary
class TestV327(unittest.TestCase):
 def pdf(self,path,text='Texte',pages=1):
  doc=fitz.open()
  for _ in range(pages):doc.new_page().insert_text((72,72),text)
  doc.save(path);doc.close()
 def test_same_pdf(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a);b.write_bytes(a.read_bytes())
   result=assess_candidate(a,b);self.assertEqual(result['gain_pourcent'],0)
   self.assertEqual(result['pages_texte_modifie'],[])
   self.assertIn('Aucun gain',quality_summary(result))
 def test_text_change_detected(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a,'ABC');self.pdf(b,'XYZ')
   self.assertEqual(assess_candidate(a,b)['pages_texte_modifie'],[1])
 def test_page_count_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';self.pdf(a);self.pdf(b,pages=2)
   with self.assertRaises(ValueError):assess_candidate(a,b)
 def test_missing_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.pdf';self.pdf(a)
   with self.assertRaises(FileNotFoundError):assess_candidate(a,Path(d)/'absent.pdf')
if __name__=='__main__':unittest.main()
