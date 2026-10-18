import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from openpdf_transaction_v338 import CompressionReceipt,compress_with_receipt,verify_receipt
class ReceiptTests(unittest.TestCase):
    def test_no_gain_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'old.pdf';p.write_bytes(b'old')
            with patch('openpdf_transaction_v338.compress_with_profile',return_value='Aucun gain : Aucun fichier de sortie modifié.'):
                r=compress_with_receipt('src',p)
            self.assertFalse(r.published)
            self.assertFalse(verify_receipt(r,p)[0])
    def test_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new.pdf';p.write_bytes(b'new')
            with patch('openpdf_transaction_v338.compress_with_profile',return_value='ok'):
                r=compress_with_receipt('src',p)
            self.assertTrue(r.published)
            self.assertTrue(verify_receipt(r,p)[0])
    def test_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new.pdf';p.write_bytes(b'new')
            with patch('openpdf_transaction_v338.compress_with_profile',return_value='ok'):
                r=compress_with_receipt('src',p)
            p.write_bytes(b'old')
            self.assertFalse(verify_receipt(r,p)[0])
    def test_missing_output(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('openpdf_transaction_v338.compress_with_profile',return_value='ok'):
                with self.assertRaises(RuntimeError):compress_with_receipt('src',Path(d)/'missing.pdf')
    def test_wrong_destination(self):
        r=CompressionReceipt(True,'/tmp/elsewhere.pdf','ok',10,'a'*64)
        self.assertFalse(verify_receipt(r,'/tmp/different.pdf')[0])
if __name__=='__main__':unittest.main()
