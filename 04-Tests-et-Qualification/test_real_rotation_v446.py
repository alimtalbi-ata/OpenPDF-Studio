"""End-to-end rotation tests using actual PDFs and public operation dispatcher."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_operations import run_operation

class RotationE2ETests(unittest.TestCase):
    def test_three_angles_preserve_text_and_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'source.pdf'
            with fitz.open() as pdf:
                page=pdf.new_page(width=300,height=500)
                page.insert_text((70,70),'ROTATION CHECK')
                pdf.save(source)
            original=source.read_bytes()
            for angle in (90,180,270):
                target=root/f'rotated-{angle}.pdf'
                run_operation('rotation',[source],target,order=str(angle))
                with fitz.open(target) as pdf:
                    self.assertEqual(pdf[0].rotation,angle)
                    self.assertIn('ROTATION CHECK',pdf[0].get_text())
                self.assertEqual(source.read_bytes(),original)
    def test_invalid_angle_does_not_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/'source.pdf'
            with fitz.open() as pdf:
                pdf.new_page()
                pdf.save(source)
            destination=root/'output.pdf'
            with self.assertRaises(ValueError):
                run_operation('rotation',[source],destination,order='45')
            self.assertFalse(destination.exists())
if __name__=='__main__':
    unittest.main()
