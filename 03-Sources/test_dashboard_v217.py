import unittest
from diagnostic_dashboard import build_dashboard
class V217Tests(unittest.TestCase):
    def test_toggle(self):
        html=build_dashboard({})
        self.assertIn('id="regions-visible"',html)
        self.assertIn('show-regions',html)
    def test_no_fabricated_regions(self):
        html=build_dashboard({})
        self.assertNotIn('<span class="pdf-region"',html)
    def test_version(self):
        self.assertIn('Diagnostic V25.4',build_dashboard({}))
    def test_javascript_included(self):
        self.assertIn("stage.classList.toggle('show-regions'",build_dashboard({}))
if __name__=='__main__':unittest.main()
