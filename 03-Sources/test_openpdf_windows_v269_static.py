"""Non-graphical release checks, safe for headless CI."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent

class ReleaseTests(unittest.TestCase):
    def test_entrypoint_is_parseable(self):
        ast.parse((ROOT / 'openpdf_windows_v269.py').read_text(encoding='utf-8'))

    def test_single_explorer_adapter(self):
        code = (ROOT / 'openpdf_windows_v269.py').read_text(encoding='utf-8')
        self.assertIn('self.filelist.pack_forget()', code)
        self.assertIn('self.sidebar_files', code)

    def test_installer_sources(self):
        iss = (ROOT / 'OpenPDF-Studio-V26.9.iss').read_text(encoding='utf-8')
        self.assertIn('AppVersion "26.9"', iss)
        self.assertIn('recursesubdirs', iss)

if __name__ == '__main__':
    unittest.main()
