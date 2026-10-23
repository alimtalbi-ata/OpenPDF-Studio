"""Functional metadata fidelity tests using real PyMuPDF documents.
Author: Abdelhalim Talbi. V50.1.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_metadata_fidelity_v501 import (FIELDS, MetadataPlan, prepare_metadata,
                                              apply_metadata, verify_metadata)
from openpdf_operations import run_operation


class MetadataFidelityV501(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.source = self.folder / 'source.pdf'
        self.target = self.folder / 'result.pdf'
        self.fields = dict(title='Rapport - été 2026', author='Abdelhalim Talbi',
                           subject='Qualité PDF / stockage', keywords='PDF, OCR, fidélité',
                           creator='OpenPDF Studio')
        with fitz.open() as doc:
            for i in range(1, 5):
                doc.new_page().insert_text((72, 72), f'Page {i}')
            doc.set_metadata(self.fields)
            doc.save(self.source)
        self.source_digest = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def assert_fidelity(self, operation, expected):
        with fitz.open(self.target) as output:
            self.assertEqual([page.get_text().strip() for page in output],
                             [f'Page {i}' for i in expected])
            for key, value in self.fields.items():
                self.assertEqual(output.metadata[key], value, key)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source_digest)

    def test_extract_contiguous(self):
        run_operation('extraction', [self.source], self.target, first=2, last=3)
        self.assert_fidelity('extraction', [2, 3])

    def test_extract_selection(self):
        run_operation('extraction', [self.source], self.target, extraction_selection='4,2,2')
        self.assert_fidelity('extraction', [4, 2, 2])

    def test_reorder(self):
        run_operation('reorganisation', [self.source], self.target, order='inverse')
        self.assert_fidelity('reorganisation', [4, 3, 2, 1])

    def test_empty_metadata(self):
        with fitz.open() as doc:
            doc.new_page()
            plan = prepare_metadata(doc)
            self.assertEqual(plan.as_dict(), {key: '' for key in FIELDS})
            with fitz.open() as dest:
                dest.new_page()
                apply_metadata(dest, plan)
                verify_metadata(dest, plan)

    def test_reject_invalid_plan(self):
        with fitz.open() as doc:
            doc.new_page()
            with self.assertRaises(TypeError):
                apply_metadata(doc, {})
            with self.assertRaises(TypeError):
                verify_metadata(doc, {})

    def test_reject_nul(self):
        with self.assertRaises(ValueError):
            prepare_metadata(SimpleNamespace(needs_pass=False, metadata={'title':'bad\x00value'}))

    def test_reject_oversize(self):
        with self.assertRaises(ValueError):
            prepare_metadata(SimpleNamespace(needs_pass=False, metadata={'title':'A'*262145}))

    def test_detect_modified_metadata(self):
        with fitz.open() as doc:
            doc.new_page()
            doc.set_metadata({'title':'other'})
            with self.assertRaises(RuntimeError):
                verify_metadata(doc, MetadataPlan((('title', 'expected'),)))

    def test_existing_target_preserved(self):
        self.target.write_bytes(b'EXISTING')
        with self.assertRaises(FileExistsError):
            run_operation('extraction', [self.source], self.target, extraction_selection='2')
        self.assertEqual(self.target.read_bytes(), b'EXISTING')

    def test_metadata_validation_does_not_publish(self):
        with patch('openpdf_metadata_fidelity_v501.prepare_metadata', side_effect=ValueError('invalid')):
            with self.assertRaises(ValueError):
                run_operation('reorganisation', [self.source], self.target, order='2,1')
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
