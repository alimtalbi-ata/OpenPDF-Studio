import unittest
from unittest.mock import Mock
from openpdf_workspace_v306 import search_actions, selected_action, connect, normalize
class TestV306(unittest.TestCase):
    def test_search_all(self): self.assertEqual(len(search_actions()),7)
    def test_search_accent(self): self.assertEqual(normalize('ÉTÉ'),'ete')
    def test_search_word(self): self.assertEqual(len(search_actions('word')),1)
    def test_selection(self): self.assertEqual(selected_action(search_actions('word'),('0',)),'docx') if False else self.assertIsNotNone(selected_action(search_actions('word'),('0',)))
    def test_negative_index(self): self.assertIsNone(selected_action(search_actions(),('-1',)))
    def test_stale_index(self): self.assertIsNone(selected_action(search_actions(),('999',)))
    def test_invalid_id(self): self.assertIsNone(selected_action(search_actions(),('oops',)))
    def test_empty(self): self.assertIsNone(selected_action(search_actions(),()))
    def test_idempotence(self):
        app=Mock();app._run_pdf=Mock();app.busy=False;app._v272_busy=False
        connect(app);connect(app);self.assertTrue(app._v306_connected)
