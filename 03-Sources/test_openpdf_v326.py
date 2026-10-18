import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_preview_v326 import render_comparison
class TestV326(unittest.TestCase):
 def test_pages_and_original_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.pdf';doc=fitz.open()
   for i in range(3):doc.new_page().insert_text((72,72),f'Page {i+1}')
   doc.save(p);doc.close();original=p.read_bytes()
   for i in range(3):
    before,after=render_comparison(p,i)
    self.assertTrue(before.startswith(b'\x89PNG'))
    self.assertTrue(after.startswith(b'\x89PNG'))
   self.assertEqual(p.read_bytes(),original)
 def test_out_of_range(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.pdf';doc=fitz.open();doc.new_page();doc.save(p);doc.close()
   with self.assertRaises(IndexError):render_comparison(p,1)
 def test_dpi_limit(self):
  with self.assertRaises(ValueError):render_comparison('missing.pdf',dpi=300)
if __name__=='__main__':unittest.main()
