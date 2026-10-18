import unittest,tempfile
from pathlib import Path
from openpdf_compression_service_v344 import CompressionRequest,validate_compression_request,execute_compression
from openpdf_transaction_v338 import verify_receipt

class CompressionServiceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.src=Path(self.tmp.name)/'input.pdf';self.dst=Path(self.tmp.name)/'out.pdf';self.src.write_bytes(b'%PDF-1.4 test')
 def request(self,profile='smaller_only'):return CompressionRequest(str(self.src),str(self.dst),profile)
 def test_unknown_profile(self):
  with self.assertRaises(ValueError):validate_compression_request(self.request('unknown'))
 def test_same_path(self):
  with self.assertRaises(ValueError):validate_compression_request(CompressionRequest(str(self.src),str(self.src)))
 def test_missing_source(self):
  self.src.unlink()
  with self.assertRaises(ValueError):validate_compression_request(self.request())
 def test_no_gain_keeps_existing_destination(self):
  self.dst.write_bytes(b'OLD OUTPUT')
  receipt=execute_compression(self.request(),lambda a,b,c:'Aucun gain : Aucun fichier de sortie modifié')
  self.assertFalse(receipt.published);self.assertEqual(self.dst.read_bytes(),b'OLD OUTPUT')
 def test_published_verified(self):
  def engine(a,b,c):Path(b).write_bytes(b'%PDF-1.4 new');return 'Publié'
  receipt=execute_compression(self.request(),engine)
  self.assertTrue(receipt.published);self.assertTrue(verify_receipt(receipt,self.dst)[0])
 def test_tampering_rejected(self):
  def engine(a,b,c):Path(b).write_bytes(b'%PDF-1.4 new');return 'Publié'
  receipt=execute_compression(self.request(),engine);self.dst.write_bytes(b'CORRUPTED')
  self.assertFalse(verify_receipt(receipt,self.dst)[0])
 def test_missing_output_rejected(self):
  with self.assertRaises(RuntimeError):execute_compression(self.request(),lambda a,b,c:'Publié')
if __name__=='__main__':unittest.main()
