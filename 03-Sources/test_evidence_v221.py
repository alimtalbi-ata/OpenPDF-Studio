import unittest
from pathlib import Path
from diagnostic_dashboard import build_dashboard
class EvidenceV221(unittest.TestCase):
 def test_card(self): self.assertIn('id="region-evidence-card"',build_dashboard({}))
 def test_script(self): self.assertIn('Rectangle PDF (points)',build_dashboard({}))
 def test_version(self): self.assertIn('Diagnostic V25.4',build_dashboard({}))
 def test_export(self): self.assertIn('openpdf-diagnostic-v25.4.csv',build_dashboard({}))
 def test_no_semantic_invention(self): self.assertIn('Non attribuée à cette région',build_dashboard({}))
 def test_bbox_source(self): self.assertIn('data-pdf-bbox',Path(__file__).with_name('diagnostic_dashboard.py').read_text())
if __name__=='__main__':unittest.main()
