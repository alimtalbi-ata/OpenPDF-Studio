import tempfile,unittest
from pathlib import Path
import fitz
from openpdf_engine_v273 import merge_pdfs,extract_pages,compress_pdf,PDFOperationError
from openpdf_tasks_v273 import TaskRunner
class V273Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'a.pdf'
        with fitz.open() as d:
            for _ in range(3):d.new_page()
            d.save(self.source)
    def test_merge_progress(self):
        p=[];out=self.root/'m.pdf';merge_pdfs([self.source,self.source],out,progress=p.append)
        with fitz.open(out) as d:self.assertEqual(len(d),6)
        self.assertEqual(p[-1],1.0)
    def test_extract_progress(self):
        p=[];out=self.root/'e.pdf';extract_pages(self.source,out,2,3,progress=p.append)
        with fitz.open(out) as d:self.assertEqual(len(d),2)
        self.assertEqual(p[-1],1.0)
    def test_cancel_preserves_target(self):
        out=self.root/'out.pdf';out.write_bytes(b'original')
        with self.assertRaises(PDFOperationError):merge_pdfs([self.source],out,cancelled=lambda:True)
        self.assertEqual(out.read_bytes(),b'original')
    def test_compress(self):
        p=[];out=self.root/'c.pdf';compress_pdf(self.source,out,progress=p.append)
        self.assertEqual(p[-1],1.0)
        with fitz.open(out) as d:self.assertEqual(len(d),3)
    def test_task_cancel(self):
        runner=TaskRunner();self.addCleanup(runner.shutdown)
        handle=runner.submit(merge_pdfs,[self.source],self.root/'z.pdf')
        self.assertIsNotNone(handle.future.result(timeout=10))
        self.assertGreaterEqual(handle.progress,0)
if __name__=='__main__':unittest.main()
