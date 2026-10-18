import unittest
from pathlib import Path
import ast,subprocess,sys
ROOT=Path(__file__).resolve().parent
class ReleaseTests(unittest.TestCase):
    def test_entrypoint_syntax(self):ast.parse((ROOT/'openpdf_studio.py').read_text())
    def test_desktop_syntax(self):ast.parse((ROOT/'openpdf_desktop.py').read_text())
    def test_selftest(self):
        r=subprocess.run([sys.executable,str(ROOT/'openpdf_studio.py'),'--self-test'],capture_output=True,text=True,timeout=20)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('OPENPDF_SELF_TEST_OK',r.stdout)
    def test_build_smoke(self):
        s=(ROOT.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertEqual(s.count('--self-test'),2)
    def test_build_version(self):
        s=(ROOT.parent/'02-Compilation'/'BUILD-WINDOWS-INSTALLER.cmd').read_text()
        self.assertIn('V38.0',s);self.assertIn('OpenPDF-Studio-V38.0.iss',s)
    def test_ui_shortcuts(self):
        s=(ROOT/'openpdf_desktop.py').read_text();self.assertIn('<Control-o>',s);self.assertIn('<Control-Return>',s)
if __name__=='__main__':unittest.main()
