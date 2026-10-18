import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class BrowserReadinessTests(unittest.TestCase):
    def test_rows_initialized_before_first_access(self):
        html=build_dashboard({})
        self.assertLess(html.index("const rows=[...document.querySelectorAll('tbody tr[data-severity]')];"),html.index('rows.forEach(r=>r.tabIndex=-1)'))
    def test_version(self):
        self.assertIn('Diagnostic V25.4',build_dashboard({}))
    def test_browser_runner_present(self):
        self.assertTrue(Path(__file__).with_name('browser_qualification_v232.py').exists())
