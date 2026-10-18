import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_core_v261 import page_info,preview_png,edit_pages
class TestV261(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.src=self.root/'source.pdf'
  with fitz.open() as d:
   for i in range(3):
    p=d.new_page();p.insert_text((72,72),f'PAGE-{i+1}')
   d.save(self.src)
 def test_info(self):self.assertEqual(len(page_info(self.src)),3)
 def test_preview(self):self.assertTrue(preview_png(self.src,2).startswith(b'\x89PNG'))
 def test_preview_invalid(self):
  with self.assertRaises(ValueError):preview_png(self.src,0)
 def test_edit_order(self):
  target=self.root/'out.pdf';edit_pages(self.src,target,[3,1],{3:90})
  with fitz.open(target) as d:
   self.assertEqual(len(d),2);self.assertIn('PAGE-3',d[0].get_text());self.assertEqual(d[0].rotation,90)
 def test_duplicate(self):
  with self.assertRaises(ValueError):edit_pages(self.src,self.root/'out.pdf',[1,1])
 def test_source_guard(self):
  with self.assertRaises(ValueError):edit_pages(self.src,self.src,[1])
if __name__=='__main__':unittest.main()
