import unittest
from pathlib import Path
from unittest.mock import Mock
from openpdf_windows_v260 import OpenPDFApp

class SidebarTests(unittest.TestCase):
    def test_sync_without_widget(self):
        obj=Mock(spec=[])
        obj.files=[]
        OpenPDFApp._sync_sidebar(obj)
    def test_sidebar_selection_without_selection(self):
        obj=Mock(spec=[])
        obj.sidebar_files=Mock()
        obj.sidebar_files.curselection.return_value=()
        OpenPDFApp._sidebar_select(obj)
        obj.sidebar_files.curselection.assert_called_once()
    def test_launcher_targets_current_version(self):
        self.assertIn('openpdf_windows_v267.py',Path(__file__).with_name('LANCER-OPENPDF-STUDIO.cmd').read_text())
if __name__=='__main__':unittest.main()
