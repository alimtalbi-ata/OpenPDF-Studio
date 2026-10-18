import unittest
from unittest.mock import Mock, patch
from openpdf_essentials_v311 import ESSENTIALS, describe, launch, connect

class EssentialsTests(unittest.TestCase):
    def test_four_priorities(self):
        self.assertEqual([x[0] for x in ESSENTIALS], ['Fusionner', 'Compresser', 'Découper', 'Vers Word'])
    def test_unique_targets(self):
        self.assertEqual(len({x[2] for x in ESSENTIALS}), 4)
    def test_descriptions(self):
        for _, description, target in ESSENTIALS:
            self.assertEqual(describe(target), description)
    def test_unknown_description(self):
        with self.assertRaises(KeyError): describe('unknown')
    def test_unknown_action(self):
        self.assertFalse(launch(Mock(), 'unknown'))
    def test_existing_dispatch(self):
        with patch('openpdf_essentials_v311.activate', return_value=True) as dispatch:
            app=Mock()
            self.assertTrue(launch(app, 'merge_async'))
            dispatch.assert_called_once_with(app, 'merge_async')
    def test_busy_action(self):
        app=Mock(busy=True, _v272_busy=False)
        self.assertFalse(launch(app, 'compress_async'))
    def test_connect_idempotent_non_tk(self):
        app=Mock(spec=['_v311_connected'])
        app._v311_connected=False
        with patch('openpdf_essentials_v311.connect_previous'):
            self.assertIs(connect(app),app)
            self.assertTrue(app._v311_connected)
            self.assertIs(connect(app),app)

if __name__=='__main__': unittest.main()
