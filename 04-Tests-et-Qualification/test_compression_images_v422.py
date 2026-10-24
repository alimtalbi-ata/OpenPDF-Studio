"""Real PDF image fidelity checks. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_compression_quality_v422 import validate_lossless_images

class ImageFidelityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.pdf'
        self._make(self.source,0x33)
    def _make(self,path,color):
        pix=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,8,8),False)
        pix.clear_with(color)
        with fitz.open() as doc:
            doc.new_page().insert_image(fitz.Rect(10,10,90,90),stream=pix.tobytes('png'))
            doc.save(path)
    def test_unchanged_images(self):
        candidate=self.root/'candidate.pdf'
        with fitz.open(self.source) as doc:
            doc.save(candidate,garbage=4,deflate=True,deflate_images=True)
        self.assertEqual(validate_lossless_images(self.source,candidate)['images_verified'],1)
    def test_changed_images_rejected(self):
        candidate=self.root/'changed.pdf'
        self._make(candidate,0x99)
        with self.assertRaisesRegex(RuntimeError,'Images modifiées'):
            validate_lossless_images(self.source,candidate)
if __name__=='__main__':unittest.main()
