import io
import contextlib
import unittest
from pathlib import Path
from unittest.mock import patch
import openpdf_functional_smoke

class FunctionalSmokeTests(unittest.TestCase):
    def test_real_pdf_roundtrip(self):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(openpdf_functional_smoke.run(),0)
        self.assertIn('OPENPDF_FUNCTIONAL_TEST_OK',stream.getvalue())
    def test_missing_dependency_fails_closed(self):
        real_import=__import__
        def blocked(name,*args,**kwargs):
            if name=='fitz': raise ImportError('missing fitz')
            return real_import(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=blocked):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(openpdf_functional_smoke.run(),1)
    def test_windows_smoke_has_timeout_and_two_checks(self):
        s=(Path(__file__).resolve().parent.parent/'02-Compilation'/'TEST-WINDOWS-BINARIES.ps1').read_text()
        self.assertIn('WaitForExit(90000)',s)
        self.assertIn('--functional-self-test',s)
        self.assertIn('Stop-Process',s)
    def test_entrypoint_exposes_functional_mode(self):
        s=(Path(__file__).resolve().parent/'openpdf_studio.py').read_text()
        self.assertIn("'--functional-self-test'",s)

if __name__=='__main__': unittest.main()
