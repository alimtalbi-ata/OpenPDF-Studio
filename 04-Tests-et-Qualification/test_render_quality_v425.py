"""Real render parity tests on vector content. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_render_quality_v425 import validate_rendered_pages

class RenderParityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/'original.pdf'
        self._make(self.source,False)
    def _make(self,path,extra):
        with fitz.open() as pdf:
            page=pdf.new_page()
            page.draw_rect(fitz.Rect(60,90,230,170),color=(0,0,0),fill=(0.2,0.5,0.8))
            if extra: page.draw_circle((330,240),35,color=(1,0,0),fill=(1,0,0))
            pdf.save(path)
    def test_equivalent_optimized_pdf(self):
        candidate=self.root/'candidate.pdf'
        with fitz.open(self.source) as doc:
            doc.save(candidate,garbage=4,deflate=True)
        self.assertEqual(validate_rendered_pages(self.source,candidate)['pages_rendered'],1)
    def test_vector_change_without_text_change_is_rejected(self):
        candidate=self.root/'changed.pdf';self._make(candidate,True)
        with self.assertRaisesRegex(RuntimeError,'Rendu visuel modifié'):
            validate_rendered_pages(self.source,candidate)
    def test_invalid_limits_rejected(self):
        with self.assertRaises(ValueError):
            validate_rendered_pages(self.source,self.source,max_pixels=10)
if __name__=='__main__':unittest.main()
