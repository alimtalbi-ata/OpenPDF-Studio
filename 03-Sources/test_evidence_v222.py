import unittest
from diagnostic_dashboard import build_dashboard
class EvidenceV222(unittest.TestCase):
 def setUp(self): self.html=build_dashboard({})
 def test_version(self): self.assertIn('Diagnostic V25.4',self.html)
 def test_summary(self): self.assertIn('id="region-evidence-summary"',self.html)
 def test_quality(self): self.assertIn('Qualité du diagnostic',self.html)
 def test_correlations(self): self.assertIn('Corrélations géométriques sur la page',self.html)
 def test_no_false_identity(self): self.assertIn('sans attribution à cette région',self.html)
 def test_reset(self): self.assertIn('Aucune preuve sélectionnée',self.html)
 def test_export(self): self.assertIn('openpdf-diagnostic-v25.3.json',self.html)
if __name__=='__main__': unittest.main()
