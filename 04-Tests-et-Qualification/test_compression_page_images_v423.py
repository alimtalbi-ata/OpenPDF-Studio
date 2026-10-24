"""Page-local image fidelity tests. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_quality_v422 import validate_lossless_images

class PageLocalImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.png=[]
        for color in (0x22,0x88):
            pix=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,8,8),False)
            pix.clear_with(color)
            self.png.append(pix.tobytes('png'))
        self.source=self.root/'source.pdf'
        self._make(self.source,[0,1])
    def _make(self,path,order):
        with fitz.open() as doc:
            for index in order:
                page=doc.new_page()
                page.insert_image(fitz.Rect(10,10,90,90),stream=self.png[index])
            doc.save(path)
    def test_same_page_images_accepted(self):
        candidate=self.root/'optimized.pdf'
        with fitz.open(self.source) as doc:
            doc.save(candidate,garbage=4,deflate=True)
        result=validate_lossless_images(self.source,candidate)
        self.assertEqual(result['images_verified'],2)
        self.assertEqual(result['pages_verified'],2)
    def test_swapped_images_rejected_even_if_global_multiset_matches(self):
        candidate=self.root/'swapped.pdf'
        self._make(candidate,[1,0])
        with self.assertRaisesRegex(RuntimeError,'page 1'):
            validate_lossless_images(self.source,candidate)
if __name__=='__main__':unittest.main()
