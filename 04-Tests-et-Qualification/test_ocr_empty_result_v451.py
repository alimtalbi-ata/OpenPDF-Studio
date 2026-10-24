"""A visually blank OCR result must not be reported as successful."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_ocr_service_v347 import searchable_pdf

class EmptyOCRTests(unittest.TestCase):
    def test_empty_recognition_refuses_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'scan.pdf';target=root/'recognized.pdf'
            with fitz.open() as document:
                page=document.new_page()
                page.draw_rect(fitz.Rect(30,30,90,90),color=(0,0,0),fill=(0,0,0))
                document.save(source)
            with fitz.open() as blank:
                blank.new_page()
                blank_bytes=blank.tobytes()
            with patch.object(fitz.Pixmap,'pdfocr_tobytes',return_value=blank_bytes):
                with self.assertRaisesRegex(RuntimeError,'OCR sans texte reconnu'):
                    searchable_pdf(source,target,language='eng')
            self.assertFalse(target.exists())
            self.assertFalse(list(root.glob('.openpdf-ocr-*')))
if __name__=='__main__':unittest.main()
