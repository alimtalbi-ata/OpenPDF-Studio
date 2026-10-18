import unittest
from unittest.mock import Mock
from pathlib import Path
from tempfile import TemporaryDirectory
from openpdf_ui_bridge_v303 import run_conversion, activate, CONVERSIONS
class TestDirectConversion(unittest.TestCase):
    def test_all_routes(self):
        for target, (func, ext) in CONVERSIONS.items():
            app=Mock(busy=False,_v272_busy=False)
            ok=run_conversion(app,target,select_source=lambda:'sample.pdf',select_destination=lambda s,e:'output.'+e,confirm_replace=lambda p:True)
            self.assertTrue(ok)
            app._run_pdf.assert_called_once_with(func,'sample.pdf','output.'+ext)
    def test_cancel_source(self):
        app=Mock(busy=False,_v272_busy=False)
        self.assertFalse(run_conversion(app,'Extraire le texte',select_source=lambda:'',select_destination=lambda s,e:'a.txt',confirm_replace=lambda p:True))
        app._run_pdf.assert_not_called()
    def test_cancel_destination(self):
        app=Mock(busy=False,_v272_busy=False)
        self.assertFalse(run_conversion(app,'Extraire le texte',select_source=lambda:'a.pdf',select_destination=lambda s,e:'',confirm_replace=lambda p:True))
        app._run_pdf.assert_not_called()
    def test_busy(self):
        app=Mock(busy=True,_v272_busy=False)
        self.assertFalse(run_conversion(app,'Extraire le texte',select_source=lambda:'a.pdf',select_destination=lambda s,e:'a.txt',confirm_replace=lambda p:True))
        app._run_pdf.assert_not_called()
    def test_refuse_replace(self):
        with TemporaryDirectory() as folder:
            dest=Path(folder)/'existing.txt';dest.write_text('original')
            app=Mock(busy=False,_v272_busy=False)
            self.assertFalse(run_conversion(app,'Extraire le texte',select_source=lambda:'a.pdf',select_destination=lambda s,e:str(dest),confirm_replace=lambda p:False))
            self.assertEqual(dest.read_text(),'original')
            app._run_pdf.assert_not_called()
    def test_wrong_extension(self):
        app=Mock(busy=False,_v272_busy=False)
        with self.assertRaises(ValueError):run_conversion(app,'Extraire le texte',select_source=lambda:'a.pdf',select_destination=lambda s,e:'a.exe',confirm_replace=lambda p:True)
    def test_unknown_action(self):
        with self.assertRaises(ValueError):activate(Mock(busy=False,_v272_busy=False),'invalid')
    def test_entrypoint(self):
        from openpdf_windows_v303 import create_app
        self.assertTrue(callable(create_app))
