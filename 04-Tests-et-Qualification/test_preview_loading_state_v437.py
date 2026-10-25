"""Prevent extraction boundaries from stale or loading PDF previews. Abdelhalim Talbi."""
import sys,unittest
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import OpenPDFStudio,preview_page_for_source

class StalePreviewTests(unittest.TestCase):
    def test_reset_before_async_render(self):
        ui=object.__new__(OpenPDFStudio)
        ui._preview_loaded_source='old.pdf';ui.preview_total=12;ui.preview_page=4
        ui.preview=MagicMock();ui.files=MagicMock();ui.files.curselection.return_value=()
        ui.page_label=MagicMock()
        OpenPDFStudio._preview(ui)
        self.assertIsNone(ui._preview_loaded_source)
        self.assertEqual(ui.preview_total,0)
    def test_page_rejected_during_load(self):
        self.assertIsNone(preview_page_for_source('a.pdf',None,0,0))
    def test_loaded_page_accepted(self):
        self.assertEqual(preview_page_for_source('a.pdf','a.pdf',2,5),3)
if __name__=='__main__':unittest.main()
