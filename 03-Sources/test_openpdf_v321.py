import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from openpdf_compression_v321 import compress_with_profile,PROFILES
class Tests(unittest.TestCase):
 def test_profiles(self):self.assertEqual(len(PROFILES),2)
 def test_invalid_profile(self):
  with self.assertRaises(ValueError):compress_with_profile('a','b','unknown')
 def test_no_gain_keeps_destination(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'%PDF-1.4'+b'x'*100);b.write_bytes(b'old')
   def fake(s,d):Path(d).write_bytes(b'%PDF-1.4'+b'y'*200)
   with patch('openpdf_compression_v321.compress_pdf',side_effect=fake):msg=compress_with_profile(a,b)
   self.assertIn('Aucun gain',msg);self.assertEqual(b.read_bytes(),b'old')
 def test_smaller_replaces(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'%PDF-1.4'+b'x'*100);b.write_bytes(b'old')
   with patch('openpdf_compression_v321.compress_pdf',side_effect=lambda s,d:Path(d).write_bytes(b'%PDF-1.4')):msg=compress_with_profile(a,b)
   self.assertIn('Gain',msg);self.assertEqual(b.read_bytes(),b'%PDF-1.4')
 def test_failure_keeps_destination(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t)/'a.pdf';b=Path(t)/'b.pdf';a.write_bytes(b'%PDF-1.4');b.write_bytes(b'old')
   with patch('openpdf_compression_v321.compress_pdf',side_effect=RuntimeError('failed')):
    with self.assertRaises(RuntimeError):compress_with_profile(a,b)
   self.assertEqual(b.read_bytes(),b'old')
if __name__=='__main__':unittest.main()
