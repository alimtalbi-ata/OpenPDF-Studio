import unittest
from unittest.mock import Mock,patch
from openpdf_essentials_v312 import SHORTCUTS,help_message,safe_launch,connect

class UsabilityTests(unittest.TestCase):
    def test_shortcuts_unique(self):
        self.assertEqual(len(SHORTCUTS),4)
        self.assertEqual(len(set(x[0] for x in SHORTCUTS)),4)
    def test_shortcuts_all_common_actions(self):
        from openpdf_essentials_v311 import ESSENTIALS
        self.assertEqual({x[1] for x in SHORTCUTS},{x[2] for x in ESSENTIALS})
    def test_help(self):
        self.assertIn('Fusionner',help_message('merge_async'))
    def test_unknown_help(self):
        with self.assertRaises(ValueError): help_message('invalid')
    def test_unknown_not_launched(self):
        self.assertFalse(safe_launch(Mock(),'invalid'))
    def test_launch_delegated(self):
        with patch('openpdf_essentials_v312.launch',return_value=True) as fn:
            app=Mock()
            self.assertTrue(safe_launch(app,'merge_async'))
            fn.assert_called_once_with(app,'merge_async')
    def test_connect_idempotent_headless(self):
        app=Mock(spec=['_v312_connected']);app._v312_connected=False
        with patch('openpdf_essentials_v312.connect_previous'):
            self.assertIs(connect(app),app)
            self.assertIs(connect(app),app)
