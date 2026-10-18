import unittest, tempfile, pathlib, sys
from unittest.mock import patch
from openpdf_ocr_service_v347 import searchable_pdf

class OCRSafety(unittest.TestCase):
    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            import fitz
            a=pathlib.Path(td)/"source.pdf"; b=pathlib.Path(td)/"existing.pdf"
            with fitz.open() as d:
                d.new_page().insert_text((70,70),"Text page")
                d.save(a)
            b.write_bytes(b"KEEP-ME")
            with self.assertRaises(FileExistsError):searchable_pdf(a,b)
            self.assertEqual(b.read_bytes(),b"KEEP-ME")
    def test_text_page_without_tesseract(self):
        with tempfile.TemporaryDirectory() as td:
            import fitz
            a=pathlib.Path(td)/"source.pdf"; b=pathlib.Path(td)/"out.pdf"
            with fitz.open() as d:
                d.new_page().insert_text((70,70),"Bonjour OCR")
                d.save(a)
            receipt=searchable_pdf(a,b)
            self.assertEqual(receipt.skipped_pages,1)
            self.assertEqual(receipt.ocr_pages,0)
            with fitz.open(b) as d:self.assertIn("Bonjour",d[0].get_text())
    def test_invalid_language(self):
        with tempfile.TemporaryDirectory() as td:
            a=pathlib.Path(td)/"a.pdf";a.write_bytes(b"notpdf")
            with self.assertRaises(ValueError):searchable_pdf(a,pathlib.Path(td)/"b.pdf",language="fra;cmd")
    def test_invalid_dpi(self):
        with tempfile.TemporaryDirectory() as td:
            a=pathlib.Path(td)/"a.pdf";a.write_bytes(b"notpdf")
            with self.assertRaises(ValueError):searchable_pdf(a,pathlib.Path(td)/"b.pdf",dpi=600)
if __name__=="__main__":unittest.main()
