"""Early validation of page options in the Windows UI. Abdelhalim Talbi."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03-Sources'))
from openpdf_desktop import validate_page_options

class PageOptionsTests(unittest.TestCase):
    def test_extract_valid(self):
        self.assertTrue(validate_page_options('extraction',first='1',last='4'))
    def test_extract_reverse(self):
        with self.assertRaisesRegex(ValueError,'début'):
            validate_page_options('extraction',first='4',last='2')
    def test_extract_not_numeric(self):
        with self.assertRaisesRegex(ValueError,'entiers'):
            validate_page_options('extraction',first='abc',last='4')
    def test_split_zero(self):
        with self.assertRaisesRegex(ValueError,'au moins'):
            validate_page_options('decoupage',chunk='0')
    def test_split_not_numeric(self):
        with self.assertRaisesRegex(ValueError,'entier'):
            validate_page_options('decoupage',chunk='xyz')
    def test_reorder_valid(self):
        self.assertTrue(validate_page_options('reorganisation',order='3,1,2'))
    def test_reorder_empty_token(self):
        with self.assertRaisesRegex(ValueError,'liste'):
            validate_page_options('reorganisation',order='1,,2')
    def test_reorder_negative(self):
        with self.assertRaises(ValueError):
            validate_page_options('reorganisation',order='-1,2')
if __name__=='__main__':unittest.main()
