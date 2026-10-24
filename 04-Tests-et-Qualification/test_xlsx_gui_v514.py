"""V51.4 Excel GUI dispatcher and real PDF conversion regressions.
Author: Abdelhalim Talbi. These tests are not a human Windows GUI qualification.
"""
import ast
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
import openpdf_operations as ops


class XLSXGUIV514(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.src = self.root / 'source.pdf'
        self.src.write_bytes(b'%PDF-1.4\n')
        self.dst = self.root / 'output.xlsx'

    def call(self, **options):
        return ops.run_operation('xlsx', [str(self.src)], str(self.dst), **options)

    def test_opt_in_routes_converter_and_audit(self):
        with patch('openpdf_conversion_service_v351.convert_office', return_value='converted') as convert, \
             patch.object(ops, '_legacy_run_operation', side_effect=AssertionError('legacy')), \
             patch.object(ops, 'write_event') as audit:
            self.assertEqual(self.call(table_mode=True), 'converted')
        self.assertEqual(convert.call_args.kwargs, {'output_format': 'xlsx', 'table_mode': True})
        self.assertEqual(audit.call_args.args[:2], ('xlsx', 'success'))

    def test_default_stays_legacy(self):
        with patch.object(ops, '_legacy_run_operation', return_value='legacy') as legacy, \
             patch.object(ops, 'write_event'):
            self.assertEqual(self.call(), 'legacy')
        legacy.assert_called_once()

    def test_explicit_off_stays_legacy(self):
        with patch.object(ops, '_legacy_run_operation', return_value='legacy') as legacy, \
             patch.object(ops, 'write_event'):
            self.assertEqual(self.call(table_mode=False), 'legacy')
        legacy.assert_called_once()

    def test_ocr_combination_refused(self):
        with self.assertRaisesRegex(ValueError, 'incompatibles'):
            self.call(table_mode=True, ocr_before_office=True)
        self.assertFalse(self.dst.exists())

    def test_other_operation_refused(self):
        with self.assertRaisesRegex(ValueError, 'réservé'):
            ops.run_operation('docx', [str(self.src)], str(self.root/'a.docx'), table_mode=True)

    def test_invalid_mode_type_refused(self):
        with self.assertRaisesRegex(ValueError, 'réservé'):
            self.call(table_mode='yes')

    def test_existing_output_preserved(self):
        self.dst.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):
            self.call(table_mode=True)
        self.assertEqual(self.dst.read_bytes(), b'KEEP')

    def test_dangling_symlink_output_refused(self):
        try:
            self.dst.symlink_to(self.root/'missing.xlsx')
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(FileExistsError):
            self.call(table_mode=True)

    def test_multiple_sources_refused(self):
        other = self.root/'other.pdf'
        other.write_bytes(self.src.read_bytes())
        with self.assertRaisesRegex(ValueError, 'un seul PDF'):
            ops.run_operation('xlsx', [str(self.src), str(other)], str(self.dst), table_mode=True)
        self.assertFalse(self.dst.exists())

    def test_gui_contract_opt_in_excel_only(self):
        source = (ROOT/'03-Sources/openpdf_desktop.py').read_text(encoding='utf-8')
        ast.parse(source)
        self.assertIn('self.xlsx_tables=tk.BooleanVar(value=False)', source)
        self.assertIn("'xlsx':('Langue OCR','OCR avant conversion','Tableaux Excel éditables')", source)
        self.assertIn("table_mode=self.xlsx_tables.get() if op=='xlsx' else False", source)
        self.assertIn('self.xlsx_tables_check,*self.operation_buttons', source)

    def test_real_pdf_to_excel_via_dispatcher(self):
        from test_xlsx_tables_v514 import fixture
        from openpyxl import load_workbook
        fixture(self.src)
        result = self.call(table_mode=True)
        self.assertEqual(result.output_format, 'xlsx')
        book = load_workbook(self.dst, read_only=True)
        try:
            self.assertEqual(book.worksheets[1]['A4'].value, 'SAN-A')
            self.assertEqual(book.worksheets[1]['B5'].value, '50 To')
        finally:
            book.close()

    def test_failed_conversion_audited_no_output(self):
        with patch('openpdf_conversion_service_v351.convert_office', side_effect=RuntimeError('bad table')), \
             patch.object(ops, 'write_event') as audit:
            with self.assertRaisesRegex(RuntimeError, 'bad table'):
                self.call(table_mode=True)
        self.assertEqual(audit.call_args.args[:2], ('xlsx', 'failure'))
        self.assertFalse(self.dst.exists())


if __name__ == '__main__':
    unittest.main()
