"""Page box geometry preservation regression. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_render_quality_v425 import validate_rendered_pages

class PageGeometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'source.pdf'
        with fitz.open() as pdf:
            pdf.new_page(width=400,height=600)
            pdf.save(self.source)
    def _mutate(self,name,mutation):
        path=self.root/name
        with fitz.open(self.source) as pdf:
            mutation(pdf[0])
            pdf.save(path)
        return path
    def test_unchanged_geometry_passes(self):
        candidate=self._mutate('same.pdf',lambda page:None)
        self.assertEqual(validate_rendered_pages(self.source,candidate)['pages_rendered'],1)
    def test_rotation_change_rejected(self):
        candidate=self._mutate('rotated.pdf',lambda page:page.set_rotation(180))
        with self.assertRaisesRegex(RuntimeError,'Géométrie PDF modifiée'):
            validate_rendered_pages(self.source,candidate)
    def test_cropbox_change_rejected(self):
        candidate=self._mutate('cropped.pdf',lambda page:page.set_cropbox(fitz.Rect(10,10,390,590)))
        with self.assertRaisesRegex(RuntimeError,'Géométrie PDF modifiée'):
            validate_rendered_pages(self.source,candidate)
if __name__=='__main__':unittest.main()
