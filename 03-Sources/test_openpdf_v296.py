"""Real engine/controller integration tests. Abdelhalim Talbi."""
import tempfile, unittest, hashlib
from pathlib import Path
import fitz
from openpdf_commands_v296 import PDFCommands
from openpdf_engine_v271 import PDFOperationError

class TestCommandsV296(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = self.root / 'a.pdf'
        self.b = self.root / 'b.pdf'
        for path, labels in [(self.a, ['alpha', 'beta']), (self.b, ['gamma'])]:
            with fitz.open() as doc:
                for label in labels:
                    doc.new_page().insert_text((72,72),label)
                doc.save(path)
    def test_merge_extract_compress_chain(self):
        events=[]
        ctl=PDFCommands(progress=events.append)
        merged=self.root/'merged.pdf'
        result=ctl.merge([self.a,self.b],merged)
        self.assertEqual(result.operation,'merge')
        self.assertGreater(result.bytes_written,0)
        extracted=self.root/'extracted.pdf'
        ctl.extract(merged,extracted,2,3)
        packed=self.root/'packed.pdf'
        ctl.compress(extracted,packed)
        with fitz.open(packed) as doc:
            self.assertEqual(len(doc),2)
            self.assertIn('gamma',doc[1].get_text())
        self.assertEqual(events[-1],1)
    def test_cancel_preserves_output(self):
        out=self.root/'result.pdf'
        PDFCommands().merge([self.a],out)
        original=hashlib.sha256(out.read_bytes()).digest()
        with self.assertRaises(PDFOperationError):
            PDFCommands(cancelled=lambda:True).merge([self.b],out)
        self.assertEqual(hashlib.sha256(out.read_bytes()).digest(),original)
    def test_invalid_range_preserves_output(self):
        out=self.root/'result.pdf'
        PDFCommands().extract(self.a,out,1,1)
        original=out.read_bytes()
        with self.assertRaises(PDFOperationError):
            PDFCommands().extract(self.a,out,1,200)
        self.assertEqual(out.read_bytes(),original)
    def test_missing_source_rejected(self):
        with self.assertRaises(Exception):
            PDFCommands().compress(self.root/'missing.pdf',self.root/'out.pdf')
    def test_empty_merge_rejected(self):
        with self.assertRaises(PDFOperationError):
            PDFCommands().merge([],self.root/'out.pdf')
    def test_no_tkinter_dependency(self):
        self.assertNotIn('tkinter',(Path(__file__).parent/'openpdf_commands_v296.py').read_text().split('from dataclasses')[1])
if __name__=='__main__':unittest.main()
