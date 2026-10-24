"""OCR must explain missing Tesseract instead of returning an opaque exception."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_ocr_service_v347 import searchable_pdf

class OCRDiagnosticsTests(unittest.TestCase):
    def test_missing_language_is_actionable_and_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'scan.pdf';target=root/'ocr.pdf'
            with fitz.open() as pdf:
                pdf.new_page()
                pdf.save(source)
            with patch.object(fitz.Pixmap,'pdfocr_tobytes',side_effect=RuntimeError('Tesseract language data missing')):
                with self.assertRaisesRegex(RuntimeError,'TESSDATA_PREFIX'):
                    searchable_pdf(source,target,language='fra+eng')
            self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('.openpdf-ocr-*')))
if __name__=='__main__':unittest.main()
