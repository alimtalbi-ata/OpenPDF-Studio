"""V40.6 output protection and duplicate input contracts. Author: Abdelhalim Talbi."""
import ast
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'03-Sources'/'openpdf_workspace_v349.py').read_text(encoding='utf-8')
UI=(ROOT/'03-Sources'/'openpdf_desktop.py').read_text(encoding='utf-8')
class OutputSafetyTests(unittest.TestCase):
    def test_source_syntax(self):
        ast.parse(SRC);ast.parse(UI)
    def test_existing_output_is_refused(self):
        self.assertIn("dest.exists(): raise FileExistsError",SRC)
    def test_pdf_output_extension(self):
        self.assertIn("dest.suffix.lower() != '.pdf'",SRC)
    def test_duplicate_inputs_normalized(self):
        self.assertIn("normalized.casefold() not in known",UI)
        self.assertIn("known.add(normalized.casefold())",UI)
    def test_actual_validation_with_stubbed_operations(self):
        import sys,types
        sys.path.insert(0,str(ROOT/'03-Sources'))
        module=types.ModuleType('openpdf_ui_controller_v348')
        module.OPERATIONS=('compression','fusion','docx','decoupage')
        previous=sys.modules.get(module.__name__)
        sys.modules[module.__name__]=module
        try:
            from openpdf_workspace_v349 import validate_request
            with tempfile.TemporaryDirectory() as tmp:
                source=Path(tmp)/'source.pdf';source.write_bytes(b'%PDF-test')
                existing=Path(tmp)/'existing.pdf';existing.write_bytes(b'untouched')
                with self.assertRaises(FileExistsError):
                    validate_request('compression',[str(source)],str(existing))
                self.assertEqual(existing.read_bytes(),b'untouched')
                with self.assertRaisesRegex(ValueError,'PDF'):
                    validate_request('compression',[str(source)],str(Path(tmp)/'bad.txt'))
                inputs,output=validate_request('compression',[str(source)],str(Path(tmp)/'new.pdf'))
                self.assertEqual(len(inputs),1)
                self.assertTrue(output.endswith('new.pdf'))
        finally:
            if previous is None:sys.modules.pop(module.__name__,None)
            else:sys.modules[module.__name__]=previous
if __name__=='__main__':unittest.main()
