"""V525: independent synthetic ground truth across ruled, borderless, mixed PDFs.

No claim of human annotation or visual fidelity. Author: Abdelhalim Talbi.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_conversion_service_v351 import convert_office
from openpdf_xlsx_corpus_gate_v519 import SCHEMA as CORPUS_SCHEMA, evaluate_corpus
from openpdf_xlsx_ground_truth_v517 import SCHEMA as TRUTH_SCHEMA
from test_xlsx_tables_v514 import fixture as ruled_pdf
from test_xlsx_borderless_v522 import make_pdf as borderless_pdf
from test_xlsx_mixed_v523 import make_mixed_pdf
from openpyxl import load_workbook


class IndependentCorpusV525(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cases = []
        for case_id in ('ruled-formula', 'borderless-multipage', 'mixed-ruled-text'):
            pdf = self.root / f'{case_id}.pdf'
            xlsx = self.root / f'{case_id}.xlsx'
            annotation = self.root / f'{case_id}.json'
            if case_id == 'ruled-formula':
                ruled_pdf(pdf, injection=True)
                grids = [(1, 1, [['Volume', 'Capacite'], ['SAN-A', '20 To'], ['SAN-B', '=1+1']])]
            elif case_id == 'borderless-multipage':
                borderless_pdf(pdf, pages=2)
                grids = [(page, 1, [[f'P{page}-R{r}-C{c}' for c in range(3)]
                                    for r in range(4)]) for page in (1, 2)]
            else:
                make_mixed_pdf(pdf, side_by_side=True)
                grids = [(1, 1, [[f'RULE-{r}-{c}' for c in range(3)] for r in range(4)]),
                         (1, 2, [[f'TEXT-{r}-{c}' for c in range(3)] for r in range(4)])]
            convert_office(pdf, xlsx, table_mode=True)
            annotation.write_text(json.dumps({
                'schema': TRUTH_SCHEMA,
                'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'origin': 'synthetic_known_at_generation',
                'tables': [{'page': page, 'index': index, 'cells': cells, 'merges': []}
                           for page, index, cells in grids],
            }), encoding='utf-8')
            self.cases.append({'id': case_id, 'pdf': pdf.name,
                               'xlsx': xlsx.name, 'annotations': annotation.name})
        self.manifest = self.root / 'manifest.json'
        self._save_manifest()

    def _save_manifest(self):
        self.manifest.write_text(json.dumps({
            'schema': CORPUS_SCHEMA, 'cases': self.cases,
            'thresholds': {'min_nonempty_cell_accuracy': 1.0,
                           'min_table_recall': 1.0, 'min_merge_recall': 1.0,
                           'max_extra_nonempty_cells': 0, 'min_human_reviewed': 0},
        }), encoding='utf-8')

    def test_three_distinct_real_pdf_conversions_pass_ground_truth(self):
        report = evaluate_corpus(self.manifest)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual((report['cases'], report['human_reviewed_cases'],
                          report['synthetic_cases']), (3, 0, 3))
        self.assertEqual((report['expected_tables'], report['matched_tables']), (5, 5))
        self.assertEqual(report['annotated_nonempty_cells'], 54)
        self.assertEqual(report['exact_nonempty_cells'], 54)
        self.assertNotIn('SAN-A', json.dumps(report))

    def test_mutated_workbook_fails_release_gate(self):
        target = self.root / self.cases[2]['xlsx']
        wb = load_workbook(target)
        wb.worksheets[2]['B4'] = 'INVENTED'
        wb.save(target)
        wb.close()
        report = evaluate_corpus(self.manifest)
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('min_nonempty_cell_accuracy', report['failed_thresholds'])

    def test_duplicate_source_content_rejected_even_with_new_filename(self):
        original = self.root / self.cases[0]['pdf']
        duplicate = self.root / self.cases[2]['pdf']
        duplicate.write_bytes(original.read_bytes())
        # Oracle validates source hashes against annotations; update annotation
        # so the duplicate test specifically reaches the corpus independence gate.
        truth_path = self.root / self.cases[2]['annotations']
        truth = json.loads(truth_path.read_text(encoding='utf-8'))
        truth['source_sha256'] = hashlib.sha256(duplicate.read_bytes()).hexdigest()
        truth_path.write_text(json.dumps(truth), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'non independant'):
            evaluate_corpus(self.manifest)


if __name__ == '__main__':
    unittest.main()
