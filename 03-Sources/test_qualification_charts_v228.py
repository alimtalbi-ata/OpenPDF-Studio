import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class ChartsV228(unittest.TestCase):
 def setUp(self): self.html=build_dashboard({});self.js=Path(__file__).with_name('qualification_charts.js').read_text()
 def test_filter(self): self.assertIn('qualification-severity-filter',self.html)
 def test_category(self): self.assertIn('qualification-category-filter',self.html)
 def test_reset(self): self.assertIn('qualification-filter-reset',self.html)
 def test_graph(self): self.assertIn('qualification-chart-bar',self.html)
 def test_meter(self): self.assertIn("document.createElement('meter')",self.html)
 def test_empty(self): self.assertIn('Aucune anomalie pour ces filtres.',self.html)
 def test_no_certification(self): self.assertIn('revue humaine requise',self.html)
 def test_offline(self): self.assertNotIn('fetch(',self.js)
if __name__=='__main__':unittest.main()
