"""Lossless image placement regression. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_quality_v422 import validate_lossless_images

class ImagePlacementTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        pix=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,8,8),False)
        pix.clear_with(0x44)
        self.png=pix.tobytes('png')
        self.source=self.root/'source.pdf'
        self._make(self.source,fitz.Rect(20,20,120,120))
    def _make(self,path,rect):
        with fitz.open() as doc:
            page=doc.new_page()
            page.insert_image(rect,stream=self.png)
            doc.save(path)
    def test_same_position_passes(self):
        candidate=self.root/'optimized.pdf'
        with fitz.open(self.source) as doc:
            doc.save(candidate,garbage=4,deflate=True)
        self.assertEqual(validate_lossless_images(self.source,candidate)['images_verified'],1)
    def test_same_image_moved_on_page_rejected(self):
        candidate=self.root/'moved.pdf'
        self._make(candidate,fitz.Rect(120,120,220,220))
        with self.assertRaisesRegex(RuntimeError,'positions modifiées'):
            validate_lossless_images(self.source,candidate)
    def test_repeated_image_occurrence_count(self):
        candidate=self.root/'repeated.pdf'
        with fitz.open(self.source) as doc:
            page=doc[0]
            page.insert_image(fitz.Rect(200,200,300,300),xref=page.get_images(full=True)[0][0])
            doc.save(candidate)
        with self.assertRaisesRegex(RuntimeError,'positions modifiées'):
            validate_lossless_images(self.source,candidate)
if __name__=='__main__':unittest.main()
