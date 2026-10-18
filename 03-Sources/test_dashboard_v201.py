import unittest
from diagnostic_dashboard import build_dashboard

class TestDashboardV201(unittest.TestCase):
    def setUp(self):
        self.html=build_dashboard({'warnings':['Missing item'], 'layout_comparable':False})
    def test_search(self): self.assertIn('id="query"',self.html)
    def test_live_counter(self): self.assertIn('id="filtered-count"',self.html)
    def test_filter(self): self.assertIn('function filterFindings()',self.html)
    def test_export_filtered(self): self.assertIn('rows.filter(r=>!r.hidden)',self.html)
    def test_keyboard_focus(self): self.assertIn('focus-visible',self.html)
    def test_version(self): self.assertIn('Diagnostic V25.4',self.html)
    def test_no_network(self): self.assertNotIn('https://',self.html)

if __name__=='__main__':unittest.main()
