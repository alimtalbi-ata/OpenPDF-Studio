"""V49.9: exclusion selectors, bounds and real-PDF publication tests.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_page_order_v497 import parse_page_order, plan_page_order
from openpdf_operations import run_operation


class ExclusionGrammarV499(unittest.TestCase):
    def test_all_except_even(self):
        self.assertEqual(parse_page_order('toutes,!paires', 7), [1, 3, 5, 7])

    def test_implicit_all_except_range(self):
        self.assertEqual(parse_page_order('!2-4', 6), [1, 5, 6])

    def test_exclusion_removes_all_duplicates(self):
        plan = plan_page_order('3,3,2,1,!3', 4)
        self.assertEqual(plan.pages, (2, 1))
        self.assertEqual((plan.duplicated_pages, plan.omitted_pages), (0, 2))

    def test_exclusion_order_and_restore(self):
        self.assertEqual(parse_page_order('5-1,!2,!4,2', 5), [5, 3, 1, 2])

    def test_alias_and_mixed_separators(self):
        self.assertEqual(parse_page_order('ALL;!EVEN;!first', 5), [3, 5])

    def test_exclusion_of_missing_page_is_noop(self):
        self.assertEqual(parse_page_order('1-3,!5', 5), [1, 2, 3])

    def test_reject_empty_selection(self):
        for expr in ('!all', 'toutes,!toutes', '1,!1', '!1'):
            with self.subTest(expr=expr), self.assertRaisesRegex(ValueError, 'vide'):
                parse_page_order(expr, 1)

    def test_invalid_exclusion_tokens(self):
        for expr in ('!', 'all,!', '!!1', '!0', '!7', '!2-', '! 1 2', 'all,!unknown'):
            with self.subTest(expr=expr), self.assertRaises(ValueError):
                parse_page_order(expr, 6)

    def test_bounded_implicit_all(self):
        with self.assertRaisesRegex(ValueError, 'maximum'):
            parse_page_order('!2', 20000, max_output_pages=100)

    def test_bounded_positive_intermediate(self):
        with self.assertRaisesRegex(ValueError, 'maximum'):
            parse_page_order('all,!even', 100, max_output_pages=50)

    def test_readded_page_counts_against_budget(self):
        with self.assertRaisesRegex(ValueError, 'maximum'):
            parse_page_order('all,!even,even', 6, max_output_pages=5)

    def test_legacy_grammar_unchanged(self):
        self.assertEqual(parse_page_order('3-1,5,5', 5), [3, 2, 1, 5, 5])


class RealPDFExclusionsV499(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.src = self.root / 'original.pdf'
        self.dest = self.root / 'filtered.pdf'
        with fitz.open() as doc:
            for i in range(6):
                doc.new_page().insert_text((72, 72), f'V49.9 page {i + 1}')
            doc.save(self.src)

    def test_real_pdf_exclusion_with_receipt(self):
        original_hash = hashlib.sha256(self.src.read_bytes()).hexdigest()
        receipt = run_operation('reorganisation', [self.src], self.dest, order='!paires')
        self.assertEqual(receipt.page_counts, (3,))
        with fitz.open(self.dest) as doc:
            self.assertEqual([p.get_text().strip() for p in doc],
                             ['V49.9 page 1', 'V49.9 page 3', 'V49.9 page 5'])
        self.assertEqual(receipt.sha256[0], hashlib.sha256(self.dest.read_bytes()).hexdigest())
        self.assertEqual(original_hash, hashlib.sha256(self.src.read_bytes()).hexdigest())

    def test_no_overwrite_existing_output(self):
        self.dest.write_bytes(b'OTHER DATA')
        with self.assertRaises(FileExistsError):
            run_operation('reorganisation', [self.src], self.dest, order='!2')
        self.assertEqual(self.dest.read_bytes(), b'OTHER DATA')

    def test_invalid_selector_leaves_no_temp(self):
        with self.assertRaises(ValueError):
            run_operation('reorganisation', [self.src], self.dest, order='all,!all')
        self.assertFalse(self.dest.exists())
        self.assertFalse(list(self.root.glob('.openpdf-pages-*.pdf')))


if __name__ == '__main__':
    unittest.main()
