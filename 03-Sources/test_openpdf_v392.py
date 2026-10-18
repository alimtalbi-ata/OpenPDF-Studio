import unittest,tempfile,struct
from pathlib import Path
from openpdf_verify_pe import verify
class PETests(unittest.TestCase):
 def test_missing(self):self.assertFalse(verify('/nonexistent/never.exe'))
 def test_truncated(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.exe';p.write_bytes(b'MZ');self.assertFalse(verify(p))
 def test_mz_not_pe(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.exe';p.write_bytes(b'MZ'+bytes(510));self.assertFalse(verify(p))
 def test_valid_minimal_signature(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.exe';data=bytearray(512);data[:2]=b'MZ';struct.pack_into('<I',data,0x3c,128);data[128:132]=b'PE\0\0';p.write_bytes(data);self.assertTrue(verify(p))
if __name__=='__main__':unittest.main()
