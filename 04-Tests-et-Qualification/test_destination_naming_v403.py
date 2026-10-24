"""Destination naming regression tests. Author: Abdelhalim Talbi.

Extract the pure helper without starting Tkinter or importing PDF dependencies.
"""
import ast
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / '03-Sources/openpdf_desktop.py').read_text(encoding='utf-8')


class DestinationNamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE)
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'suggested_output_name')
        namespace = {'Path': Path}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), '<output-name-helper>', 'exec'), namespace)
        cls.suggest = staticmethod(namespace['suggested_output_name'])

    def test_office_extensions(self):
        self.assertEqual(self.suggest('rapport.pdf', 'docx'), 'rapport.docx')
        self.assertEqual(self.suggest('rapport.pdf', 'xlsx'), 'rapport.xlsx')
        self.assertEqual(self.suggest('rapport.pdf', 'pptx'), 'rapport.pptx')

    def test_pdf_operation_suffixes(self):
        self.assertEqual(self.suggest('rapport.pdf', 'compression'), 'rapport_compresse.pdf')
        self.assertEqual(self.suggest('rapport.pdf', 'fusion'), 'rapport_fusion.pdf')

    def test_empty_source(self):
        self.assertEqual(self.suggest(None, 'ocr'), 'document_ocr.pdf')

    def test_save_dialog_uses_suggestion(self):
        self.assertIn('initialfile=suggested', SOURCE)
        self.assertIn('asksaveasfilename', SOURCE)


if __name__ == '__main__':
    unittest.main()
