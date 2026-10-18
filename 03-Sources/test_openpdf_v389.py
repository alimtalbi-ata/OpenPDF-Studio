import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os, sys
import openpdf_studio

class SmokeOutputTests(unittest.TestCase):
    def test_marker_written_to_file(self):
        with TemporaryDirectory() as td:
            output = Path(td)/'marker.txt'
            with patch.dict(os.environ, {'OPENPDF_SMOKE_OUTPUT':str(output)}), patch.object(sys,'argv',['app','--self-test']):
                oldout,olderr=sys.stdout,sys.stderr
                try:
                    self.assertEqual(openpdf_studio.main(),0)
                finally:
                    sys.stdout.flush();sys.stdout.close();sys.stdout,sys.stderr=oldout,olderr
            self.assertIn('OPENPDF_SELF_TEST_OK',output.read_text())
    def test_build_paths(self):
        root=Path(__file__).resolve().parent.parent
        cmd=(root/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertIn('01-Application\\binary',cmd)
        self.assertIn('OpenPDF-Studio-V38.9-Setup.exe',cmd)
        self.assertIn('OpenPDF-Studio-Portable-V38.9.exe',cmd)
    def test_no_fake_executables(self):
        root=Path(__file__).resolve().parent.parent
        self.assertFalse(list((root/'01-Application'/'binary').glob('*.exe')))
