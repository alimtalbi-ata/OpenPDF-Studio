"""Source mutation guards on extraction and reordering. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
import openpdf_page_service_v345 as service

class PageSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.src=self.root/'source.pdf';self.dest=self.root/'result.pdf'
        with fitz.open() as doc:
            doc.new_page();doc.new_page();doc.save(self.src)
    def _mutate_during_write(self,action):
        original=service._publish
        def wrapped(destination,writer,expected_pages=None,pre_publish=None):
            def changed(tmp):
                writer(tmp)
                with open(self.src,'ab') as stream:stream.write(b'\n% external edit')
            return original(destination,changed,expected_pages=expected_pages,pre_publish=pre_publish)
        with patch.object(service,'_publish',side_effect=wrapped):
            with self.assertRaisesRegex(RuntimeError,'Source modifiée'):
                action()
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.root.glob('.openpdf-pages-*')))
    def test_extract_stable(self):
        self.assertEqual(service.extract(self.src,self.dest,1,2).page_counts,(2,))
    def test_reorder_stable(self):
        self.assertEqual(service.reorder(self.src,self.dest,[2,1]).page_counts,(2,))
    def test_extract_modified(self):
        self._mutate_during_write(lambda:service.extract(self.src,self.dest,1,1))
    def test_reorder_modified(self):
        self._mutate_during_write(lambda:service.reorder(self.src,self.dest,[2,1]))
if __name__=='__main__':unittest.main()
