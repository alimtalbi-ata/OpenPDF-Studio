"""Static UI wiring regression for audit controls. Abdelhalim Talbi."""
import ast
import unittest
from pathlib import Path
class AuditUITests(unittest.TestCase):
    def test_audit_dialog_and_controls_present(self):
        source=(Path(__file__).resolve().parents[1]/'03-Sources'/'openpdf_desktop.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        app=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='OpenPDFStudio')
        methods={n.name for n in app.body if isinstance(n,ast.FunctionDef)}
        self.assertIn('_audit_dialog',methods)
        self.assertIn('export_snapshot',source)
        self.assertIn('verify_snapshot',source)
        self.assertIn('self.audit_button',source)
        self.assertIn('OPENPDF_AUDIT',source)
if __name__=='__main__':unittest.main()
