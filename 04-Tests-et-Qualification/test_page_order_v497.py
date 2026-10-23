"""OpenPDF V49.7 page order regression tests. Author: Abdelhalim Talbi."""
from pathlib import Path
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03-Sources"))
from openpdf_page_order_v497 import plan_page_order, parse_page_order
from openpdf_ui_controller_v348 import run_operation


class PageOrderV497(unittest.TestCase):
    def test_ranges_duplicates_and_metrics(self):
        p = plan_page_order("3-1,5;5,2-4", 5)
        self.assertEqual(p.pages, (3,2,1,5,5,2,3,4))
        self.assertEqual((p.output_pages,p.duplicated_pages,p.omitted_pages), (8,3,0))

    def test_invalid_input(self):
        for value in ("", "1,", "1,,2", "1-", "-1", "1:2", "0", "6", "2-6", "1; ;2", "１", "1e2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_page_order(value, 5)

    def test_expansion_budget(self):
        with self.assertRaises(ValueError):
            parse_page_order("1-5,1-5", 5, max_output_pages=9)

    def test_invalid_page_count(self):
        for count in (0, True, -1, "5"):
            with self.subTest(count=count), self.assertRaises(ValueError):
                parse_page_order("1", count)

    def test_real_pdf_reorder_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/"src.pdf"
            dst = Path(d)/"out.pdf"
            with fitz.open() as doc:
                for n in range(1,6):
                    doc.new_page().insert_text((72,72), f"Original page {n}")
                doc.save(src)
            receipt = run_operation("reorganisation", [src], dst, order="3-1,5,5")
            self.assertEqual(receipt.page_counts, (5,))
            with fitz.open(dst) as doc:
                self.assertEqual([p.get_text().strip() for p in doc],
                                 ["Original page 3","Original page 2","Original page 1","Original page 5","Original page 5"])
            with self.assertRaises(FileExistsError):
                run_operation("reorganisation", [src], dst, order="1")
            self.assertEqual(dst.stat().st_size > 0, True)

    def test_invalid_request_has_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d)/"src.pdf"
            dst = Path(d)/"out.pdf"
            with fitz.open() as doc:
                doc.new_page()
                doc.save(src)
            with self.assertRaises(ValueError):
                run_operation("reorganisation", [src], dst, order="1-2")
            self.assertFalse(dst.exists())


if __name__ == "__main__":
    unittest.main()
