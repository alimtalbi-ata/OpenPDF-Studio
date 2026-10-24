"""Release documentation and cumulative package contract tests.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from docx import Document
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]

class DocumentationContract(unittest.TestCase):
    def test_version_specific_docs_generation(self):
        import subprocess
        subprocess.run([sys.executable,str(ROOT/'02-Compilation/generate_release_docs.py')],cwd=ROOT,check=True)
        version=(ROOT/'VERSION.txt').read_text(encoding='utf-8').strip()
        docx=ROOT/'05-Documentation'/f'OpenPDF-Studio-V{version}-Guide.docx'
        pdf=ROOT/'05-Documentation'/f'OpenPDF-Studio-V{version}-Guide.pdf'
        self.assertTrue(docx.is_file() and pdf.is_file())
        paragraphs=' '.join(p.text for p in Document(docx).paragraphs)
        self.assertIn('Abdelhalim Talbi',paragraphs)
        self.assertIn('V'+version,paragraphs)
        self.assertGreaterEqual(len(PdfReader(str(pdf)).pages),2)
        self.assertIn('V'+version,PdfReader(str(pdf)).pages[0].extract_text())
    def test_packaging_requires_matching_docs(self):
        script=(ROOT/'02-Compilation/PACKAGE-CUMULATIVE.ps1').read_text(encoding='utf-8')
        self.assertIn('Missing version-specific documentation',script)
        self.assertIn('Missing documentation inside ZIP',script)
        self.assertIn('RELEASE-FILES-SHA256.json',script)
if __name__=='__main__':unittest.main()
