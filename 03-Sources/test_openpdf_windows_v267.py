"""Static checks for the V26.7 Windows entry point and packaging."""
import unittest
from pathlib import Path
from openpdf_windows_v267 import OpenPDFStudio

ROOT = Path(__file__).resolve().parent
class WindowsV267Tests(unittest.TestCase):
    def test_studio_class(self):
        self.assertTrue(callable(OpenPDFStudio._create_quick_toolbar))
    def test_async_metadata(self):
        self.assertTrue(callable(OpenPDFStudio._deliver_properties))
    def test_windows_launcher(self):
        self.assertIn('openpdf_windows_v267.py', (ROOT/'LANCER-OPENPDF-STUDIO.cmd').read_text())
    def test_exe_build_entry(self):
        self.assertIn('openpdf_windows_v267.py', (ROOT/'BUILD-WINDOWS-EXE.cmd').read_text())
    def test_no_embedded_exe_claim(self):
        self.assertFalse((ROOT/'dist'/'OpenPDF-Studio'/'OpenPDF-Studio.exe').exists())
