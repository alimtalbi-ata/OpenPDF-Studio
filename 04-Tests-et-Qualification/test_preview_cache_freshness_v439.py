"""PDF preview cache must distinguish edited source files. Abdelhalim Talbi."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import preview_cache_key

class PreviewCacheTests(unittest.TestCase):
    def test_stable_source_same_key(self):
        with tempfile.TemporaryDirectory() as root:
            pdf=Path(root)/'doc.pdf';pdf.write_bytes(b'original')
            self.assertEqual(preview_cache_key(pdf,0),preview_cache_key(pdf,0))
    def test_modified_source_new_key(self):
        with tempfile.TemporaryDirectory() as root:
            pdf=Path(root)/'doc.pdf';pdf.write_bytes(b'original')
            old=preview_cache_key(pdf,0)
            pdf.write_bytes(b'modified and longer')
            self.assertNotEqual(old,preview_cache_key(pdf,0))
    def test_different_pages_different_keys(self):
        with tempfile.TemporaryDirectory() as root:
            pdf=Path(root)/'doc.pdf';pdf.write_bytes(b'pdf')
            self.assertNotEqual(preview_cache_key(pdf,0),preview_cache_key(pdf,1))
    def test_missing_source(self):
        self.assertEqual(preview_cache_key('/not/a/real/pdf.pdf',0)[2:],(None,None))
if __name__=='__main__':unittest.main()
