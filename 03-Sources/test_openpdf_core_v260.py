import tempfile,unittest
from pathlib import Path
import fitz
from openpdf_core_v260 import *
class TestWindowsCore(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.a=self.root/'a.pdf';self.b=self.root/'b.pdf'
  for path,text in ((self.a,'Alpha'),(self.b,'Beta')):
   with fitz.open() as d:
    p=d.new_page();p.insert_text((60,60),text);d.save(path)
 def tearDown(self):self.temp.cleanup()
 def test_merge(self):
  result=merge_pdfs([self.a,self.b],self.root/'merged.pdf')
  with fitz.open(result[0]) as d:self.assertEqual(len(d),2)
 def test_split(self):
  merged=merge_pdfs([self.a,self.b],self.root/'merged.pdf')[0]
  self.assertEqual(len(split_pdf(merged,self.root/'split')),2)
 def test_compress(self):
  out=compress_pdf(self.a,self.root/'compressed.pdf')[0]
  with fitz.open(out) as d:self.assertEqual(len(d),1)
 def test_text(self):self.assertIn('Alpha',(extract_text(self.a,self.root/'out.txt')[0]).read_text())
 def test_word(self):self.assertTrue(pdf_to_docx(self.a,self.root/'out.docx')[0].exists())
 def test_excel(self):self.assertTrue(pdf_to_xlsx(self.a,self.root/'out.xlsx')[0].exists())
 def test_ppt(self):self.assertTrue(pdf_to_pptx(self.a,self.root/'out.pptx')[0].exists())
 def test_no_overwrite_source(self):
  with self.assertRaises(PDFOperationError):compress_pdf(self.a,self.a)
 def test_no_invalid(self):
  with self.assertRaises(PDFOperationError):merge_pdfs([],self.root/'x.pdf')
if __name__=='__main__':unittest.main()
