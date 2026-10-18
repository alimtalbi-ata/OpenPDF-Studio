import tempfile,unittest
from pathlib import Path
import fitz
from openpdf_ocr_service_v347 import searchable_pdf,OCRReceipt

class OCRTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name); self.source=self.base/'input.pdf'; self.out=self.base/'output.pdf'
        with fitz.open() as doc:
            p=doc.new_page();p.insert_text((70,70),'Existing searchable text')
            doc.save(self.source)
    def test_preserves_text_without_tesseract(self):
        r=searchable_pdf(self.source,self.out)
        self.assertIsInstance(r,OCRReceipt);self.assertEqual((r.pages,r.ocr_pages,r.skipped_pages),(1,0,1))
        with fitz.open(self.out) as doc:self.assertIn('Existing searchable text',doc[0].get_text())
    def test_source_preserved(self):
        old=self.source.read_bytes();searchable_pdf(self.source,self.out);self.assertEqual(old,self.source.read_bytes())
    def test_same_path(self):
        with self.assertRaises(ValueError):searchable_pdf(self.source,self.source)
    def test_invalid_language(self):
        with self.assertRaises(ValueError):searchable_pdf(self.source,self.out,language='fr;rm')
    def test_invalid_dpi(self):
        with self.assertRaises(ValueError):searchable_pdf(self.source,self.out,dpi=500)
    def test_no_parent(self):
        with self.assertRaises(ValueError):searchable_pdf(self.source,self.base/'missing'/'out.pdf')
    def test_cancel_does_not_publish(self):
        def stop(*_):raise RuntimeError('cancel')
        with self.assertRaisesRegex(RuntimeError,'cancel'):searchable_pdf(self.source,self.out,progress=stop)
        self.assertFalse(self.out.exists())
    def test_invalid_tessdata(self):
        with self.assertRaises(ValueError):searchable_pdf(self.source,self.out,tessdata=self.base/'missing')
if __name__=='__main__':unittest.main()
