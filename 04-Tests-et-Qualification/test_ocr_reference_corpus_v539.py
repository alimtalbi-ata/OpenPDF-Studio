"""V539 real PDF text-layer corpus tests; synthetic reference, not human review.
Author: Abdelhalim Talbi.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_ocr_reference_corpus_v539 import (
    ANNOTATION_SCHEMA, SCHEMA, _page_distance, evaluate_ocr_reference_corpus, main)

class OCRReferenceCorpusV539(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cases = []
        self._make_case('scan-one', 'ALPHA SAN VOLUME 2026')
        self._make_case('scan-two', 'BETA STORAGE BACKUP 2027')
        self.manifest = self.root / 'manifest.json'
        self._save_manifest()

    def _make_case(self, name, text):
        source = self.root / f'{name}-source.pdf'
        output = self.root / f'{name}-ocr.pdf'
        annotation = self.root / f'{name}-annotation.json'
        with fitz.open() as original:
            page = original.new_page(width=500, height=180)
            page.insert_text((40, 90), text, fontsize=18)
            png = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes('png')
        with fitz.open() as scanned:
            page = scanned.new_page(width=500, height=180)
            page.insert_image(page.rect, stream=png)
            scanned.save(source)
        annotation.write_text(json.dumps({
            'schema': ANNOTATION_SCHEMA,
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'origin': 'synthetic_known_at_generation',
            'pages': [{'page': 1, 'text': text}],
        }), encoding='utf-8')
        with fitz.open(source) as result:
            result[0].insert_text((40, 90), text, fontsize=18, render_mode=3)
            result.save(output)
        self.cases.append({'id': name, 'source_pdf': source.name,
                           'ocr_pdf': output.name, 'annotations': annotation.name})

    def _save_manifest(self, **threshold_overrides):
        thresholds = {'max_cer': 0, 'max_wer': 0, 'max_case_cer': 0,
                      'max_case_wer': 0, 'min_human_reviewed': 0}
        thresholds.update(threshold_overrides)
        self.manifest.write_text(json.dumps({'schema': SCHEMA, 'cases': self.cases,
                                             'thresholds': thresholds}), encoding='utf-8')

    def _annotation(self, index):
        path = self.root / self.cases[index]['annotations']
        return path, json.loads(path.read_text(encoding='utf-8'))

    def test_two_real_serialized_pdf_text_layers_pass(self):
        report = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual((report['cases'], report['pages'], report['synthetic_cases']), (2, 2, 2))
        self.assertEqual((report['cer'], report['wer']), (0, 0))
        self.assertEqual(report['human_reviewed_cases'], 0)
        self.assertNotIn('ALPHA', json.dumps(report))
        self.assertNotIn('scan-one', json.dumps(report))

    def test_one_mutated_text_layer_fails_even_when_other_case_is_perfect(self):
        path = self.root / self.cases[0]['ocr_pdf']
        with fitz.open(path) as doc:
            doc[0].insert_text((30, 125), 'UNEXPECTED', render_mode=3)
            temp = self.root / 'changed.pdf'
            doc.save(temp)
        temp.replace(path)
        report = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(report['status'], 'FAIL')
        self.assertGreater(report['cer'], 0)
        self.assertEqual(report['cases_below_quality_floors'], 1)
        self.assertIn('case_quality_floors', report['failed_thresholds'])

    def test_deletion_and_insertion_are_measured(self):
        chars, words, ce, we, work = _page_distance('A B C', 'A C X')
        self.assertEqual((chars, words, ce, we), (5, 3, 2, 2))
        self.assertGreater(work, 0)

    def test_missing_page_reference_rejected(self):
        path, data = self._annotation(0)
        data['pages'][0]['page'] = 2
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing or reordered'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_annotation_cannot_be_rebound_to_other_pdf(self):
        path, data = self._annotation(0)
        data['source_sha256'] = '0' * 64
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unbound'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_no_unsubstantiated_human_review_claim(self):
        self._save_manifest(min_human_reviewed=1)
        report = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('min_human_reviewed', report['failed_thresholds'])

    def test_duplicate_source_pdf_refused(self):
        duplicate = self.root / self.cases[1]['source_pdf']
        original = self.root / self.cases[0]['source_pdf']
        duplicate.write_bytes(original.read_bytes())
        path, data = self._annotation(1)
        data['source_sha256'] = hashlib.sha256(duplicate.read_bytes()).hexdigest()
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate source'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_symlink_refused(self):
        original = self.root / self.cases[0]['annotations']
        linked = self.root / 'annotation-link.json'
        try:
            linked.symlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation not permitted by runner')
        self.cases[0]['annotations'] = linked.name
        self._save_manifest()
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_path_traversal_refused(self):
        self.cases[0]['source_pdf'] = '../outside.pdf'
        self._save_manifest()
        with self.assertRaisesRegex(ValueError, 'traversal'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_duplicate_json_keys_refused(self):
        self.manifest.write_text('{"schema":1,"schema":2}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_work_budget_prevents_expensive_edit_distance(self):
        with self.assertRaisesRegex(ValueError, 'edit-distance budget'):
            _page_distance('A' * 4000, 'B' * 4000)

    def test_empty_reference_refused(self):
        path, data = self._annotation(0)
        data['pages'][0]['text'] = ''
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'no measurable reference'):
            evaluate_ocr_reference_corpus(self.manifest)

    def test_cli_report_created_exclusively(self):
        report = self.root / 'quality.json'
        self.assertEqual(main(['--manifest', str(self.manifest), '--report', str(report)]), 0)
        self.assertTrue(report.is_file())
        self.assertEqual(main(['--manifest', str(self.manifest), '--report', str(report)]), 2)

    def test_tight_threshold_does_not_round_error_to_pass(self):
        path = self.root / self.cases[0]['ocr_pdf']
        with fitz.open(path) as doc:
            doc[0].insert_text((30, 125), 'X', render_mode=3)
            changed = self.root / 'changed.pdf'
            doc.save(changed)
        changed.replace(path)
        self._save_manifest(max_cer=0.01, max_wer=0.01,
                            max_case_cer=1, max_case_wer=1)
        result = evaluate_ocr_reference_corpus(self.manifest)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('max_cer', result['failed_thresholds'])

if __name__ == '__main__':
    unittest.main()
