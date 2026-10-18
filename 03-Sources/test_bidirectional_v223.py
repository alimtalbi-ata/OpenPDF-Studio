import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class BidirectionalV223(unittest.TestCase):
 def test_version(self):self.assertIn('Diagnostic V25.4',build_dashboard({}))
 def test_embedded(self):self.assertIn('region-back-to-correlations',build_dashboard({}))
 def test_page_only(self):self.assertIn('Aucun lien texte-région individuel démontré',build_dashboard({}))
 def test_safe_page(self):self.assertIn('Number.isSafeInteger(page)',build_dashboard({}))
 def test_selection_event(self):self.assertIn('openpdf:region-selected',Path('bidirectional_navigation.js').read_text())
 def test_navigation_event(self):self.assertIn('openpdf:correlation-page',Path('bidirectional_navigation.js').read_text())
 def test_clear_event(self):self.assertIn('openpdf:region-cleared',Path('bidirectional_navigation.js').read_text())
 def test_accessibility(self):self.assertIn("setAttribute('aria-current','location')",Path('bidirectional_navigation.js').read_text())
