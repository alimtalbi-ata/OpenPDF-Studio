import tempfile
import unittest
from pathlib import Path
from openpdf_engine_v272 import compress_pdf, PDFOperationError

class EngineTests(unittest.TestCase):
    def test_compression_and_source_preservation(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp)/'input.pdf', Path(tmp)/'output.pdf'
            with fitz.open() as doc:
                doc.new_page().insert_text((50, 50), 'V27.2')
                doc.save(src)
            before = src.read_bytes()
            compress_pdf(src, dst)
            with fitz.open(dst) as doc:
                self.assertEqual(len(doc), 1)
            self.assertEqual(src.read_bytes(), before)
    def test_reject_source_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'a.pdf'
            src.write_bytes(b'%PDF-1.4')
            with self.assertRaises(PDFOperationError):
                compress_pdf(src, src)
    def test_cancel_before_write(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp)/'a.pdf', Path(tmp)/'b.pdf'
            with fitz.open() as doc:
                doc.new_page(); doc.save(src)
            with self.assertRaises(PDFOperationError):
                compress_pdf(src, dst, cancelled=lambda: True)
            self.assertFalse(dst.exists())
