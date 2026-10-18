"""Real PDF end-to-end tests. Author: Abdelhalim Talbi."""
import unittest
from openpdf_functional_v282 import run
class TestFunctional(unittest.TestCase):
    def test_real_pdf_workflows(self):
        self.assertEqual(len(run()),6)
if __name__=='__main__':unittest.main()
