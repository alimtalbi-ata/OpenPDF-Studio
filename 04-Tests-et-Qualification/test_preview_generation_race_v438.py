"""Regression: rapid preview navigation must not strand latest request. Abdelhalim Talbi."""
import sys,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import OpenPDFStudio

class PreviewRaceTests(unittest.TestCase):
    def test_same_page_new_generation_starts_worker(self):
        ui=object.__new__(OpenPDFStudio)
        ui._preview_generation=2;ui._preview_pending={(('input.pdf',0),1)}
        ui._preview_after_id=None;ui.events=MagicMock()
        with patch('openpdf_desktop.threading.Thread') as worker:
            OpenPDFStudio._dispatch_preview(ui,'input.pdf',0,2)
        worker.assert_called_once()
        self.assertIn((('input.pdf',0),2),ui._preview_pending)
    def test_old_generation_is_ignored(self):
        ui=object.__new__(OpenPDFStudio)
        ui._preview_generation=2;ui._preview_pending=set();ui._preview_after_id=None
        with patch('openpdf_desktop.threading.Thread') as worker:
            OpenPDFStudio._dispatch_preview(ui,'input.pdf',0,1)
        worker.assert_not_called()
if __name__=='__main__':unittest.main()
