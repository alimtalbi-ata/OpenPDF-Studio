import unittest
from unittest.mock import Mock, patch
from openpdf_guided_v314 import launch_guided,task_description,connect
class GuidedCommonTests(unittest.TestCase):
    def test_all_descriptions(self):
        for op in ('merge_async','compress_async','extract_async','PDF vers Word (texte)'):
            self.assertIn('1.',task_description(op))
    def test_unknown_description(self):
        with self.assertRaises(ValueError):task_description('invalid')
    def test_common_routes(self):
        for op in ('merge_async','compress_async','extract_async'):
            a=Mock();a.busy=False;a._v272_busy=False
            self.assertTrue(launch_guided(a,op));getattr(a,op).assert_called_once()
    def test_busy_blocks(self):
        a=Mock();a.busy=True;a._v272_busy=False
        self.assertFalse(launch_guided(a,'merge_async'));a.merge_async.assert_not_called()
    def test_worker_busy_blocks(self):
        a=Mock();a.busy=False;a._v272_busy=True
        self.assertFalse(launch_guided(a,'compress_async'));a.compress_async.assert_not_called()
    def test_invalid_action(self):
        a=Mock();a.busy=False;a._v272_busy=False
        self.assertFalse(launch_guided(a,'no-such-action'))
    def test_word(self):
        a=Mock();a.busy=False;a._v272_busy=False
        with patch('openpdf_guided_v314.guided_word',return_value=True) as fn:
            self.assertTrue(launch_guided(a,'PDF vers Word (texte)'));fn.assert_called_once_with(a)
    def test_missing_handler(self):
        a=Mock(spec=['busy','_v272_busy']);a.busy=False;a._v272_busy=False
        self.assertFalse(launch_guided(a,'merge_async'))
    def test_headless_connect_idempotent(self):
        a=Mock(spec=['_v314_connected']);a._v314_connected=False
        with patch('openpdf_guided_v314.connect_previous'):
            self.assertIs(connect(a),a);self.assertIs(connect(a),a)
