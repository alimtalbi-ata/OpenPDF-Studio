"""End-to-end French OCR with the actual Tesseract engine."""
import sys,tempfile,unittest
from pathlib import Path
import fitz
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_ocr_service_v347 import searchable_pdf,locate_tessdata

class RealFrenchOCRTests(unittest.TestCase):
    def test_french_and_english_models_on_raster(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'scan.pdf';target=root/'searchable.pdf'
            with fitz.open() as original:
                page=original.new_page(width=595,height=842)
                page.insert_text((70,140),'DOCUMENT FACTURE TEST',fontsize=26)
                image=page.get_pixmap(dpi=200,alpha=False).tobytes('png')
            with fitz.open() as raster:
                page=raster.new_page(width=595,height=842)
                page.insert_image(page.rect,stream=image)
                raster.save(source)
            self.assertEqual(fitz.open(source)[0].get_text('text').strip(),'')
            receipt=searchable_pdf(source,target,language='fra+eng',dpi=200)
            self.assertEqual(receipt.ocr_pages,1)
            with fitz.open(target) as output:
                text=output[0].get_text('text').upper()
                self.assertIn('DOCUMENT',text)
                self.assertIn('FACTURE',text)
if __name__=='__main__':unittest.main()
