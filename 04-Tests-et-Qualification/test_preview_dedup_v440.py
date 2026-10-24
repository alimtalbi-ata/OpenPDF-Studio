"""Prevent duplicate preview workers while preserving generation isolation."""
import sys,unittest
from pathlib import Path
from unittest.mock import MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import OpenPDFStudio

class PreviewDedupTests(unittest.TestCase):
    def make_ui(self, pending, generation=3):
        ui=object.__new__(OpenPDFStudio)
        ui._preview_generation=generation
        ui._preview_pending=set(pending)
        ui._preview_after_id=None
        ui.events=MagicMock()
        return ui
    def test_duplicate_same_generation_is_suppressed(self):
        ui=self.make_ui({(('sample.pdf',2),3)})
        with patch('openpdf_desktop.threading.Thread') as thread:
            OpenPDFStudio._dispatch_preview(ui,'sample.pdf',2,3)
        thread.assert_not_called()
    def test_old_generation_does_not_suppress_current(self):
        ui=self.make_ui({(('sample.pdf',2),2)})
        with patch('openpdf_desktop.threading.Thread') as thread:
            OpenPDFStudio._dispatch_preview(ui,'sample.pdf',2,3)
        thread.assert_called_once()
    def test_other_page_does_not_suppress_current(self):
        ui=self.make_ui({(('sample.pdf',1),3)})
        with patch('openpdf_desktop.threading.Thread') as thread:
            OpenPDFStudio._dispatch_preview(ui,'sample.pdf',2,3)
        thread.assert_called_once()
if __name__=='__main__':unittest.main()
