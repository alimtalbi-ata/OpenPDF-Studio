import unittest
from diagnostic_dashboard import build_dashboard
from pathlib import Path
class Region219(unittest.TestCase):
 def test_details(self): self.assertIn('region-selection-details',build_dashboard({}))
 def test_previous(self): self.assertIn('region-selection-previous',build_dashboard({}))
 def test_next(self): self.assertIn('region-selection-next',build_dashboard({}))
 def test_navigation(self): self.assertIn('function step(direction)',Path(__file__).with_name('region_overlay.js').read_text())
 def test_percentage(self): self.assertIn('non mesure PDF',Path(__file__).with_name('region_overlay.js').read_text())
 def test_version(self): self.assertIn('Diagnostic V25.4',build_dashboard({}))
