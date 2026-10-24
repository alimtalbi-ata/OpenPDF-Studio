"""V528 independent evidence binding and per-document fidelity floors.
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
from openpdf_xlsx_corpus_gate_v519 import SCHEMA, evaluate_corpus


class EvidenceBindingV528(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cases = []
        for i in range(2):
            c = {'id': f'case-{i}', 'pdf': f'{i}.pdf', 'xlsx': f'{i}.xlsx', 'annotations': f'{i}.json'}
            for k in ('pdf', 'xlsx', 'annotations'):
                (self.root / c[k]).write_bytes(f'{k}-{i}'.encode())
            self.cases.append(c)
        self.thresholds = {'min_nonempty_cell_accuracy': .4, 'min_table_recall': .4,
                           'min_merge_recall': 0, 'max_extra_nonempty_cells': 2,
                           'min_human_reviewed': 0}
        self.manifest = self.root / 'manifest.json'

    def write_manifest(self):
        self.manifest.write_text(json.dumps({'schema': SCHEMA, 'cases': self.cases,
                                             'thresholds': self.thresholds}))

    def oracle(self, pdf, xlsx, annotations):
        first = pdf.name == '0.pdf'
        return {'schema': 'openpdf.xlsx.ground_truth.report.v1',
                'status': 'DEVIATION' if first else 'PASS',
                'annotation_origin': 'synthetic_known_at_generation',
                'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'workbook_sha256': hashlib.sha256(xlsx.read_bytes()).hexdigest(),
                'annotation_sha256': hashlib.sha256(annotations.read_bytes()).hexdigest(),
                'expected_tables': 1, 'observed_tables': 1, 'matched_tables': 1,
                'annotated_cells': 10, 'exact_cells': 5 if first else 10,
                'annotated_nonempty_cells': 2, 'exact_nonempty_cells': 2,
                'extra_nonempty_cells': 0, 'expected_merges': 2,
                'observed_merges': 1 if first else 2, 'matched_merges': 1 if first else 2}

    def test_independent_case_cell_accuracy_rejects_masked_failure(self):
        self.write_manifest()
        self.assertEqual(evaluate_corpus(self.manifest, oracle=self.oracle)['status'], 'PASS')
        self.thresholds['min_case_cell_exact_accuracy'] = .9
        self.write_manifest()
        report = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['worst_case_cell_exact_accuracy'], .5)
        self.assertEqual(report['cases_below_quality_floors'], 1)

    def test_independent_merge_recall_rejects_masked_failure(self):
        self.thresholds['min_case_merge_recall'] = .9
        self.write_manifest()
        report = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['worst_case_merge_recall'], .5)

    def test_forged_sha256_rejected(self):
        self.write_manifest()
        def forged(*files):
            result = self.oracle(*files)
            result['source_sha256'] = '0' * 64
            return result
        with self.assertRaisesRegex(ValueError, 'non liee'):
            evaluate_corpus(self.manifest, oracle=forged)

    def test_changed_file_during_oracle_rejected(self):
        self.write_manifest()
        def mutating(*files):
            result = self.oracle(*files)
            files[2].write_bytes(b'mutated-after-oracle')
            return result
        with self.assertRaisesRegex(ValueError, 'modifiee'):
            evaluate_corpus(self.manifest, oracle=mutating)

    def test_invalid_new_thresholds_rejected(self):
        for name in ('min_case_cell_exact_accuracy', 'min_case_merge_recall'):
            for invalid in (True, -0.01, 1.01):
                with self.subTest(name=name, invalid=invalid):
                    self.thresholds[name] = invalid
                    self.write_manifest()
                    with self.assertRaises(ValueError):
                        evaluate_corpus(self.manifest, oracle=self.oracle)
            self.thresholds.pop(name)

    def test_no_case_names_or_values_in_report(self):
        self.thresholds['min_case_merge_recall'] = .9
        self.write_manifest()
        report = evaluate_corpus(self.manifest, oracle=self.oracle)
        self.assertNotIn('case-0', json.dumps(report))
        self.assertNotIn('annotations-0', json.dumps(report))


if __name__ == '__main__':
    unittest.main()
