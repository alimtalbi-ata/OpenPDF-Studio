import unittest, tempfile
from pathlib import Path
from unittest.mock import patch
import fitz
from openpdf_roundtrip_v355 import qualify_roundtrip, save_report

class RoundtripTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.pdf=Path(self.tmp.name)/'source.pdf'
  with fitz.open() as doc:
   p=doc.new_page(); p.insert_text((70,70),'Document de reference'); doc.save(self.pdf)
 def test_invalid_format(self):
  with self.assertRaises(ValueError): qualify_roundtrip(self.pdf,office_format='txt')
 def test_missing_source(self):
  with self.assertRaises(ValueError): qualify_roundtrip(Path(self.tmp.name)/'missing.pdf')
 def test_invalid_timeout(self):
  with self.assertRaises(ValueError): qualify_roundtrip(self.pdf,timeout=0)
 def test_missing_engine(self):
  with patch('openpdf_roundtrip_v355.shutil.which',return_value=None):
   with self.assertRaisesRegex(RuntimeError,'LibreOffice absent'): qualify_roundtrip(self.pdf)
 def test_roundtrip_docx(self):
  import shutil
  if not (shutil.which('libreoffice') or shutil.which('soffice')): self.skipTest('LibreOffice absent')
  result=qualify_roundtrip(self.pdf,office_format='docx',max_pages=2)
  self.assertEqual(result.office_format,'docx'); self.assertEqual(result.visual['compared_pages'],1)
  report=Path(self.tmp.name)/'report.json';save_report(result,report);self.assertTrue(report.is_file())
if __name__=='__main__':unittest.main()
