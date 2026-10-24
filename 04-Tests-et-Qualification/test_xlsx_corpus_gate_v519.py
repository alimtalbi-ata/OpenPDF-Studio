"""V519 corpus gate unit and end-to-end tests. Author: Abdelhalim Talbi."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_xlsx_corpus_gate_v519 import SCHEMA, evaluate_corpus, main


class CorpusGateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manifest = self.root / 'corpus.json'
        self.cases = []
        for n in (1, 2):
            names = {key: f'case{n}.{ext}' for key, ext in (
                ('pdf', 'pdf'), ('xlsx', 'xlsx'), ('annotations', 'json'))}
            for value in names.values():
                (self.root / value).write_bytes(f'fixture-{n}'.encode())
            self.cases.append({'id': f'case-{n}', **names})
        self.thresholds = {
            'min_nonempty_cell_accuracy': 0.95,
            'min_table_recall': 1.0,
            'min_merge_recall': 1.0,
            'max_extra_nonempty_cells': 0,
            'min_human_reviewed': 0,
        }
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps({'schema': SCHEMA, 'cases': self.cases,
                                             'thresholds': self.thresholds}), encoding='utf-8')

    def oracle(self, pdf, xlsx, annotation):
        return {
            'schema': 'openpdf.xlsx.ground_truth.report.v1',
            'status': 'PASS', 'annotation_origin': 'synthetic_known_at_generation',
            'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'workbook_sha256': hashlib.sha256(xlsx.read_bytes()).hexdigest(),
            'annotation_sha256': hashlib.sha256(annotation.read_bytes()).hexdigest(),
            'expected_tables': 1, 'observed_tables': 1, 'matched_tables': 1,
            'annotated_cells': 6, 'exact_cells': 6,
            'annotated_nonempty_cells': 6, 'exact_nonempty_cells': 6,
            'extra_nonempty_cells': 0, 'expected_merges': 1,
            'observed_merges': 1, 'matched_merges': 1,
        }

    def test_two_cases_pass_and_report_has_no_source_text(self):
        result = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['cases'], 2)
        self.assertEqual(result['annotated_nonempty_cells'], 12)
        self.assertEqual(result['merge_recall'], 1)
        self.assertNotIn('case-1', json.dumps(result))
        self.assertNotIn('fixture-1', json.dumps(result))

    def test_micro_average_not_average_of_case_ratios(self):
        def altered(pdf, xlsx, annotation):
            result = self.oracle(pdf, xlsx, annotation)
            if pdf.stem == 'case1':
                result['annotated_nonempty_cells'] = 2
                result['exact_nonempty_cells'] = 1
                result['status'] = 'DEVIATION'
            else:
                result['annotated_nonempty_cells'] = 8
                result['exact_nonempty_cells'] = 8
            return result
        self.thresholds['min_nonempty_cell_accuracy'] = 0.9
        self.save()
        result = evaluate_corpus(self.manifest, oracle=altered)
        self.assertEqual(result['nonempty_cell_accuracy'], 0.9)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['deviating_cases'], 1)

    def test_fidelity_regression_fails_gate(self):
        def bad(pdf, xlsx, annotation):
            result = self.oracle(pdf, xlsx, annotation)
            result['exact_nonempty_cells'] = 4
            result['status'] = 'DEVIATION'
            return result
        result = evaluate_corpus(self.manifest, oracle=bad)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('min_nonempty_cell_accuracy', result['failed_thresholds'])

    def test_rounded_ratio_cannot_hide_threshold_failure(self):
        def nearly_good(*paths):
            result = self.oracle(*paths)
            result['annotated_nonempty_cells'] = 1000000
            result['exact_nonempty_cells'] = 949999
            result['status'] = 'DEVIATION'
            return result
        self.thresholds['min_nonempty_cell_accuracy'] = 0.95
        self.save()
        result = evaluate_corpus(self.manifest, oracle=nearly_good)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['nonempty_cell_accuracy'], 0.949999)

    def test_empty_annotated_corpus_fails_closed(self):
        def empty(*paths):
            result = self.oracle(*paths)
            result['expected_tables'] = 0
            result['observed_tables'] = 0
            result['matched_tables'] = 0
            result['annotated_nonempty_cells'] = 0
            result['exact_nonempty_cells'] = 0
            return result
        with self.assertRaisesRegex(ValueError, 'sans tableaux'):
            evaluate_corpus(self.manifest, oracle=empty)

    def test_missing_human_annotation_fails_gate(self):
        self.thresholds['min_human_reviewed'] = 1
        self.save()
        result = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['synthetic_cases'], 2)

    def test_extra_cells_fail_gate(self):
        def extra(*paths):
            result = self.oracle(*paths)
            result['extra_nonempty_cells'] = 1
            result['status'] = 'DEVIATION'
            return result
        result = evaluate_corpus(self.manifest, oracle=extra)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['extra_nonempty_cells'], 2)

    def test_identical_pdf_bytes_under_different_names_rejected(self):
        (self.root / self.cases[1]['pdf']).write_bytes(
            (self.root / self.cases[0]['pdf']).read_bytes())
        with self.assertRaisesRegex(ValueError, 'non independant'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_identical_xlsx_bytes_under_different_names_rejected(self):
        (self.root / self.cases[1]['xlsx']).write_bytes(
            (self.root / self.cases[0]['xlsx']).read_bytes())
        with self.assertRaisesRegex(ValueError, 'non independant'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_duplicate_case_id_rejected(self):
        self.cases[1]['id'] = self.cases[0]['id']
        self.save()
        with self.assertRaisesRegex(ValueError, 'duplique'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_duplicate_json_key_rejected(self):
        self.manifest.write_text('{"schema":"x", "schema":"y"}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'dupliquee'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_path_traversal_rejected(self):
        self.cases[0]['pdf'] = '../outside.pdf'
        self.save()
        with self.assertRaisesRegex(ValueError, 'traversal'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_symlink_component_rejected(self):
        folder = self.root / 'real'
        folder.mkdir()
        (folder / 'source.pdf').write_bytes(b'pdf')
        link = self.root / 'linked'
        try:
            link.symlink_to(folder, target_is_directory=True)
        except OSError:
            self.skipTest('symlinks unavailable on Windows runner')
        self.cases[0]['pdf'] = 'linked/source.pdf'
        self.save()
        with self.assertRaisesRegex(ValueError, 'symbolique'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_bool_and_nonfinite_threshold_rejected(self):
        for value in (True, float('nan'), float('inf')):
            self.thresholds['min_table_recall'] = value
            self.save()
            with self.assertRaises(ValueError):
                evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_single_case_rejected_no_false_coverage(self):
        self.cases.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, 'entre 2 et 64'):
            evaluate_corpus(self.manifest, oracle=self.oracle)

    def test_bad_oracle_report_rejected(self):
        def bad(*args):
            result = self.oracle(*args)
            result['source_sha256'] = 'invalid'
            return result
        with self.assertRaisesRegex(ValueError, 'Empreinte'):
            evaluate_corpus(self.manifest, oracle=bad)

    @unittest.skipUnless((ROOT / '03-Sources/openpdf_xlsx_fidelity_v515.py').exists(),
                         'V515 report writer absent du candidat local')
    def test_no_overwrite_of_existing_report(self):
        report = self.root / 'report.json'
        report.write_text('original', encoding='utf-8')
        with patch('openpdf_xlsx_corpus_gate_v519.evaluate_corpus', return_value={'status': 'PASS'}):
            self.assertEqual(main(['--manifest', str(self.manifest), '--report', str(report)]), 2)
        self.assertEqual(report.read_text(encoding='utf-8'), 'original')

    @unittest.skipUnless((ROOT / '03-Sources/openpdf_xlsx_ground_truth_v517.py').exists(),
                         'V517 oracle absent du candidat local ; test integre actif sur GitHub')
    def test_real_pdf_to_xlsx_two_case_corpus(self):
        from openpdf_conversion_service_v351 import convert_office
        from openpdf_xlsx_ground_truth_v517 import SCHEMA as TRUTH_SCHEMA
        from test_xlsx_tables_v514 import fixture
        for case_number, case in enumerate(self.cases):
            pdf = self.root / case['pdf']
            xlsx = self.root / case['xlsx']
            pdf.unlink()
            xlsx.unlink()
            fixture(pdf, injection=bool(case_number))
            convert_office(pdf, xlsx, table_mode=True)
            truth = {'schema': TRUTH_SCHEMA,
                     'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                     'origin': 'synthetic_known_at_generation',
                     'tables': [{'page': 1, 'index': 1,
                                 'cells': [['Volume', 'Capacite'], ['SAN-A', '20 To'],
                                           ['SAN-B', '=1+1' if case_number else '50 To']],
                                 'merges': []}]}
            (self.root / case['annotations']).write_text(json.dumps(truth), encoding='utf-8')
        self.save()
        result = evaluate_corpus(self.manifest)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['cases'], 2)
        self.assertEqual(result['annotated_nonempty_cells'], 12)
        self.assertNotIn('SAN-A', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
