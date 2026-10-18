import unittest
from openpdf_functional_qualification import run_suite
class FunctionalTests(unittest.TestCase):
    def test_all_functional_scenarios(self):
        result=run_suite()
        self.assertEqual(result['passed'],result['total'],result)
    def test_coverage(self):
        self.assertEqual({c['case'] for c in run_suite()['cases']},{'merge','extract','reorder','split-single','compression-publication'})
if __name__=='__main__':unittest.main()
