"""Real PDF image extraction into DOCX; no mocked converters."""
import sys,tempfile,unittest
from pathlib import Path
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from PIL import Image
from docx import Document
from openpdf_operations import run_operation

class OfficeImagesE2E(unittest.TestCase):
    def test_docx_preserves_embedded_png(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            image=Image.new('RGB',(60,30),(220,30,30))
            stream=BytesIO();image.save(stream,format='PNG')
            source=root/'image.pdf'
            with fitz.open() as pdf:
                page=pdf.new_page()
                page.insert_text((50,50),'IMAGE CHECK')
                page.insert_image(fitz.Rect(50,100,170,160),stream=stream.getvalue())
                pdf.save(source)
            target=root/'image.docx'
            run_operation('docx',[source],target)
            doc=Document(target)
            self.assertIn('IMAGE CHECK',' '.join(p.text for p in doc.paragraphs))
            self.assertGreaterEqual(len(doc.inline_shapes),1)
            self.assertTrue(any(part.content_type.startswith('image/') for part in doc.part.related_parts.values()))
if __name__=='__main__':unittest.main()
