import unittest
from diagnostic_dashboard import build_dashboard
class V210(unittest.TestCase):
 def setUp(self):self.html=build_dashboard({})
 def test_version(self):self.assertIn('Diagnostic V25.4',self.html)
 def test_region_algorithm(self):self.assertIn('function groupDifferenceRegions(',self.html)
 def test_mask(self):self.assertIn('mask[i]=1',self.html)
 def test_bounds(self):self.assertIn('out.strokeRect(',self.html)
 def test_candidate_label(self):self.assertIn('régions candidates',self.html)
 def test_no_network(self):self.assertNotIn('fetch(',self.html)
 def test_fidelity_warning(self):self.assertIn('ne prouve pas la fidélité',self.html)
