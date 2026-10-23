"""V49.8 PDF page set selectors: real PDF, bounds and publication tests.
Author: Abdelhalim Talbi.
"""
from pathlib import Path
import sys
import tempfile
import unittest
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '03-Sources'))
from openpdf_page_order_v497 import parse_page_order, plan_page_order
from openpdf_ui_controller_v348 import run_operation


class KeywordGrammarTests(unittest.TestCase):
    def test_french_and_english_aliases(self):
        cases = {
            'toutes': [1,2,3,4,5], 'all': [1,2,3,4,5],
            'impaires': [1,3,5], 'odd': [1,3,5],
            'paires': [2,4], 'even': [2,4],
            'inverse': [5,4,3,2,1], 'reverse': [5,4,3,2,1],
            'premiere': [1], 'première': [1], 'first': [1],
            'derniere': [5], 'dernière': [5], 'last': [5],
        }
        for token, expected in cases.items():
            with self.subTest(token=token):
                self.assertEqual(parse_page_order(token, 5), expected)

    def test_case_insensitive_and_mixed(self):
        p = plan_page_order(' PAIRES ; 5, Impaires ', 5)
        self.assertEqual(p.pages, (2,4,5,1,3,5))
        self.assertEqual((p.duplicated_pages, p.omitted_pages), (1, 0))

    def test_limit_before_expansion(self):
        with self.assertRaisesRegex(ValueError, 'maximum'):
            parse_page_order('inverse', 100000, max_output_pages=100)
        with self.assertRaisesRegex(ValueError, 'maximum'):
            parse_page_order('impaires,impaires', 5, max_output_pages=5)

    def test_empty_even_set(self):
        with self.assertRaisesRegex(ValueError, 'Aucune page'):
            parse_page_order('paires', 1)

    def test_unknown_and_empty_segments(self):
        for expression in ('odd,', ',all', 'every', 'all; ;1', 'lastone'):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                parse_page_order(expression, 5)

    def test_original_numeric_grammar(self):
        self.assertEqual(parse_page_order('3-1,5,5', 5), [3,2,1,5,5])


class KeywordRealPdfTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'input.pdf'
        self.target = self.root / 'output.pdf'
        with fitz.open() as pdf:
            for i in range(5):
                pdf.new_page().insert_text((72, 72), f'V49.8 PAGE {i+1}')
            pdf.save(self.source)

    def test_even_then_last_real_pdf(self):
        receipt = run_operation('reorganisation', [self.source], self.target,
                                order='paires,derniere')
        self.assertEqual(receipt.page_counts, (3,))
        with fitz.open(self.target) as pdf:
            self.assertEqual([p.get_text().strip() for p in pdf],
                             ['V49.8 PAGE 2', 'V49.8 PAGE 4', 'V49.8 PAGE 5'])

    def test_reverse_real_pdf(self):
        run_operation('reorganisation', [self.source], self.target, order='inverse')
        with fitz.open(self.target) as pdf:
            self.assertEqual([p.get_text().strip() for p in pdf],
                             [f'V49.8 PAGE {i}' for i in range(5, 0, -1)])

    def test_existing_output_not_overwritten(self):
        self.target.write_bytes(b'foreign data')
        with self.assertRaises(FileExistsError):
            run_operation('reorganisation', [self.source], self.target, order='impaires')
        self.assertEqual(self.target.read_bytes(), b'foreign data')

    def test_invalid_set_never_published(self):
        with self.assertRaises(ValueError):
            run_operation('reorganisation', [self.source], self.target, order='paires,unknown')
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
