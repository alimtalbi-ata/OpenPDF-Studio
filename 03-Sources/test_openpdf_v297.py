"""Tests de raccordement UI / commandes sans affichage graphique."""
import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import fitz
from openpdf_ui_bridge_v297 import connect,dispatch
from openpdf_engine_v272 import merge_pdfs,extract_pages,compress_pdf
from openpdf_commands_v296 import PDFCommands

class FakeUI:
    def __init__(self): self.calls=[]
    def _run_pdf(self, operation,*args):
        self.calls.append((operation,args))
        return operation(*args)

class TestV297(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.a=self.root/'a.pdf';self.b=self.root/'b.pdf'
        for path,label in [(self.a,'alpha'),(self.b,'beta')]:
            with fitz.open() as doc:
                doc.new_page().insert_text((72,72),label);doc.save(path)
    def test_connected_merge_extract_compress(self):
        ui=connect(FakeUI())
        merged=self.root/'merged.pdf';cut=self.root/'cut.pdf';packed=self.root/'packed.pdf'
        self.assertEqual(ui._run_pdf(merge_pdfs,[self.a,self.b],merged),str(merged.resolve()))
        self.assertEqual(ui._run_pdf(extract_pages,merged,cut,2,2),str(cut.resolve()))
        self.assertEqual(ui._run_pdf(compress_pdf,cut,packed),str(packed.resolve()))
        with fitz.open(packed) as pdf:
            self.assertEqual(len(pdf),1);self.assertIn('beta',pdf[0].get_text())
        self.assertEqual(len(ui.calls),3)
    def test_idempotent_connect(self):
        ui=FakeUI();connect(ui);fn=ui._run_pdf;connect(ui);self.assertIs(ui._run_pdf,fn)
    def test_other_operation_preserved(self):
        ui=connect(FakeUI())
        self.assertEqual(ui._run_pdf(lambda x:x+1,4),5)
    def test_error_does_not_overwrite(self):
        ui=connect(FakeUI());out=self.root/'out.pdf'
        ui._run_pdf(merge_pdfs,[self.a],out);old=out.read_bytes()
        with self.assertRaises(Exception):ui._run_pdf(extract_pages,self.a,out,1,999)
        self.assertEqual(out.read_bytes(),old)
    def test_unknown_dispatch_rejected(self):
        with self.assertRaises(ValueError):dispatch(PDFCommands(),lambda:None,())
    def test_ui_module_importable_without_display(self):
        import openpdf_windows_v297
        self.assertTrue(callable(openpdf_windows_v297.create_app))

if __name__=='__main__':unittest.main()
