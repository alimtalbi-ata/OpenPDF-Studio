"""Real PDF OCR skip-text and failure-atomicity tests; no Tesseract required.
Author: Abdelhalim Talbi.
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'03-Sources'))
from openpdf_ocr_service_v347 import searchable_pdf

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class OCRFunctionalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'text.pdf'
        with fitz.open() as doc:
            for label in ('PAGE-ALPHA','PAGE-BETA'):
                page=doc.new_page()
                page.insert_text((70,100),label)
            doc.save(self.source)
    def test_skip_text_preserves_pages_and_receipt(self):
        output=self.root/'searchable.pdf'
        before=digest(self.source)
        receipt=searchable_pdf(self.source,output,language='fra+eng',skip_text=True)
        self.assertEqual((receipt.pages,receipt.ocr_pages,receipt.skipped_pages),(2,0,2))
        self.assertEqual(receipt.sha256,digest(output))
        self.assertEqual(receipt.bytes_written,output.stat().st_size)
        with fitz.open(output) as doc:
            self.assertEqual([p.get_text().strip() for p in doc],['PAGE-ALPHA','PAGE-BETA'])
        self.assertEqual(before,digest(self.source))
    def test_cancel_before_publication(self):
        output=self.root/'cancelled.pdf'
        def cancel(done,total):
            raise RuntimeError('simulated cancellation')
        with self.assertRaisesRegex(RuntimeError,'simulated cancellation'):
            searchable_pdf(self.source,output,progress=cancel)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob('.openpdf-ocr-*')))
    def test_invalid_language_refuses_output(self):
        output=self.root/'invalid.pdf'
        with self.assertRaisesRegex(ValueError,'Langue OCR invalide'):
            searchable_pdf(self.source,output,language='fra;rm -rf /')
        self.assertFalse(output.exists())
    def test_existing_output_is_preserved(self):
        output=self.root/'existing.pdf';output.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            searchable_pdf(self.source,output)
        self.assertEqual(output.read_bytes(),b'original')
    def test_missing_tessdata_refuses_output(self):
        output=self.root/'missing.pdf'
        with self.assertRaisesRegex(ValueError,'tessdata absent'):
            searchable_pdf(self.source,output,tessdata=self.root/'no-tessdata')
        self.assertFalse(output.exists())
if __name__=='__main__':unittest.main()
