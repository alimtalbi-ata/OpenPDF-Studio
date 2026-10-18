import unittest
from unittest.mock import Mock
from openpdf_workspace_v305 import search_actions,connect
class TestSearch(unittest.TestCase):
    def test_all(self): self.assertEqual(len(search_actions()),7)
    def test_case(self): self.assertEqual(len(search_actions('WORD')),1)
    def test_accents(self): self.assertEqual(len(search_actions('extraire le texte')),1)
    def test_group(self): self.assertEqual(len(search_actions('organiser')),3)
    def test_multiword(self): self.assertEqual(len(search_actions('PDF WORD')),1)
    def test_no_results(self): self.assertEqual(search_actions('inconnu zzzz'),())
    def test_connect_idempotent_non_gui(self):
        app=Mock()
        app._run_pdf=Mock()
        app.busy=False
        app._v272_busy=False
        connect(app);connect(app)
        self.assertTrue(app._v305_connected)
    def test_entrypoint(self):
        from openpdf_windows_v305 import OpenPDFStudio,ApplicationCore
        self.assertTrue(issubclass(OpenPDFStudio,ApplicationCore))
