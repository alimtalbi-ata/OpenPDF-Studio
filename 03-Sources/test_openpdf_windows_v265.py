"""Regression tests for V26.5 unified Windows shell."""
import tempfile
import unittest
from pathlib import Path
import fitz
from openpdf_windows_v265 import describe_document, EmbeddedEditor, OpenPDFStudio

class UnifiedWorkspaceTests(unittest.TestCase):
    def test_document_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'sample.pdf'
            with fitz.open() as doc:
                doc.new_page(width=300, height=420)
                doc.new_page()
                doc.save(path)
            data = describe_document(path)
            self.assertEqual(data['pages'], 2)
            self.assertEqual(data['name'], 'sample.pdf')
            self.assertEqual(data['width'], 300)
            self.assertGreater(data['size_bytes'], 0)
    def test_missing_pdf(self):
        with self.assertRaises(Exception): describe_document('/not/available/file.pdf')
    def test_embedded_editor_type(self):
        from tkinter import ttk
        self.assertTrue(issubclass(EmbeddedEditor, ttk.Frame))
    def test_unified_studio(self):
        self.assertTrue(issubclass(OpenPDFStudio, __import__('tkinter').Tk))

if __name__ == '__main__': unittest.main()
