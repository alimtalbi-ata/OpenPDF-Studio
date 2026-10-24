"""V530: independent PDF/XLSX evidence rejects ghost cells, hidden sheets and tampering.
Synthetic PDF fixture; no human GUI or business-document qualification.
Author: Abdelhalim Talbi.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))

from openpyxl import load_workbook
from openpdf_conversion_service_v351 import convert_office
from openpdf_xlsx_ground_truth_v517 import SCHEMA, evaluate_ground_truth
from test_xlsx_tables_v514 import fixture


class GroundTruthIntegrityV530(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.pdf, self.xlsx, self.annotation = (
            root / 'input.pdf', root / 'output.xlsx', root / 'truth.json')
        fixture(self.pdf)
        convert_office(self.pdf, self.xlsx, table_mode=True)
        self.truth = {
            'schema': SCHEMA,
            'source_sha256': hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
            'origin': 'synthetic_known_at_generation',
            'tables': [{'page': 1, 'index': 1,
                        'cells': [['Volume', 'Capacite'], ['SAN-A', '20 To'], ['SAN-B', '50 To']],
                        'merges': []}],
        }
        self.annotation.write_text(json.dumps(self.truth), encoding='utf-8')
        self.assertEqual(
            evaluate_ground_truth(self.pdf, self.xlsx, self.annotation)['status'], 'PASS')

    def change_book(self, change):
        book = load_workbook(self.xlsx)
        try:
            change(book)
            book.save(self.xlsx)
        finally:
            book.close()

    def assert_ghost_detected(self, cell):
        self.change_book(lambda book: setattr(book.worksheets[1][cell], 'value', 'PHANTOM'))
        report = evaluate_ground_truth(self.pdf, self.xlsx, self.annotation)
        self.assertEqual(report['status'], 'DEVIATION')
        self.assertEqual(report['extra_nonempty_cells'], 1)
        self.assertEqual(report['exact_cells'], 6)
        self.assertNotIn('PHANTOM', json.dumps(report))

    def test_provenance_row_ghost_e1(self):
        self.assert_ghost_detected('E1')

    def test_spacer_row_ghost_a2(self):
        self.assert_ghost_detected('A2')

    def test_spacer_row_ghost_outside_grid_e2(self):
        self.assert_ghost_detected('E2')

    def test_far_right_ghost_on_table_row(self):
        self.assert_ghost_detected('G4')

    def test_hidden_table_sheet_fails_closed(self):
        self.change_book(lambda book: setattr(book.worksheets[1], 'sheet_state', 'hidden'))
        with self.assertRaisesRegex(ValueError, 'masquee|visible'):
            evaluate_ground_truth(self.pdf, self.xlsx, self.annotation)

    def test_hidden_legacy_sheet_fails_closed(self):
        self.change_book(lambda book: setattr(book.worksheets[0], 'sheet_state', 'hidden'))
        with self.assertRaisesRegex(ValueError, 'masquee|visible'):
            evaluate_ground_truth(self.pdf, self.xlsx, self.annotation)

    def test_annotation_tampering_during_evaluation_fails_closed(self):
        from openpdf_xlsx_fidelity_v515 import _xlsx_preflight

        def mutate_during_preflight(path):
            self.truth['origin'] = 'human_reviewed'
            self.annotation.write_text(json.dumps(self.truth), encoding='utf-8')
            return _xlsx_preflight(path)

        with patch('openpdf_xlsx_fidelity_v515._xlsx_preflight',
                   side_effect=mutate_during_preflight):
            with self.assertRaisesRegex(ValueError, 'Annotation.*modifiee|modifiee.*annotation'):
                evaluate_ground_truth(self.pdf, self.xlsx, self.annotation)


if __name__ == '__main__':
    unittest.main()
