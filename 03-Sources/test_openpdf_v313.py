import tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from openpdf_guided_v313 import prepare_word,suggest_destination,guided_word,launch_common,connect
class GuidedTests(unittest.TestCase):
    def app(self):
        app=Mock();app.busy=False;app._v272_busy=False;app.files=[];return app
    def test_destination(self): self.assertEqual(suggest_destination('a.PDF'),'a.docx')
    def test_empty_destination(self):
        with self.assertRaises(ValueError):suggest_destination('')
    def test_cancel_source(self): self.assertFalse(guided_word(self.app(),ask_source=lambda:'',ask_destination=Mock()))
    def test_cancel_destination(self): self.assertFalse(guided_word(self.app(),ask_source=lambda:'a.pdf',ask_destination=lambda x:''))
    def test_busy(self):
        a=self.app();a.busy=True;ask=Mock();self.assertFalse(guided_word(a,ask_source=ask,ask_destination=ask));ask.assert_not_called()
    def test_prepare_delegates(self):
        a=self.app()
        with patch('openpdf_guided_v313.dispatch_selected',return_value=True) as gate:
            self.assertTrue(prepare_word(a,'a.pdf','a.docx'))
            self.assertEqual(a.files,['a.pdf']);a.operation.set.assert_called_with('PDF vers Word (texte)');a.destination.set.assert_called_with('a.docx');gate.assert_called_once()
    def test_prepare_missing(self):
        a=self.app();self.assertFalse(prepare_word(a,'','out.docx'));a.operation.set.assert_not_called()
    def test_prepare_busy(self):
        a=self.app();a._v272_busy=True;self.assertFalse(prepare_word(a,'a.pdf','out.docx'));a.operation.set.assert_not_called()
    def test_guided_handoff(self):
        a=self.app()
        with patch('openpdf_guided_v313.prepare_word',return_value=True) as prep:
            self.assertTrue(guided_word(a,ask_source=lambda:'in.pdf',ask_destination=lambda p:p))
            self.assertEqual(prep.call_args.args[:3],(a,'in.pdf','in.docx'))
    def test_word_launch(self):
        with patch('openpdf_guided_v313.guided_word',return_value=True) as g:
            a=self.app();self.assertTrue(launch_common(a,'PDF vers Word (texte)'));g.assert_called_once_with(a)
    def test_other_launch(self):
        with patch('openpdf_guided_v313.safe_launch',return_value=True) as fn:
            a=self.app();self.assertTrue(launch_common(a,'merge_async'));fn.assert_called_once()
    def test_connect_headless(self):
        a=Mock(spec=['_v313_connected']);a._v313_connected=False
        with patch('openpdf_guided_v313.connect_previous'):
            self.assertIs(connect(a),a);self.assertIs(connect(a),a)
