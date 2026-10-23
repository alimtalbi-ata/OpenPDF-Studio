"""V50.0: real-PDF extraction selection and regression tests.
Author: Abdelhalim Talbi.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))
from openpdf_operations import run_operation


class ExtractionSelectionV500(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.source = self.folder / "input.pdf"
        self.target = self.folder / "output.pdf"
        with fitz.open() as doc:
            for i in range(1, 7):
                doc.new_page().insert_text((72, 72), f"Extraction page {i}")
            doc.save(self.source)
        self.original = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def check_selection(self, selection, expected):
        receipt = run_operation("extraction", [self.source], self.target,
                                extraction_selection=selection)
        self.assertEqual(receipt.operation, "extract")
        self.assertEqual(receipt.page_counts, (len(expected),))
        self.assertEqual(receipt.sha256, (hashlib.sha256(self.target.read_bytes()).hexdigest(),))
        with fitz.open(self.target) as doc:
            self.assertEqual([p.get_text().strip() for p in doc],
                             [f"Extraction page {i}" for i in expected])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original)

    def test_odd(self):
        self.check_selection("!paires", [1, 3, 5])

    def test_discontinuous(self):
        self.check_selection("1,4,6", [1, 4, 6])

    def test_reverse(self):
        self.check_selection("5-3", [5, 4, 3])

    def test_duplicates(self):
        self.check_selection("2,2,1", [2, 2, 1])

    def test_exclusion_restore(self):
        self.check_selection("toutes,!paires,6", [1, 3, 5, 6])

    def test_legacy_range(self):
        receipt = run_operation("extraction", [self.source], self.target,
                                first=2, last=4, extraction_selection="")
        self.assertEqual(receipt.operation, "extract")
        with fitz.open(self.target) as doc:
            self.assertEqual([p.get_text().strip() for p in doc],
                             ["Extraction page 2", "Extraction page 3", "Extraction page 4"])

    def test_selection_overrides_range(self):
        self.check_selection("6", [6])

    def test_out_of_bounds_no_output(self):
        with self.assertRaises(ValueError):
            run_operation("extraction", [self.source], self.target,
                          extraction_selection="1,99")
        self.assertFalse(self.target.exists())

    def test_empty_selection_no_output(self):
        with self.assertRaises(ValueError):
            run_operation("extraction", [self.source], self.target,
                          extraction_selection="toutes,!toutes")
        self.assertFalse(self.target.exists())

    def test_invalid_type_no_output(self):
        with self.assertRaises(ValueError):
            run_operation("extraction", [self.source], self.target,
                          extraction_selection=["1"])
        self.assertFalse(self.target.exists())

    def test_existing_output_preserved(self):
        self.target.write_bytes(b"KEEP THIS FILE")
        with self.assertRaises(FileExistsError):
            run_operation("extraction", [self.source], self.target,
                          extraction_selection="1,3")
        self.assertEqual(self.target.read_bytes(), b"KEEP THIS FILE")

    def test_invalid_token_no_temp(self):
        with self.assertRaises(ValueError):
            run_operation("extraction", [self.source], self.target,
                          extraction_selection="!!1")
        self.assertFalse(list(self.folder.glob(".openpdf-pages-*.pdf")))


if __name__ == "__main__":
    unittest.main()
