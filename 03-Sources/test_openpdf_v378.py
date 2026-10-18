import unittest, tempfile
from pathlib import Path
import fitz
from openpdf_preview import render_preview
class PreviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.pdf'
  with fitz.open() as doc:
   for i in range(3):doc.new_page(width=600,height=800).insert_text((40,40),str(i))
   doc.save(self.path)
 def tearDown(self):self.tmp.cleanup()
 def test_first_page(self):
  r=render_preview(self.path);self.assertEqual(r['pages'],3);self.assertEqual(r['page'],0)
 def test_clamp_page(self):self.assertEqual(render_preview(self.path,99)['page'],2)
 def test_image_size(self):
  r=render_preview(self.path);self.assertLessEqual(r['size'][0],460);self.assertLessEqual(r['size'][1],520)
 def test_invalid_size(self):
  with self.assertRaises(ValueError):render_preview(self.path,max_width=0)
 def test_missing(self):
  with self.assertRaises(Exception):render_preview(self.path.with_name('missing.pdf'))
if __name__=='__main__':unittest.main()
