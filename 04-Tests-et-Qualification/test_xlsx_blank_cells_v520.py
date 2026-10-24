"""V520: prevent invented Excel values in annotated blank cells.
Real synthetic PDF -> XLSX; synthetic ground truth, NOT human review.
Author: Abdelhalim Talbi.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpyxl import load_workbook
from openpdf_conversion_service_v351 import convert_office
from openpdf_xlsx_ground_truth_v517 import SCHEMA as TRUTH_SCHEMA, evaluate_ground_truth
from openpdf_xlsx_corpus_gate_v519 import SCHEMA as CORPUS_SCHEMA, evaluate_corpus
from test_xlsx_tables_v514 import fixture


class BlankCellFalsePositiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cases = []
        for n in (1, 2):
            pdf = self.root / f'doc{n}.pdf'
            xlsx = self.root / f'doc{n}.xlsx'
            annotation = self.root / f'doc{n}.json'
            fixture(pdf)
            convert_office(pdf, xlsx, table_mode=True)
            truth = {
                'schema': TRUTH_SCHEMA,
                'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'origin': 'synthetic_known_at_generation',
                'tables': [{'page': 1, 'index': 1,
                            'cells': [['Volume', 'Capacite', None],
                                      ['SAN-A', '20 To', None],
                                      ['SAN-B', '50 To', None]],
                            'merges': []}],
            }
            annotation.write_text(json.dumps(truth), encoding='utf-8')
            self.cases.append((pdf, xlsx, annotation))
        self.manifest = self.root / 'corpus.json'
        self.manifest.write_text(json.dumps({
            'schema': CORPUS_SCHEMA,
            'cases': [{'id': f'case-{n}', 'pdf': pdf.name,
                       'xlsx': xlsx.name, 'annotations': annotation.name}
                      for n, (pdf, xlsx, annotation) in enumerate(self.cases, 1)],
            'thresholds': {'min_nonempty_cell_accuracy': 1.0,
                           'min_table_recall': 1.0,
                           'min_merge_recall': 1.0,
                           'max_extra_nonempty_cells': 0,
                           'min_human_reviewed': 0},
        }), encoding='utf-8')

    def inject(self, index, address, value):
        book = load_workbook(self.cases[index][1])
        try:
            book.worksheets[1][address] = value
            book.save(self.cases[index][1])
        finally:
            book.close()

    def test_clean_conversion_passes(self):
        report = evaluate_ground_truth(*self.cases[0])
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['annotated_cells'], 9)
        self.assertEqual(report['exact_cells'], 9)
        self.assertEqual(report['extra_nonempty_cells'], 0)

    def test_invented_value_inside_blank_cell_counted(self):
        self.inject(0, 'C4', 'INVENTED-SECRET-VALUE')
        report = evaluate_ground_truth(*self.cases[0])
        self.assertEqual(report['status'], 'DEVIATION')
        self.assertEqual(report['annotated_nonempty_cells'], 6)
        self.assertEqual(report['exact_nonempty_cells'], 6)
        self.assertEqual(report['extra_nonempty_cells'], 1)
        self.assertEqual(report['exact_cells'], 8)
        self.assertNotIn('INVENTED-SECRET-VALUE', json.dumps(report))

    def test_corpus_gate_fails_despite_perfect_nonempty_accuracy(self):
        self.inject(1, 'C5', 'INVENTED-SECRET-VALUE')
        result = evaluate_corpus(self.manifest)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['nonempty_cell_accuracy'], 1.0)
        self.assertEqual(result['extra_nonempty_cells'], 1)
        self.assertIn('max_extra_nonempty_cells', result['failed_thresholds'])
        self.assertNotIn('INVENTED-SECRET-VALUE', json.dumps(result))

    def test_extra_outside_grid_still_counted(self):
        self.inject(0, 'D6', 'EXTRA-OUTSIDE')
        report = evaluate_ground_truth(*self.cases[0])
        self.assertEqual(report['extra_nonempty_cells'], 1)
        self.assertEqual(report['status'], 'DEVIATION')


if __name__ == '__main__':
    unittest.main()
