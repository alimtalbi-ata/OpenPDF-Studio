import unittest,tempfile
from pathlib import Path
from unittest.mock import Mock
from openpdf_compression_v319 import validate_compression,size_report,guided_compress
class CompressionTests(unittest.TestCase):
 def test_paths_and_size(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'x'*100);b.write_bytes(b'y'*120)
   self.assertEqual(validate_compression(a,b),(str(a),str(b)))
   self.assertFalse(size_report(a,b)['smaller'])
   self.assertEqual(size_report(a,b)['saved_bytes'],-20)
   with self.assertRaises(ValueError):validate_compression(a,a)
   with self.assertRaises(ValueError):validate_compression(a,Path(t)/'x.txt')
 def test_guided_dispatch(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'PDF')
   app=Mock();app.busy=False;app._v272_busy=False
   self.assertTrue(guided_compress(app,ask_source=lambda:str(a),ask_destination=lambda _:str(b)))
   self.assertEqual(app._run_pdf.call_count,1)
 def test_cancel_and_busy(self):
  app=Mock();app.busy=True
  self.assertFalse(guided_compress(app,ask_source=lambda:'unused'))
  app.busy=False;app._v272_busy=False
  self.assertFalse(guided_compress(app,ask_source=lambda:None))
if __name__=='__main__':unittest.main()
