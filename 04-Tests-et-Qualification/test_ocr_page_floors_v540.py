"""V540 independent PDF text-layer page floors, regression/security tests.
Synthetic PDFs only. Author: Abdelhalim Talbi.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_ocr_reference_corpus_v539 import (  # noqa: E402
    ANNOTATION_SCHEMA, SCHEMA, evaluate_ocr_reference_corpus, main)


class OCRPageFloorsV540(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cases = []
        self._case('first', ['A LONG FIRST PAGE OF INDEPENDENT TEXT', 'SHORT SECOND PAGE'],
                   [True, False])
        self._case('second', ['A SECOND PERFECT OCR PAGE'], [True])
        self.manifest = self.root / 'manifest.json'
        self.thresholds = {'max_cer': .75, 'max_wer': .75,
                           'max_case_cer': .75, 'max_case_wer': .75,
                           'min_human_reviewed': 0}
        self._save()

    def _case(self, label, references, recognized):
        source = self.root / (label + '-scan.pdf')
        output = self.root / (label + '-ocr.pdf')
        annotation = self.root / (label + '-reference.json')
        with fitz.open() as original:
            for ref in references:
                page = original.new_page(width=560, height=200)
                page.insert_text((30, 90), ref, fontsize=16)
            with fitz.open() as scan:
                for index in range(len(references)):
                    image = original[index].get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).tobytes('png')
                    page = scan.new_page(width=560, height=200)
                    page.insert_image(page.rect, stream=image)
                scan.save(source)
        with fitz.open(source) as doc:
            for index, should_recognize in enumerate(recognized):
                if should_recognize:
                    doc[index].insert_text((30, 90), references[index], fontsize=16, render_mode=3)
            doc.save(output)
        annotation.write_text(json.dumps({
            'schema': ANNOTATION_SCHEMA,
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'origin': 'synthetic_known_at_generation',
            'pages': [{'page': i + 1, 'text': ref} for i, ref in enumerate(references)],
        }), encoding='utf-8')
        self.cases.append({'id': label, 'source_pdf': source.name,
                           'ocr_pdf': output.name, 'annotations': annotation.name})

    def _save(self):
        self.manifest.write_text(json.dumps({'schema': SCHEMA, 'cases': self.cases,
                                             'thresholds': self.thresholds}), encoding='utf-8')

    def test_regression_old_gate_passes_despite_missing_second_page(self):
        result = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['page_quality_floors_enabled'])
        self.assertIsNone(result['worst_page_cer'])

    def test_new_gate_detects_missing_page_hidden_by_case_averages(self):
        self.thresholds.update(max_page_cer=.25, max_page_wer=.25)
        self._save()
        result = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['pages_below_quality_floors'], 1)
        self.assertEqual(result['cases_below_quality_floors'], 0)
        self.assertEqual(result['worst_page_cer'], 1)
        self.assertEqual(result['worst_page_wer'], 1)
        self.assertEqual(result['failed_thresholds'], ['page_quality_floors'])
        self.assertNotIn('SHORT SECOND PAGE', json.dumps(result))
        self.assertNotIn('first-scan.pdf', json.dumps(result))

    def test_exact_page_threshold_boundary_passes(self):
        self.thresholds.update(max_page_cer=1, max_page_wer=1)
        self._save()
        self.assertEqual(evaluate_ocr_reference_corpus(self.manifest)['status'], 'PASS')

    def test_cli_returns_three_and_writes_failure_receipt_without_overwriting(self):
        self.thresholds.update(max_page_cer=0, max_page_wer=0)
        self._save()
        report = self.root / 'quality.json'
        self.assertEqual(main(['--manifest', str(self.manifest), '--report', str(report)]), 3)
        self.assertEqual(json.loads(report.read_text())['pages_below_quality_floors'], 1)
        self.assertEqual(main(['--manifest', str(self.manifest), '--report', str(report)]), 2)

    def test_half_page_threshold_manifest_rejected(self):
        self.thresholds['max_page_cer'] = 0.2
        self._save()
        with self.assertRaisesRegex(ValueError, 'Incomplete OCR thresholds'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_unexpected_threshold_rejected(self):
        self.thresholds['max_page_cer'] = 0.2
        self.thresholds['max_page_wer'] = 0.2
        self.thresholds['unexpected'] = 0
        self._save()
        with self.assertRaisesRegex(ValueError, 'Incomplete OCR thresholds'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_boolean_page_threshold_rejected(self):
        self.thresholds.update(max_page_cer=True, max_page_wer=0.1)
        self._save()
        with self.assertRaisesRegex(ValueError, 'Invalid OCR error threshold'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_negative_page_threshold_rejected(self):
        self.thresholds.update(max_page_cer=-.01, max_page_wer=.1)
        self._save()
        with self.assertRaisesRegex(ValueError, 'Invalid OCR error threshold'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_empty_page_reference_is_rejected_when_page_floors_enabled(self):
        self.thresholds.update(max_page_cer=.5, max_page_wer=.5)
        self._save()
        annotation = self.root / self.cases[0]['annotations']
        data = json.loads(annotation.read_text())
        data['pages'][1]['text'] = ''
        annotation.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'nonempty page reference'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_unmodified_source_and_ocr_hashes(self):
        self.thresholds.update(max_page_cer=0, max_page_wer=0)
        self._save()
        paths = [self.root / c[k] for c in self.cases for k in ('source_pdf', 'ocr_pdf')]
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        evaluate_ocr_reference_corpus(self.manifest)
        after = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
