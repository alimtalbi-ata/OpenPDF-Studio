import unittest
from unittest.mock import patch
from openpdf_ui_controller_v348 import run_operation, OPERATIONS
class UITests(unittest.TestCase):
    def test_registry(self): self.assertTrue({'compression','fusion','extraction','decoupage','reorganisation','ocr'}.issubset(OPERATIONS))
    def test_unknown(self):
        with self.assertRaisesRegex(ValueError,'inconnue'):run_operation('bad',['a.pdf'],'b.pdf')
    def test_no_source(self):
        with self.assertRaisesRegex(ValueError,'au moins'):run_operation('fusion',[],'b.pdf')
    def test_no_destination(self):
        with self.assertRaisesRegex(ValueError,'Destination'):run_operation('fusion',['a.pdf'],'')
    def test_multiple_rejected(self):
        with self.assertRaisesRegex(ValueError,'exactement'):run_operation('ocr',['a.pdf','b.pdf'],'out.pdf')
    @patch('openpdf_ui_controller_v348.merge',return_value='merged')
    def test_merge(self,m):
        self.assertEqual(run_operation('fusion',['a.pdf','b.pdf'],'out.pdf'),'merged');m.assert_called_once()
    @patch('openpdf_ui_controller_v348.extract',return_value='extracted')
    def test_extract(self,m):
        self.assertEqual(run_operation('extraction',['a.pdf'],'out.pdf',first='2',last='4'),'extracted');m.assert_called_once_with('a.pdf','out.pdf',2,4)
    @patch('openpdf_ui_controller_v348.searchable_pdf',return_value='ocr')
    def test_ocr(self,m):
        self.assertEqual(run_operation('ocr',['a.pdf'],'out.pdf',language='eng'),'ocr');m.assert_called_once_with('a.pdf','out.pdf',language='eng')
if __name__=='__main__':unittest.main()
