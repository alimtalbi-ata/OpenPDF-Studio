"""Régression des interactions UI V29.8."""
import unittest,tempfile
from pathlib import Path
import fitz
from openpdf_ui_bridge_v298 import connect, dispatch, ROUTES
from openpdf_engine_v273 import merge_pdfs, extract_pages, compress_pdf
from openpdf_commands_v296 import PDFCommands

class FakeUI:
    def __init__(self): self.calls=[]
    def _run_pdf(self, op, *args):
        self.calls.append((op,args))
        return op(*args)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.a=self.root/'a.pdf';self.b=self.root/'b.pdf'
        for path,text in ((self.a,'first'),(self.b,'second')):
            with fitz.open() as d:
                d.new_page().insert_text((72,72),text);d.save(path)
    def test_pipeline(self):
        app=connect(FakeUI());m=self.root/'m.pdf';e=self.root/'e.pdf';c=self.root/'c.pdf'
        app._run_pdf(merge_pdfs,[self.a,self.b],m)
        app._run_pdf(extract_pages,m,e,2,2)
        app._run_pdf(compress_pdf,e,c)
        with fitz.open(c) as d: self.assertIn('second',d[0].get_text())
    def test_name_collision_does_not_route(self):
        app=connect(FakeUI())
        def merge_pdfs(a,b): return ('custom',a,b)
        self.assertEqual(app._run_pdf(merge_pdfs,1,2),('custom',1,2))
        self.assertEqual(len(app.calls),1)
        self.assertIs(app.calls[0][0],merge_pdfs)
    def test_unknown_dispatch(self):
        with self.assertRaises(ValueError): dispatch(PDFCommands(),lambda:None,())
    def test_registered_identity(self):
        self.assertEqual(len(ROUTES),3)
        self.assertEqual(ROUTES[compress_pdf],'compress')
    def test_idempotent(self):
        app=connect(FakeUI());old=app._run_pdf;connect(app);self.assertIs(old,app._run_pdf)
    def test_invalid_range_preserves_output(self):
        app=connect(FakeUI());out=self.root/'out.pdf'
        app._run_pdf(merge_pdfs,[self.a],out);before=out.read_bytes()
        with self.assertRaises(Exception):app._run_pdf(extract_pages,self.a,out,1,999)
        self.assertEqual(out.read_bytes(),before)

if __name__=='__main__': unittest.main()
