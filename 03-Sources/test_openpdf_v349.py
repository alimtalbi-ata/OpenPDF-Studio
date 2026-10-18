import unittest,tempfile
from pathlib import Path
from openpdf_workspace_v349 import page_window,next_page,previous_page,validate_request
class WorkspaceTests(unittest.TestCase):
 def test_bounds(self):
  self.assertEqual(page_window(-4,3),0);self.assertEqual(page_window(10,3),2)
 def test_navigation(self):
  self.assertEqual(next_page(2,3),2);self.assertEqual(previous_page(0,3),0)
 def test_empty(self):
  with self.assertRaises(ValueError):page_window(0,0)
 def test_missing_source(self):
  with self.assertRaises(ValueError):validate_request('fusion',['/missing.pdf'],'/tmp/out.pdf')
 def test_collision(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.pdf';p.write_bytes(b'%PDF')
   with self.assertRaises(ValueError):validate_request('compression',[p],p)
 def test_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.pdf';p.write_bytes(b'%PDF')
   with self.assertRaises(ValueError):validate_request('fusion',[p,p],Path(d)/'out.pdf')
 def test_valid(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.pdf';p.write_bytes(b'%PDF');a,b=validate_request('compression',[p],Path(d)/'out.pdf');self.assertEqual(a,(str(p),));self.assertTrue(b.endswith('out.pdf'))
if __name__=='__main__':unittest.main()
