"""V30.2 navigation and integration regression tests."""
import unittest
from unittest.mock import Mock
from openpdf_ui_bridge_v302 import ACTIONS, activate, connect
class TestQuickActions(unittest.TestCase):
    def test_unique_actions(self):
        self.assertEqual(len(ACTIONS),len(set(a[0] for a in ACTIONS)))
        self.assertEqual(len(ACTIONS),len(set(a[2] for a in ACTIONS)))
    def test_busy_refuses(self):
        app=Mock(busy=True,_v272_busy=False)
        self.assertFalse(activate(app,'merge_async'))
        app.merge_async.assert_not_called()
    def test_legacy_busy_refuses(self):
        app=Mock(busy=False,_v272_busy=True)
        self.assertFalse(activate(app,'compress_async'))
    def test_pdf_actions(self):
        for target in ('merge_async','extract_async','compress_async'):
            app=Mock(busy=False,_v272_busy=False)
            self.assertTrue(activate(app,target))
            getattr(app,target).assert_called_once_with()
    def test_conversion_actions(self):
        for target in ('PDF vers Word (texte)','PDF vers Excel (lignes)','PDF vers PowerPoint (texte)','Extraire le texte'):
            app=Mock(busy=False,_v272_busy=False)
            self.assertTrue(activate(app,target))
            app.operation.set.assert_called_once_with(target)
            app._refresh.assert_called_once_with()
    def test_connect_idempotent(self):
        app=Mock();app._v300_connected=False;app._v301_connected=False;app._v302_connected=False
        self.assertIs(connect(app),app)
        self.assertIs(connect(app),app)
    def test_entrypoint(self):
        from openpdf_windows_v302 import create_app
        self.assertTrue(callable(create_app))
if __name__=='__main__': unittest.main()
