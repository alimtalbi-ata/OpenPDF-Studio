import tempfile,unittest
from pathlib import Path
import fitz
from openpdf_page_service_v345 import merge,extract,reorder,split
class PageServiceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.d=Path(self.temp.name)
  self.src=self.d/'src.pdf'
  with fitz.open() as doc:
   for i in range(3):doc.new_page().insert_text((72,72),f'PAGE-{i+1}')
   doc.save(self.src)
 def test_merge(self):
  r=merge([self.src,self.src],self.d/'merged.pdf');self.assertEqual(r.page_counts,(6,));self.assertEqual(len(r.sha256[0]),64)
 def test_extract(self):
  r=extract(self.src,self.d/'extracted.pdf',2,3);self.assertEqual(r.page_counts,(2,))
 def test_reorder(self):
  r=reorder(self.src,self.d/'reordered.pdf',[3,1,3]);self.assertEqual(r.page_counts,(3,))
  with fitz.open(r.outputs[0]) as doc:self.assertIn('PAGE-3',doc[0].get_text())
 def test_split(self):
  r=split(self.src,self.d,2);self.assertEqual(r.page_counts,(2,1));self.assertEqual(len(r.outputs),2)
 def test_split_collision(self):
  split(self.src,self.d,1)
  with self.assertRaises(FileExistsError):split(self.src,self.d,1)
 def test_source_protection(self):
  with self.assertRaises(ValueError):merge([self.src],self.src)
 def test_invalid_range(self):
  with self.assertRaises(ValueError):extract(self.src,self.d/'bad.pdf',1,9)
 def test_no_partial_invalid_source(self):
  with self.assertRaises(Exception):merge([self.src,self.d/'missing.pdf'],self.d/'out.pdf')
  self.assertFalse((self.d/'out.pdf').exists())
if __name__=='__main__':unittest.main()
