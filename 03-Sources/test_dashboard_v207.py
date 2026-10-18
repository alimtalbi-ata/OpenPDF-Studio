import unittest
from diagnostic_dashboard import build_dashboard
class V207(unittest.TestCase):
 def setUp(self): self.html=build_dashboard({})
 def test_version(self): self.assertIn('V20.9',self.html)
 def test_auto_button(self): self.assertIn('id="overlay-auto"',self.html)
 def test_status(self): self.assertIn('id="overlay-auto-status"',self.html)
 def test_conservative(self): self.assertIn('improvement<.08',self.html)
 def test_no_network(self): self.assertIn('getImageData',self.html)
 def test_bounds(self): self.assertIn('Math.abs(x)>150',self.html)
 def test_manual(self): self.assertIn('id="overlay-reset"',self.html)
 def test_confidence(self): self.assertIn('Vérification humaine nécessaire',self.html)
