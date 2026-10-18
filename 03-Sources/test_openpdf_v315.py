import unittest,tempfile
from pathlib import Path
from unittest.mock import Mock,patch
from openpdf_guided_v315 import move_item,validate_merge,guided_merge,connect
class GuidedMergeTests(unittest.TestCase):
    def test_move_up(self):self.assertEqual(move_item(['a','b','c'],1,-1),(['b','a','c'],0))
    def test_move_down(self):self.assertEqual(move_item(['a','b','c'],0,1),(['b','a','c'],1))
    def test_boundary(self):self.assertEqual(move_item(['a','b'],0,-1),(['a','b'],0))
    def test_invalid_direction(self):self.assertEqual(move_item(['a','b'],0,9),(['a','b'],0))
    def test_validation(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';a.write_bytes(b'%PDF');b.write_bytes(b'%PDF')
            self.assertEqual(len(validate_merge([a,b],Path(d)/'out.pdf')[0]),2)
            for paths,target in [([a,a],Path(d)/'out.pdf'),([a,b],a),([a,b],Path(d)/'out.docx')]:
                with self.assertRaises(ValueError):validate_merge(paths,target)
    def test_guided_success(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.pdf';b=Path(d)/'b.pdf';a.write_bytes(b'%PDF');b.write_bytes(b'%PDF')
            app=Mock(spec=['busy','_v272_busy','_run_pdf']);app.busy=False;app._v272_busy=False
            self.assertTrue(guided_merge(app,ask_sources=lambda:[a,b],ask_destination=lambda x:str(Path(d)/x),warn=Mock()))
            app._run_pdf.assert_called_once()
    def test_cancel(self):
        app=Mock(spec=['busy','_v272_busy','_run_pdf']);app.busy=False;app._v272_busy=False
        self.assertFalse(guided_merge(app,ask_sources=lambda:[],ask_destination=lambda x:x));app._run_pdf.assert_not_called()
    def test_busy(self):
        app=Mock(spec=['busy','_v272_busy','_run_pdf']);app.busy=True;app._v272_busy=False
        self.assertFalse(guided_merge(app,ask_sources=lambda:[],ask_destination=lambda x:x))
    def test_connect_idempotent(self):
        app=Mock(spec=['_v315_connected']);app._v315_connected=False
        with patch('openpdf_guided_v315.connect_previous'):
            self.assertIs(connect(app),app);self.assertIs(connect(app),app)
