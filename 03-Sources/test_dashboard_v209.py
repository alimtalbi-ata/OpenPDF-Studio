import unittest
from diagnostic_dashboard import build_dashboard
class V209(unittest.TestCase):
 def setUp(self):self.html=build_dashboard({})
 def test_version(self):self.assertIn('Diagnostic V25.4',self.html)
 def test_canvas(self):self.assertIn('id="difference-canvas"',self.html)
 def test_button(self):self.assertIn('id="difference-render"',self.html)
 def test_threshold(self):self.assertIn('min="10" max="100"',self.html)
 def test_real_pixels(self):self.assertIn('getImageData(0,0,w,h)',self.html)
 def test_scale(self):self.assertIn('cb.scale(scale,scale)',self.html)
 def test_no_auto_certificate(self):self.assertIn('ne prouve pas la fidélité',self.html)
 def test_invalidates(self):self.assertIn('Paramètres modifiés : relancer',self.html)
