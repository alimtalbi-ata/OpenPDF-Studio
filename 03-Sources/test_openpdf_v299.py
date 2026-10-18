"""V29.9 regressions: asynchronous progress and cancellation are not lost."""
import tempfile, unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import fitz
from openpdf_ui_bridge_v299 import connect
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf, PDFOperationError

class FakeRunnerUI:
    def __init__(self): self.calls=[]
    def _run_pdf(self, op, *args):
        progress=[]
        result=op(*args, progress=progress.append, cancelled=lambda:False)
        self.calls.append(progress)
        return result

class Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.src=self.root/'input.pdf'
        with fitz.open() as d:
            for i in range(3):d.new_page().insert_text((72,72),f'page {i}')
            d.save(self.src)
    def test_progress_propagated(self):
        app=connect(FakeRunnerUI())
        for op,args in [(merge_pdfs,([self.src],self.root/'merged.pdf')),(extract_pages,(self.src,self.root/'extract.pdf',1,2)),(compress_pdf,(self.src,self.root/'compressed.pdf'))]:
            self.assertTrue(Path(app._run_pdf(op,*args)).exists())
            self.assertGreater(len(app.calls[-1]),0)
            self.assertEqual(app.calls[-1][-1],1)
    def test_cancellation_propagated(self):
        app=connect(FakeRunnerUI());out=self.root/'cancel.pdf'
        def cancelled():return True
        def run(op,*args):return op(*args,progress=lambda x:None,cancelled=cancelled)
        app._run_pdf=connect(app)._run_pdf
        # Simulate a task runner that passes an already-cancelled token.
        app2=type('CancelledUI',(),{'_run_pdf':lambda self,op,*args:run(op,*args)})()
        connect(app2)
        with self.assertRaises(PDFOperationError):app2._run_pdf(merge_pdfs,[self.src],out)
        self.assertFalse(out.exists())
    def test_unknown_operation_untouched(self):
        app=connect(FakeRunnerUI())
        def custom(*,progress=None,cancelled=None):return 'custom'
        self.assertEqual(app._run_pdf(custom),'custom')
    def test_idempotent(self):
        app=connect(FakeRunnerUI());fn=app._run_pdf
        self.assertIs(connect(app)._run_pdf,fn)
    def test_import_entry(self):
        from openpdf_windows_v299 import create_app
        self.assertTrue(callable(create_app))
