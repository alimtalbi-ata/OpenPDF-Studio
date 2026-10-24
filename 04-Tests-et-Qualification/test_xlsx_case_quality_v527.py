"""V527 opt-in per-case PDF->XLSX quality floors. Author: Abdelhalim Talbi."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_xlsx_corpus_gate_v519 import SCHEMA, evaluate_corpus


class PerCaseQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cases = []
        for i in range(2):
            files = {'id': f'private-case-{i}', 'pdf': f'{i}.pdf',
                     'xlsx': f'{i}.xlsx', 'annotations': f'{i}.json'}
            for key in ('pdf', 'xlsx', 'annotations'):
                (self.root / files[key]).write_bytes(f'{key}:{i}'.encode())
            self.cases.append(files)
        self.thresholds = {
            'min_nonempty_cell_accuracy': .90,
            'min_table_recall': .90, 'min_merge_recall': 1.0,
            'max_extra_nonempty_cells': 2, 'min_human_reviewed': 0,
        }
        self.manifest = self.root / 'manifest.json'

    def write_manifest(self):
        self.manifest.write_text(json.dumps({
            'schema': SCHEMA, 'cases': self.cases, 'thresholds': self.thresholds,
        }))

    def oracle(self, pdf, xlsx, annotations):
        first = pdf.name.startswith('0.')
        return {
            'schema': 'openpdf.xlsx.ground_truth.report.v1',
            'status': 'DEVIATION' if first else 'PASS',
            'annotation_origin': 'synthetic_known_at_generation',
            'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
            'workbook_sha256': hashlib.sha256(xlsx.read_bytes()).hexdigest(),
            'annotation_sha256': hashlib.sha256(annotations.read_bytes()).hexdigest(),
            'expected_tables': 1 if first else 10,
            'observed_tables': 1 if first else 10,
            'matched_tables': 1 if first else 10,
            'annotated_cells': 2 if first else 100,
            'exact_cells': 1 if first else 100,
            'annotated_nonempty_cells': 2 if first else 100,
            'exact_nonempty_cells': 1 if first else 100,
            'extra_nonempty_cells': 1 if first else 0,
            'expected_merges': 0, 'observed_merges': 0, 'matched_merges': 0,
        }

    def test_masked_failure_rejected_without_case_names(self):
        self.write_manifest()
        self.assertEqual(evaluate_corpus(self.manifest, oracle=self.oracle)['status'], 'PASS')
        self.thresholds['min_case_nonempty_cell_accuracy'] = .90
        self.write_manifest()
        result = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['cases_below_quality_floors'], 1)
        self.assertEqual(result['worst_case_nonempty_cell_accuracy'], .5)
        self.assertNotIn('private-case-', json.dumps(result))

    def test_extra_cell_floor(self):
        self.thresholds['max_case_extra_nonempty_cells'] = 0
        self.write_manifest()
        result = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['worst_case_extra_nonempty_cells'], 1)

    def test_recall_floor(self):
        self.thresholds['min_case_table_recall'] = .9
        self.write_manifest()
        def missing(*args):
            result = self.oracle(*args)
            if args[0].name.startswith('0.'):
                result['expected_tables'] = 2
                result['matched_tables'] = 1
            return result
        result = evaluate_corpus(self.manifest, oracle=missing)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['worst_case_table_recall'], .5)

    def test_empty_case_fails_closed(self):
        self.thresholds['min_case_nonempty_cell_accuracy'] = .5
        self.write_manifest()
        def empty(*args):
            result = self.oracle(*args)
            if args[0].name.startswith('0.'):
                result['annotated_nonempty_cells'] = 0
                result['exact_nonempty_cells'] = 0
            return result
        with self.assertRaisesRegex(ValueError, 'non mesurable'):
            evaluate_corpus(self.manifest, oracle=empty)

    def test_invalid_optional_thresholds(self):
        for key, invalid in [('min_case_nonempty_cell_accuracy', True),
                             ('min_case_table_recall', 1.1),
                             ('max_case_extra_nonempty_cells', -1)]:
            with self.subTest(key=key):
                self.thresholds[key] = invalid
                self.write_manifest()
                with self.assertRaises(ValueError):
                    evaluate_corpus(self.manifest, oracle=self.oracle)
                del self.thresholds[key]

    def test_comparison_is_not_rounded(self):
        self.thresholds['min_case_nonempty_cell_accuracy'] = .95
        self.write_manifest()
        def close(*args):
            result = self.oracle(*args)
            if args[0].name.startswith('0.'):
                result['annotated_nonempty_cells'] = 1000000
                result['exact_nonempty_cells'] = 949999
            return result
        result = evaluate_corpus(self.manifest, oracle=close)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['worst_case_nonempty_cell_accuracy'], .949999)

    def test_real_pdf_conversion_and_mutation(self):
        from openpdf_conversion_service_v351 import convert_office
        from openpdf_xlsx_ground_truth_v517 import SCHEMA as TRUTH_SCHEMA
        from test_xlsx_tables_v514 import fixture
        from openpyxl import load_workbook
        for index, case in enumerate(self.cases):
            pdf = self.root / case['pdf']
            xlsx = self.root / case['xlsx']
            pdf.unlink()
            xlsx.unlink()
            fixture(pdf, injection=bool(index))
            convert_office(pdf, xlsx, table_mode=True)
            truth = {
                'schema': TRUTH_SCHEMA,
                'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'origin': 'synthetic_known_at_generation',
                'tables': [{'page': 1, 'index': 1,
                            'cells': [['Volume', 'Capacite'], ['SAN-A', '20 To'],
                                      ['SAN-B', '=1+1' if index else '50 To']],
                            'merges': []}],
            }
            (self.root / case['annotations']).write_text(json.dumps(truth))
            if index == 0:
                book = load_workbook(xlsx)
                book.worksheets[1]['B4'] = 'ALTERED'
                book.save(xlsx)
                book.close()
        self.thresholds['min_nonempty_cell_accuracy'] = .80
        self.write_manifest()
        self.assertEqual(evaluate_corpus(self.manifest)['status'], 'PASS')
        self.thresholds['min_case_nonempty_cell_accuracy'] = .90
        self.write_manifest()
        result = evaluate_corpus(self.manifest)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['cases_below_quality_floors'], 1)


if __name__ == '__main__':
    unittest.main()
