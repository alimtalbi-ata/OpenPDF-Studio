"""Core PDF page-count publication invariants. Abdelhalim Talbi."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
import fitz
from openpdf_page_service_v345 import _publish,merge,extract,reorder

class PageIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.src=self.root/'source.pdf'
        with fitz.open() as doc:
            for label in ('ONE','TWO','THREE'):
                doc.new_page().insert_text((50,70),label)
            doc.save(self.src)
    def test_reject_page_count_mismatch_without_publishing(self):
        output=self.root/'wrong.pdf'
        def writer(path):
            with fitz.open() as doc:
                doc.new_page()
                doc.save(path)
        with self.assertRaisesRegex(ValueError,'Nombre de pages inattendu'):
            _publish(output,writer,expected_pages=2)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob('.openpdf-pages-*')),[])
    def test_merge_extract_reorder_counts(self):
        merged=self.root/'merged.pdf'
        self.assertEqual(merge([self.src,self.src],merged).page_counts,(6,))
        extracted=self.root/'extracted.pdf'
        self.assertEqual(extract(self.src,extracted,2,3).page_counts,(2,))
        reordered=self.root/'reordered.pdf'
        self.assertEqual(reorder(self.src,reordered,[3,1,3]).page_counts,(3,))
if __name__=='__main__':unittest.main()
