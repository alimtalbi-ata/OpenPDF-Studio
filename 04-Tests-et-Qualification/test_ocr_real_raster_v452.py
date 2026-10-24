"""Real, non-mocked OCR: render text as pixels and recover searchable text."""
import os,sys,tempfile,unittest
from pathlib import Path
import fitz
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_ocr_service_v347 import searchable_pdf,locate_tessdata

class RealOCRRasterTests(unittest.TestCase):
    def test_rasterized_pdf_recovers_searchable_text(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'scan.pdf';target=root/'searchable.pdf'
            with fitz.open() as text_doc:
                page=text_doc.new_page(width=595,height=842)
                page.insert_text((70,130),'OPENPDF SCAN TEST',fontsize=28)
                pix=page.get_pixmap(dpi=200,alpha=False)
                png=pix.tobytes('png')
            with fitz.open() as scan:
                page=scan.new_page(width=595,height=842)
                page.insert_image(page.rect,stream=png)
                scan.save(source)
            with fitz.open(source) as before:
                self.assertEqual(before[0].get_text('text').strip(),'')
            receipt=searchable_pdf(source,target,language='eng',dpi=200,skip_text=True)
            self.assertEqual((receipt.pages,receipt.ocr_pages),(1,1))
            with fitz.open(target) as recognized:
                result=recognized[0].get_text('text').upper()
                self.assertIn('OPENPDF',result)
                self.assertIn('SCAN',result)
            with fitz.open(source) as after:
                self.assertEqual(after[0].get_text('text').strip(),'')
if __name__=='__main__':unittest.main()
