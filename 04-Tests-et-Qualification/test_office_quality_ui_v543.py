"""V543 Office GUI qualification tests; actual GUI exercised under Xvfb separately.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_office_quality_ui_v543 import (safe_office_receipt,
    format_office_quality_summary, serialize_office_quality_receipt)
from openpdf_office_reference_v542 import evaluate_office_reference_corpus


def report():
    return {'schema': 'openpdf.office.reference.report.v1', 'status': 'PASS',
            'cases': 3, 'human_reviewed_cases': 0, 'synthetic_cases': 3,
            'editable_elements': 9, 'cases_below_recall_floor': 0,
            'cases_below_editable_floor': 0, 'reference_tokens': 12,
            'matched_tokens': 12, 'token_recall': 1.0, 'worst_case_token_recall': 1.0,
            'manifest_sha256': 'a'*64, 'evidence_set_sha256': 'b'*64,
            'thresholds': {'min_token_recall': .9, 'min_case_token_recall': .8,
                           'min_human_reviewed': 0, 'min_editable_elements_per_case': 1},
            'by_format': {fmt: {'cases': 1, 'reference_tokens': 4,
                                'matched_tokens': 4, 'token_recall': 1.0}
                          for fmt in ('docx','xlsx','pptx')},
            'failed_thresholds': [], 'source_path': 'C:/Client/SECRET.pdf',
            'text': 'SENSITIVE-CUSTOMER-DATA'}


class OfficeUiV543Tests(unittest.TestCase):
    def test_valid_report_and_explicit_noncertification(self):
        safe = safe_office_receipt(report())
        self.assertEqual(safe['status'], 'PASS')
        self.assertEqual(safe['by_format']['xlsx']['cases'], 1)
        summary = format_office_quality_summary(report())
        self.assertIn('fidélité visuelle', summary)
        self.assertIn('non attestée', summary)

    def test_sensitive_fields_not_serialized_or_displayed(self):
        combined = serialize_office_quality_receipt(report()) + format_office_quality_summary(report())
        self.assertNotIn('SECRET', combined)
        self.assertNotIn('SENSITIVE', combined)
        self.assertNotIn('C:/', combined)
        self.assertNotIn('source_path', combined)

    def test_untrusted_threshold_failure_refused(self):
        r = report(); r['status'] = 'FAIL'; r['failed_thresholds'] = ['SECRET-PRIVATE']
        with self.assertRaises(ValueError): safe_office_receipt(r)

    def test_nonfinite_boolean_negative_or_overflow_recall_refused(self):
        for bad in (float('nan'), float('inf'), -0.1, 1.01, True, '0.8'):
            r = report(); r['worst_case_token_recall'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_office_receipt(r)

    def test_invalid_counts_and_status_refused(self):
        for bad in (True, -1, 3.1, '3'):
            r = report(); r['cases'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_office_receipt(r)
        r = report(); r['status'] = 'FAIL'
        with self.assertRaises(ValueError): safe_office_receipt(r)

    def test_invalid_hash_and_inconsistent_aggregate_refused(self):
        for bad in ('0'*63, 'Z'*64, None):
            r = report(); r['manifest_sha256'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_office_receipt(r)
        r = report(); r['matched_tokens'] = 11
        with self.assertRaises(ValueError): safe_office_receipt(r)
        r = report(); r['by_format']['xlsx']['matched_tokens'] = 3
        with self.assertRaises(ValueError): safe_office_receipt(r)

    def test_fail_receipt_and_zero_format(self):
        r = report(); r['status'] = 'FAIL'; r['failed_thresholds'] = ['min_case_token_recall']
        r['cases_below_recall_floor'] = 1
        r['by_format']['xlsx'] = {'cases': 0, 'reference_tokens': 0,
                                  'matched_tokens': 0, 'token_recall': None}
        r['cases'] = 2; r['synthetic_cases'] = 2
        r['reference_tokens'] = 8; r['matched_tokens'] = 8
        self.assertEqual(safe_office_receipt(r)['status'], 'FAIL')

    def test_real_synthetic_corpus_reconciles_with_ui(self):
        from test_office_reference_v542 import OfficeReferenceV542Tests
        fixture = OfficeReferenceV542Tests()
        fixture.setUp()
        try:
            for fmt, phrase in [('docx', 'Contrat client Alpha 123'),
                                ('xlsx', 'Budget annuel Beta 456'),
                                ('pptx', 'Plan projet Gamma 789')]:
                fixture.case(fmt, phrase)
            actual = evaluate_office_reference_corpus(fixture.manifest())
            receipt = safe_office_receipt(actual)
            self.assertEqual(receipt['cases'], 3)
            self.assertEqual(receipt['matched_tokens'], 12)
            self.assertEqual(receipt['status'], 'PASS')
        finally:
            fixture.doCleanups()

    def test_gui_source_wired_and_explicitly_disabled_when_busy(self):
        source = (ROOT / '03-Sources/openpdf_desktop.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'OpenPDFStudio')
        self.assertIn('_office_quality_dialog', {n.name for n in klass.body if isinstance(n, ast.FunctionDef)})
        self.assertIn("ttk.Button(header,text='Qualité Office'", source)
        self.assertIn('self.office_quality_button', source)
        self.assertIn('openpdf_office_reference_v542', source)
        self.assertIn('openpdf_office_precision_order_ui_v544', source)


@unittest.skipUnless(os.environ.get('OPENPDF_RUN_GUI_TEST') == '1', 'Explicit GUI qualification not requested')
class OfficeUiV543LiveTests(unittest.TestCase):
    def test_real_tk_dialog_async_result_export_and_no_overwrite(self):
        import tkinter as tk
        from tkinter import ttk
        from openpdf_desktop import OpenPDFStudio
        root = OpenPDFStudio()
        root.withdraw()
        self.addCleanup(lambda: root.destroy() if root.winfo_exists() else None)
        def widgets(widget):
            yield widget
            for child in widget.winfo_children():
                yield from widgets(child)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'receipt.json'
            with mock.patch('openpdf_office_reference_v542.evaluate_office_reference_corpus', return_value=report()), \
                 mock.patch('openpdf_desktop.filedialog.askopenfilename', return_value='synthetic.json'), \
                 mock.patch('openpdf_desktop.filedialog.asksaveasfilename', return_value=str(target)), \
                 mock.patch('openpdf_desktop.messagebox.showinfo'), \
                 mock.patch('openpdf_desktop.messagebox.showerror') as show_error:
                root._office_quality_dialog()
                root.update()
                window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel))
                def button(label):
                    return next(w for w in widgets(window) if isinstance(w, ttk.Button) and w.cget('text') == label)
                button('Manifeste…').invoke()
                button('Analyser').invoke()
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    root.update()
                    if str(button('Exporter le reçu').cget('state')) == 'normal':
                        break
                    time.sleep(.04)
                self.assertEqual(str(button('Exporter le reçu').cget('state')), 'normal')
                summary = '\n'.join(w.get('1.0', 'end') for w in widgets(window) if isinstance(w, tk.Text))
                self.assertIn('PASS', summary)
                self.assertNotIn('SECRET', summary)
                button('Exporter le reçu').invoke()
                self.assertEqual(json.loads(target.read_text())['status'], 'PASS')
                button('Exporter le reçu').invoke()
                show_error.assert_called_once()
                self.assertEqual(json.loads(target.read_text())['status'], 'PASS')
                window.destroy()


if __name__ == '__main__':
    unittest.main()
