"""Extraction page selection must use only a matching loaded preview. Abdelhalim Talbi."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import preview_page_for_source

class PreviewSelectionTests(unittest.TestCase):
    def test_valid_first(self):self.assertEqual(preview_page_for_source('a','a',0,8),1)
    def test_valid_last(self):self.assertEqual(preview_page_for_source('a','a',7,8),8)
    def test_other_document(self):self.assertIsNone(preview_page_for_source('a','b',2,8))
    def test_unloaded(self):self.assertIsNone(preview_page_for_source('a','a',0,0))
    def test_out_of_range(self):self.assertIsNone(preview_page_for_source('a','a',9,8))
    def test_no_selection(self):self.assertIsNone(preview_page_for_source(None,'a',0,8))
if __name__=='__main__':unittest.main()
