"""V51.2 OCR Office GUI routing and symlink safety; not a Windows GUI test.
Author: Abdelhalim Talbi.
"""
import ast
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
import openpdf_operations as operations

class OCRGUIRouteV512(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / 'source.pdf'
        self.source.write_bytes(b'%PDF-1.4\nsynthetic dispatcher fixture\n')
        self.destination = self.root / 'result.docx'

    def run_office(self, **kwargs):
        return operations.run_operation('docx', (str(self.source),), str(self.destination), **kwargs)

    def test_opt_in_routes_to_pipeline_and_audits_success(self):
        receipt = object()
        module = types.ModuleType('openpdf_ocr_office_pipeline_v511')
        seen = []
        def convert(source, destination, **kwargs):
            seen.append((source, destination, kwargs))
            return receipt
        module.convert_scanned_office = convert
        with patch.dict(sys.modules, {'openpdf_ocr_office_pipeline_v511': module}), \
             patch.object(operations, '_legacy_run_operation', side_effect=AssertionError('legacy path')), \
             patch.object(operations, 'write_event') as audit:
            self.assertIs(self.run_office(ocr_before_office=True, language='eng'), receipt)
        self.assertEqual(seen, [(self.source, self.destination, {'language': 'eng'})])
        self.assertEqual(audit.call_args.args[:2], ('docx', 'success'))

    def test_explicitly_disabled_stays_legacy(self):
        with patch.object(operations, '_legacy_run_operation', return_value='legacy') as legacy, \
             patch.object(operations, 'write_event'):
            self.assertEqual(self.run_office(ocr_before_office=False), 'legacy')
        legacy.assert_called_once()

    def test_default_stays_legacy(self):
        with patch.object(operations, '_legacy_run_operation', return_value='legacy'), \
             patch.object(operations, 'write_event'):
            self.assertEqual(self.run_office(), 'legacy')

    def test_missing_ocr_engine_fails_without_output(self):
        module = types.ModuleType('openpdf_ocr_office_pipeline_v511')
        def fail(*args, **kwargs):
            raise RuntimeError('missing OCR model')
        module.convert_scanned_office = fail
        with patch.dict(sys.modules, {'openpdf_ocr_office_pipeline_v511': module}), \
             patch.object(operations, 'write_event') as audit:
            with self.assertRaisesRegex(RuntimeError, 'missing OCR model'):
                self.run_office(ocr_before_office=True)
        self.assertFalse(self.destination.exists())
        self.assertEqual(audit.call_args.args[:2], ('docx', 'failure'))

    def test_existing_destination_not_overwritten(self):
        self.destination.write_bytes(b'KEEP')
        with patch.object(operations, 'write_event'):
            with self.assertRaises(FileExistsError):
                self.run_office(ocr_before_office=True)
        self.assertEqual(self.destination.read_bytes(), b'KEEP')

    def test_multiple_sources_refused(self):
        other = self.root / 'other.pdf'
        other.write_bytes(self.source.read_bytes())
        with patch.object(operations, 'write_event'):
            with self.assertRaisesRegex(ValueError, 'un seul PDF'):
                operations.run_operation('docx', (str(self.source), str(other)), str(self.destination), ocr_before_office=True)

    def test_source_symlink_rejected(self):
        link = self.root / 'link.pdf'
        try: link.symlink_to(self.source)
        except OSError: self.skipTest('Symlinks unavailable')
        with self.assertRaisesRegex(ValueError, 'lien symbolique'):
            operations.run_operation('docx', (str(link),), str(self.destination), ocr_before_office=True)

    def test_dangling_destination_symlink_rejected(self):
        try: self.destination.symlink_to(self.root / 'missing.docx')
        except OSError: self.skipTest('Symlinks unavailable')
        with self.assertRaises(FileExistsError):
            self.run_office(ocr_before_office=True)
        self.assertTrue(self.destination.is_symlink())

    def test_non_office_operations_keep_legacy(self):
        with patch.object(operations, '_legacy_run_operation', return_value='other') as legacy, \
             patch.object(operations, 'write_event'):
            self.assertEqual(operations.run_operation('ocr', (str(self.source),), str(self.destination), ocr_before_office=True), 'other')
        legacy.assert_called_once()

    def test_gui_checkbox_contract(self):
        source = (ROOT / '03-Sources/openpdf_desktop.py').read_text(encoding='utf-8')
        ast.parse(source)
        self.assertIn('self.ocr_before_office=tk.BooleanVar(value=False)', source)
        for ext in ('docx', 'xlsx', 'pptx'):
            self.assertIn("'"+ext+"':('Langue OCR','OCR avant conversion')", source)
        self.assertIn('ocr_before_office=self.ocr_before_office.get()', source)
        self.assertIn('self.ocr_office_check,*self.operation_buttons', source)

if __name__ == '__main__':
    unittest.main()
