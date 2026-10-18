import ast
import unittest
from pathlib import Path
from openpdf_architecture_audit import audit
ROOT=Path(__file__).parent
class TestCanonicalArchitecture(unittest.TestCase):
    def test_canonical_entrypoint(self):
        tree=ast.parse((ROOT/'openpdf_studio.py').read_text())
        self.assertTrue(any(isinstance(n,ast.ImportFrom) and n.module=='openpdf_desktop' for n in ast.walk(tree)))
    def test_desktop_no_versioned_ui_imports(self):
        tree=ast.parse((ROOT/'openpdf_desktop.py').read_text())
        names=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any((n or '').startswith('openpdf_windows_v') for n in names))
    def test_desktop_has_real_ui(self):
        tree=ast.parse((ROOT/'openpdf_desktop.py').read_text())
        self.assertTrue(any(isinstance(n,ast.ClassDef) and n.name=='OpenPDFStudio' for n in ast.walk(tree)))
    def test_audit_reaches_desktop(self):
        self.assertIn('openpdf_desktop',audit(ROOT)['reachable_static'])
    def test_audit_warning(self):
        self.assertIn('not proof',audit(ROOT)['caution'])
if __name__=='__main__': unittest.main()
