import unittest
from unittest.mock import Mock, patch
from openpdf_workspace_v304 import available_actions, dispatch, connect

class TestWorkspace(unittest.TestCase):
    def test_all_seven_actions_present(self):
        items=available_actions()
        self.assertEqual(len(items),7)
        self.assertEqual(len({target for _,_,target,_ in items}),7)
    def test_grouping(self):
        items=available_actions()
        self.assertEqual(sum(group=='Organiser les PDF' for group,*_ in items),3)
        self.assertEqual(sum(group=='Convertir et exporter' for group,*_ in items),4)
    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError):dispatch(Mock(),'malicious')
    def test_known_action_dispatch(self):
        app=Mock(busy=False,_v272_busy=False)
        self.assertTrue(dispatch(app,'merge_async'))
        app.merge_async.assert_called_once()
    def test_busy_blocks_dispatch(self):
        app=Mock(busy=True,_v272_busy=False)
        self.assertFalse(dispatch(app,'merge_async'))
        app.merge_async.assert_not_called()
    def test_entrypoint_is_subclass(self):
        from openpdf_windows_v304 import OpenPDFStudio, ApplicationCore, create_app
        self.assertTrue(issubclass(OpenPDFStudio,ApplicationCore))
        self.assertTrue(callable(create_app))
