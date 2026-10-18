"""V31.0 regression tests for legacy button routing."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from openpdf_ui_bridge_v310 import dispatch_selected

class LegacyButtonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pdf = self.root / 'source.pdf'
        self.pdf.write_bytes(b'%PDF-1.4\n')
        self.app = Mock()
        self.app.busy = False
        self.app._v272_busy = False
        self.app.files = [str(self.pdf)]
        self.app.operation.get.return_value = 'PDF vers Word (texte)'
        self.app.destination.get.return_value = str(self.root / 'output.docx')
        self.warn = Mock()

    def dispatch(self, **kw):
        return dispatch_selected(self.app, warn=self.warn, confirm_replace=kw.get('confirm', lambda path: True))

    def test_word_routes_controller(self):
        self.assertTrue(self.dispatch())
        self.app._run_pdf.assert_called_once()
        self.assertEqual(self.app._run_pdf.call_args.args[1:], (str(self.pdf), str(self.root/'output.docx')))

    def test_excel_routes(self):
        self.app.operation.get.return_value = 'PDF vers Excel (lignes)'
        self.app.destination.get.return_value = str(self.root/'out.xlsx')
        self.assertTrue(self.dispatch())

    def test_powerpoint_routes(self):
        self.app.operation.get.return_value = 'PDF vers PowerPoint (texte)'
        self.app.destination.get.return_value = str(self.root/'out.pptx')
        self.assertTrue(self.dispatch())

    def test_text_routes(self):
        self.app.operation.get.return_value = 'Extraire le texte'
        self.app.destination.get.return_value = str(self.root/'out.txt')
        self.assertTrue(self.dispatch())

    def test_other_actions_delegate(self):
        self.app.operation.get.return_value = 'Fusionner des PDF'
        self.assertIsNone(self.dispatch())
        self.app._run_pdf.assert_not_called()

    def test_wrong_extension_blocked(self):
        self.app.destination.get.return_value = str(self.root/'out.pdf')
        self.assertFalse(self.dispatch())
        self.app._run_pdf.assert_not_called()

    def test_missing_source_blocked(self):
        self.app.files = [str(self.root/'missing.pdf')]
        self.assertFalse(self.dispatch())

    def test_multiple_sources_blocked(self):
        self.app.files = [str(self.pdf),str(self.pdf)]
        self.assertFalse(self.dispatch())

    def test_overwrite_decline(self):
        (self.root/'output.docx').write_text('untouched')
        self.assertFalse(self.dispatch(confirm=lambda _: False))
        self.app._run_pdf.assert_not_called()

    def test_busy_blocked(self):
        self.app.busy = True
        self.assertFalse(self.dispatch())

    def test_missing_parent_blocked(self):
        self.app.destination.get.return_value = str(self.root/'absent'/'out.docx')
        self.assertFalse(self.dispatch())

if __name__ == '__main__': unittest.main()
