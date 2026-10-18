import unittest,tempfile,sys,json
from pathlib import Path
from openpdf_binary_manifest import inspect, VERSION
class TestBinaryManifest(unittest.TestCase):
 def test_missing_binaries_reported_honestly(self):
  with tempfile.TemporaryDirectory() as d:
   r=inspect(d);self.assertEqual(len(r['binaries']),2);self.assertTrue(all(not x['present'] for x in r['binaries']))
 def test_fake_exe_not_accepted(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/f'OpenPDF-Studio-Portable-V{VERSION}.exe').write_bytes(b'not a PE')
   self.assertFalse(inspect(d)['binaries'][1]['pe_mz_header'])
 def test_pe_header_and_hash(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/f'OpenPDF-Studio-Portable-V{VERSION}.exe').write_bytes(b'MZ'+bytes(58)+(128).to_bytes(4,'little')+bytes(64)+b'PE\0\0'+bytes(128))
   self.assertEqual(len(inspect(d)['binaries'][1]['sha256']),64)
