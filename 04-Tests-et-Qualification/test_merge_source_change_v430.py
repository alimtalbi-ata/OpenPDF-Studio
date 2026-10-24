"""Merge source mutation safety regression. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
import openpdf_page_service_v345 as service

class MergeSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.a=self.root/'a.pdf';self.b=self.root/'b.pdf';self.dest=self.root/'merged.pdf'
        for path in (self.a,self.b):
            with fitz.open() as doc:
                doc.new_page()
                doc.save(path)
    def test_normal_merge(self):
        result=service.merge([self.a,self.b],self.dest)
        self.assertEqual(result.page_counts,(2,))
    def test_mutation_before_publish_rejected(self):
        original=service._publish
        def mutation(destination,writer,expected_pages=None,pre_publish=None):
            def changed_writer(tmp):
                writer(tmp)
                with open(self.a,'ab') as stream:stream.write(b'\n% changed')
            return original(destination,changed_writer,expected_pages=expected_pages,pre_publish=pre_publish)
        with patch.object(service,'_publish',side_effect=mutation):
            with self.assertRaisesRegex(RuntimeError,'Source modifiée'):
                service.merge([self.a,self.b],self.dest)
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.root.glob('.openpdf-pages-*')))
if __name__=='__main__':unittest.main()
