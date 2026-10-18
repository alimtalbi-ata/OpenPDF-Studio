import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_preview_v325 import render_comparison
class TestV325(unittest.TestCase):
 def test_preview_png_and_source_unchanged(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.pdf';doc=fitz.open();doc.new_page().insert_text((72,72),'Source intacte');doc.save(p);doc.close();data=p.read_bytes()
   before,after=render_comparison(p)
   self.assertTrue(before.startswith(b'\x89PNG'));self.assertTrue(after.startswith(b'\x89PNG'));self.assertEqual(p.read_bytes(),data)
 def test_invalid_page(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.pdf';doc=fitz.open();doc.new_page();doc.save(p);doc.close()
   with self.assertRaises(IndexError):render_comparison(p,2)
 def test_invalid_dpi(self):
  with self.assertRaises(ValueError):render_comparison('missing.pdf',dpi=500)
if __name__=='__main__':unittest.main()
