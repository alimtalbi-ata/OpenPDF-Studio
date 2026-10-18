import tempfile, unittest
from pathlib import Path
from openpdf_output_receipt_v337 import fingerprint, compression_publication

class ReceiptTests(unittest.TestCase):
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(compression_publication(None,Path(d)/'missing.pdf','done')[0])
    def test_no_gain_old_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.pdf';p.write_bytes(b'old')
            self.assertFalse(compression_publication(fingerprint(p),p,'Aucun gain : Aucun fichier de sortie modifié.')[0])
    def test_unchanged_existing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.pdf';p.write_bytes(b'old')
            self.assertFalse(compression_publication(fingerprint(p),p,'success')[0])
    def test_new_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.pdf';p.write_bytes(b'new')
            self.assertTrue(compression_publication(None,p,'success')[0])
    def test_replaced_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.pdf';p.write_bytes(b'old');before=fingerprint(p)
            p.unlink();p.write_bytes(b'new file')
            self.assertTrue(compression_publication(before,p,'success')[0])
    def test_empty(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.pdf';p.touch()
            self.assertFalse(compression_publication(None,p,'success')[0])
if __name__=='__main__': unittest.main()
