"""Regression tests: OCR preflight rejects excessive jobs before rasterization."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-Sources'))
from openpdf_ocr_budget_v467 import plan_ocr_pages
from openpdf_ocr_service_v347 import searchable_pdf


class OCRBudgetTests(unittest.TestCase):
    def test_selected_pages_only(self):
        with fitz.open() as doc:
            for _ in range(3):
                doc.new_page(width=300, height=400)
            selected, audit = plan_ocr_pages(
                doc, 200, lambda page: page.number != 1, max_ocr_pages=2)
            self.assertEqual(selected, (True, False, True))
            self.assertEqual(audit['ocr_pages'], 2)

    def test_reject_cumulative_pixels(self):
        with fitz.open() as doc:
            for _ in range(2):
                doc.new_page(width=300, height=400)
            with self.assertRaisesRegex(ValueError, 'pixels OCR dépassé'):
                plan_ocr_pages(doc, 200, lambda page: True,
                               max_total_pixels=1_000_000)

    def test_reject_page_count(self):
        with fitz.open() as doc:
            for _ in range(2):
                doc.new_page(width=300, height=400)
            with self.assertRaisesRegex(ValueError, 'pages OCR dépassé'):
                plan_ocr_pages(doc, 200, lambda page: True, max_ocr_pages=1)

    def test_reject_single_page(self):
        with fitz.open() as doc:
            doc.new_page(width=2000, height=2000)
            with self.assertRaisesRegex(ValueError, 'limite de pixels'):
                plan_ocr_pages(doc, 200, lambda page: True,
                               max_total_pixels=10**12)

    def test_invalid_budgets(self):
        with fitz.open() as doc:
            doc.new_page()
            for kwargs in ({'max_ocr_pages': True},
                           {'max_ocr_pages': 0},
                           {'max_total_pixels': False}):
                with self.assertRaises(ValueError):
                    plan_ocr_pages(doc, 200, lambda page: True, **kwargs)

    def test_service_rejects_before_rasterization(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.pdf'
            destination = Path(folder) / 'output.pdf'
            with fitz.open() as doc:
                for _ in range(2):
                    doc.new_page(width=300, height=400)
                doc.save(source)
            with patch.object(fitz.Page, 'get_pixmap',
                              side_effect=AssertionError('OCR started')):
                with self.assertRaisesRegex(ValueError, 'pages OCR dépassé'):
                    searchable_pdf(source, destination, language='eng',
                                   max_ocr_pages=1)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(folder).glob('.openpdf-ocr-*')), [])

    def test_text_only_pages_do_not_consume_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.pdf'
            destination = Path(folder) / 'output.pdf'
            with fitz.open() as doc:
                for _ in range(3):
                    page = doc.new_page(width=300, height=400)
                    page.insert_text((30, 40), 'Digital page')
                doc.save(source)
            receipt = searchable_pdf(source, destination, language='eng',
                                     max_ocr_pages=1, max_ocr_pixels=1)
            self.assertEqual((receipt.ocr_pages, receipt.skipped_pages), (0, 3))


if __name__ == '__main__':
    unittest.main()
