"""V541 privacy and validation regression tests. Author: Abdelhalim Talbi."""
import ast
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_ocr_quality_ui_v541 import (safe_receipt, format_ocr_quality_summary,
                                         serialize_ocr_quality_receipt)


def example():
    return {'schema': 'openpdf.ocr.reference.report.v1', 'status': 'FAIL',
            'cases': 2, 'pages': 3, 'human_reviewed_cases': 0, 'synthetic_cases': 2,
            'cases_below_quality_floors': 0, 'pages_below_quality_floors': 1,
            'reference_characters': 40, 'reference_words': 8,
            'character_errors': 5, 'word_errors': 2,
            'cer': .125, 'wer': .25, 'worst_case_cer': .2, 'worst_case_wer': .5,
            'worst_page_cer': 1., 'worst_page_wer': 1.,
            'manifest_sha256': 'a'*64, 'evidence_set_sha256': 'b'*64,
            'failed_thresholds': ['page_quality_floors'], 'page_quality_floors_enabled': True,
            'path': 'C:/private/company.pdf', 'text': 'SECRET-CLIENT-DATA'}


class QualityUiV541(unittest.TestCase):
    def test_pass_and_fail_receipts(self):
        result = safe_receipt(example())
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['pages_below_quality_floors'], 1)
        good = example(); good['status'] = 'PASS'; good['failed_thresholds'] = []
        self.assertEqual(safe_receipt(good)['status'], 'PASS')

    def test_unknown_fields_never_leak(self):
        raw = example()
        summary = format_ocr_quality_summary(raw)
        receipt = serialize_ocr_quality_receipt(raw)
        for sensitive in ('SECRET-CLIENT-DATA', 'company.pdf', 'C:/private'):
            self.assertNotIn(sensitive, summary + receipt)
        self.assertEqual(json.loads(receipt)['status'], 'FAIL')

    def test_untrusted_failure_strings_refused(self):
        raw = example(); raw['failed_thresholds'] = ['SECRET-CLIENT-DATA']
        with self.assertRaises(ValueError): safe_receipt(raw)

    def test_nonfinite_and_negative_rates_refused(self):
        for bad in (float('nan'), float('inf'), -0.1, '0.2', True):
            raw = example(); raw['cer'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_receipt(raw)

    def test_bogus_counts_refused(self):
        for bad in (True, -1, 1.2, '3'):
            raw = example(); raw['pages'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_receipt(raw)

    def test_digests_validated(self):
        for bad in ('0'*63, 'Z'*64, None):
            raw = example(); raw['manifest_sha256'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError): safe_receipt(raw)

    def test_old_manifest_receipt_warns_page_gate_disabled(self):
        raw = example(); raw['page_quality_floors_enabled'] = False
        raw['worst_page_cer'] = None; raw['worst_page_wer'] = None
        self.assertIn('désactivés', format_ocr_quality_summary(raw))

    def test_ui_entrypoint_wired_without_launching_tk(self):
        source = (ROOT / '03-Sources/openpdf_desktop.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'OpenPDFStudio')
        self.assertIn('_ocr_quality_dialog', {n.name for n in klass.body if isinstance(n, ast.FunctionDef)})
        self.assertIn('Qualité OCR', source)
        self.assertIn("ttk.Button(header,text='Qualité OCR'", source)
        self.assertIn("ttk.Button(header,text='Audit'", source)
        self.assertIn('openpdf_ocr_reference_corpus_v539', source)
        self.assertIn('openpdf_ocr_quality_ui_v541', source)


if __name__ == '__main__':
    unittest.main()
